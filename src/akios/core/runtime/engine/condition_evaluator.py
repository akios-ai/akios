"""
AST-based safe condition evaluator for AKIOS workflow steps.

Replaces the previous eval()-based evaluator with a secure AST walker
that only allows comparisons, boolean logic, arithmetic, attribute
access, and literal values. Function calls, imports, assignments, and
all other constructs are rejected at parse time — before any code runs.

Security guarantees:
  - No eval() / exec() / compile()
  - No function calls (ast.Call blocked)
  - No import statements
  - No attribute access to dunder names
  - No subscript access to dunder keys
  - No arbitrary code execution of any kind

Usage::

    from akios.core.runtime.engine.condition_evaluator import safe_eval

    namespace = {'step_1_output': {'status': 'success'}, 'x': 42}
    result = safe_eval("x > 10 and step_1_output['status'] == 'success'", namespace)
"""

import ast
import logging
from typing import Any, Dict

logger = logging.getLogger("akios.condition_evaluator")

# AST node types allowed in condition expressions.
# Everything else is rejected before evaluation begins.
ALLOWED_NODES = frozenset({
    # Top-level expression wrapper
    ast.Expression,
    # Boolean operators
    ast.BoolOp, ast.And, ast.Or,
    # Unary operators
    ast.UnaryOp, ast.Not, ast.UAdd, ast.USub,
    # Binary operators (arithmetic)
    ast.BinOp, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod,
    # Comparisons
    ast.Compare, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.Is, ast.IsNot, ast.In, ast.NotIn,
    # Values
    ast.Constant,   # strings, numbers, booleans, None
    ast.Name,       # variable references
    ast.Attribute,  # obj.attr access
    ast.Subscript,  # obj['key'] / obj[0] access
    # Containers (for `x in [1, 2, 3]` patterns)
    ast.List, ast.Tuple, ast.Set,
    # Context (required by Name/Attribute/Subscript nodes)
    ast.Load,
    # Ternary expression
    ast.IfExp,
    # String formatting (f-strings compile to JoinedStr)
    # NOT allowed — too complex and unnecessary for conditions
})

# Maximum expression length to prevent DoS via huge strings
MAX_EXPRESSION_LENGTH = 1024

# Maximum AST depth to prevent deeply nested expressions
MAX_AST_DEPTH = 20


class ConditionEvaluationError(Exception):
    """Raised when a condition expression cannot be safely evaluated."""
    pass


class UnsafeExpressionError(ConditionEvaluationError):
    """Raised when a condition contains disallowed constructs."""
    pass


def safe_eval(expression: str, namespace: Dict[str, Any]) -> Any:
    """
    Safely evaluate a simple expression against a namespace.

    Only allows: comparisons, boolean operators, arithmetic,
    attribute access (non-dunder), subscript access, and literal values.
    Function calls, imports, assignments, and all dangerous constructs
    are rejected at parse time.

    Args:
        expression: The expression string to evaluate.
        namespace:  Variables available to the expression.

    Returns:
        The result of evaluating the expression.

    Raises:
        ConditionEvaluationError: If the expression is invalid or unsafe.
    """
    if not isinstance(expression, str):
        raise ConditionEvaluationError(
            f"Expression must be a string, got {type(expression).__name__}"
        )

    expression = expression.strip()
    if not expression:
        raise ConditionEvaluationError("Empty expression")

    if len(expression) > MAX_EXPRESSION_LENGTH:
        raise UnsafeExpressionError(
            f"Expression too long ({len(expression)} chars, max {MAX_EXPRESSION_LENGTH})"
        )

    # Parse into AST
    try:
        tree = ast.parse(expression, mode='eval')
    except SyntaxError as exc:
        raise ConditionEvaluationError(f"Invalid expression syntax: {exc}") from exc

    # Validate every node in the AST
    _validate_ast(tree)

    # Check depth
    depth = _ast_depth(tree)
    if depth > MAX_AST_DEPTH:
        raise UnsafeExpressionError(
            f"Expression too deeply nested (depth {depth}, max {MAX_AST_DEPTH})"
        )

    # Evaluate the validated AST
    return _eval_node(tree.body, namespace)


def evaluate_condition(condition: str, step_id: int,
                       execution_context: Dict[str, Any]) -> bool:
    """
    Evaluate a workflow step condition expression.

    Builds a safe namespace from the execution context and evaluates
    the condition. Returns True if the step should run, False if not.

    This is the high-level entry point used by the engine.

    Args:
        condition:         Expression string from the workflow step.
        step_id:           Current step ID (for logging).
        execution_context: Engine's execution context dict.

    Returns:
        True if the condition passes (step should run),
        False if it fails or errors.
    """
    # Build namespace from execution context
    namespace: Dict[str, Any] = {
        'True': True,
        'False': False,
        'None': None,
    }

    # Expose step results as step_N_output
    for key, value in execution_context.items():
        if key.startswith('step_') and key.endswith('_result'):
            step_num = key.replace('step_', '').replace('_result', '')
            namespace[f'step_{step_num}_output'] = value

    # Expose previous_output (= result of step_id - 1)
    prev_key = f'step_{step_id - 1}_result'
    namespace['previous_output'] = execution_context.get(prev_key)

    try:
        result = safe_eval(condition, namespace)
        return bool(result)
    except (ConditionEvaluationError, UnsafeExpressionError) as exc:
        logger.warning(
            'Condition evaluation failed for step %d ("%s"): %s',
            step_id, condition, exc
        )
        return False
    except Exception as exc:
        logger.warning(
            'Unexpected error evaluating condition for step %d ("%s"): %s',
            step_id, condition, exc
        )
        return False


# ── AST Validation ──────────────────────────────────────────────────

def _validate_ast(tree: ast.AST) -> None:
    """Walk the AST and reject any disallowed node types."""
    for node in ast.walk(tree):
        node_type = type(node)

        if node_type not in ALLOWED_NODES:
            raise UnsafeExpressionError(
                f"Disallowed expression element: {node_type.__name__}. "
                f"Only comparisons, boolean logic, arithmetic, and "
                f"attribute access are permitted."
            )

        # Extra safety: block dunder attribute access
        if isinstance(node, ast.Attribute):
            if node.attr.startswith('_'):
                raise UnsafeExpressionError(
                    f"Access to private/dunder attribute '{node.attr}' is blocked"
                )

        # Extra safety: block dunder name access
        if isinstance(node, ast.Name):
            if node.id.startswith('__') and node.id.endswith('__'):
                raise UnsafeExpressionError(
                    f"Access to dunder name '{node.id}' is blocked"
                )

        # Extra safety: block string subscript to dunder keys
        if isinstance(node, ast.Subscript):
            if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                if node.slice.value.startswith('_'):
                    raise UnsafeExpressionError(
                        f"Subscript access to private key '{node.slice.value}' is blocked"
                    )


def _ast_depth(node: ast.AST, current: int = 0) -> int:
    """Calculate the maximum depth of an AST tree."""
    max_depth = current
    for child in ast.iter_child_nodes(node):
        child_depth = _ast_depth(child, current + 1)
        if child_depth > max_depth:
            max_depth = child_depth
    return max_depth


# ── AST Evaluation ──────────────────────────────────────────────────

def _eval_node(node: ast.AST, namespace: Dict[str, Any]) -> Any:
    """Recursively evaluate a validated AST node."""

    # Literal values: strings, numbers, booleans, None
    if isinstance(node, ast.Constant):
        return node.value

    # Variable references
    if isinstance(node, ast.Name):
        if node.id not in namespace:
            raise ConditionEvaluationError(f"Unknown variable: '{node.id}'")
        return namespace[node.id]

    # Attribute access: obj.attr
    if isinstance(node, ast.Attribute):
        obj = _eval_node(node.value, namespace)
        try:
            return getattr(obj, node.attr)
        except AttributeError:
            raise ConditionEvaluationError(
                f"Object has no attribute '{node.attr}'"
            )

    # Subscript access: obj['key'] or obj[0]
    if isinstance(node, ast.Subscript):
        obj = _eval_node(node.value, namespace)
        key = _eval_node(node.slice, namespace)
        try:
            return obj[key]
        except (KeyError, IndexError, TypeError) as exc:
            raise ConditionEvaluationError(
                f"Subscript access failed: {exc}"
            )

    # Boolean operators: and, or
    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            result = True
            for value in node.values:
                result = _eval_node(value, namespace)
                if not result:
                    return result
            return result
        if isinstance(node.op, ast.Or):
            result = False
            for value in node.values:
                result = _eval_node(value, namespace)
                if result:
                    return result
            return result

    # Unary operators: not, +, -
    if isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand, namespace)
        if isinstance(node.op, ast.Not):
            return not operand
        if isinstance(node.op, ast.UAdd):
            return +operand
        if isinstance(node.op, ast.USub):
            return -operand

    # Binary operators: +, -, *, /, //, %
    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left, namespace)
        right = _eval_node(node.right, namespace)
        _OPS = {
            ast.Add: lambda a, b: a + b,
            ast.Sub: lambda a, b: a - b,
            ast.Mult: lambda a, b: a * b,
            ast.Div: lambda a, b: a / b,
            ast.FloorDiv: lambda a, b: a // b,
            ast.Mod: lambda a, b: a % b,
        }
        op_func = _OPS.get(type(node.op))
        if op_func:
            return op_func(left, right)
        raise ConditionEvaluationError(
            f"Unsupported binary operator: {type(node.op).__name__}"
        )

    # Comparisons: ==, !=, <, <=, >, >=, is, is not, in, not in
    if isinstance(node, ast.Compare):
        left = _eval_node(node.left, namespace)
        for op, comparator in zip(node.ops, node.comparators):
            right = _eval_node(comparator, namespace)
            if not _compare(op, left, right):
                return False
            left = right  # chained comparisons: a < b < c
        return True

    # Container literals: [1, 2, 3], (1, 2), {1, 2}
    if isinstance(node, ast.List):
        return [_eval_node(e, namespace) for e in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_eval_node(e, namespace) for e in node.elts)
    if isinstance(node, ast.Set):
        return {_eval_node(e, namespace) for e in node.elts}

    # Ternary: x if condition else y
    if isinstance(node, ast.IfExp):
        test = _eval_node(node.test, namespace)
        if test:
            return _eval_node(node.body, namespace)
        return _eval_node(node.orelse, namespace)

    raise ConditionEvaluationError(
        f"Cannot evaluate node type: {type(node).__name__}"
    )


def _compare(op: ast.cmpop, left: Any, right: Any) -> bool:
    """Evaluate a single comparison operation."""
    if isinstance(op, ast.Eq):
        return left == right
    if isinstance(op, ast.NotEq):
        return left != right
    if isinstance(op, ast.Lt):
        return left < right
    if isinstance(op, ast.LtE):
        return left <= right
    if isinstance(op, ast.Gt):
        return left > right
    if isinstance(op, ast.GtE):
        return left >= right
    if isinstance(op, ast.Is):
        return left is right
    if isinstance(op, ast.IsNot):
        return left is not right
    if isinstance(op, ast.In):
        return left in right
    if isinstance(op, ast.NotIn):
        return left not in right
    raise ConditionEvaluationError(
        f"Unsupported comparison operator: {type(op).__name__}"
    )
