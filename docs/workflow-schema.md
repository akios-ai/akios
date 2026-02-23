# AKIOS v1.0.11 Workflow Schema Guide
**Document Version:** 1.0.11  
**Date:** 2026-02-22  

**Version 1.0.11** | **Last Updated:** February 22, 2026

## Overview

AKIOS includes automatic workflow validation to ensure your custom workflows are structured correctly and will execute reliably. This validation helps catch common mistakes before they cause problems.

## What is Workflow Validation?

Workflow validation ensures that your `workflow.yml` file follows the correct structure that AKIOS expects. Think of it as a friendly assistant that checks your workflow for obvious issues before you run it.

### Key Benefits

- **Catch mistakes early** - Know immediately if your workflow has structural issues
- **Clear error messages** - Get helpful guidance when something is wrong
- **Invisible when working** - No impact on valid workflows
- **Consistent experience** - All workflows follow the same reliable structure

## What Gets Validated?

### Required Workflow Structure

Every workflow must have these three elements:

```yaml
name: "Your Workflow Name"        # Required: String
description: "What it does"       # Required: String
steps:                            # Required: Array of steps
  # ... workflow steps go here
```

### Step Structure

Each step in your workflow must include:

```yaml
steps:
  - step: 1                       # Optional: Step number (recommended)
    agent: llm                    # Required: One of 4 agents
    action: complete             # Required: Agent-specific action
    config: {}                   # Required: Agent configuration
    parameters: {}               # Required: Action parameters
```

### Allowed Agents

AKIOS v1.0 supports exactly 4 agents:

| Agent | Purpose | Example Actions |
|-------|---------|-----------------|
| `llm` | AI language model calls | `complete`, `chat` |
| `http` | Web API calls | `get`, `post`, `put`, `delete` |
| `filesystem` | File operations | `read`, `write`, `stat` |
| `tool_executor` | System commands | `run` |

## Common Validation Errors

### Missing Required Fields

**Error:** `Step 1: missing required field 'action'`

**Fix:** Add the missing field to your step:
```yaml
steps:
  - step: 1
    agent: llm
    action: complete  # ← Add this
    parameters: { "prompt": "Hello" }
```

### Unknown Agent

**Error:** `Step 1 uses unknown agent 'gpt'. Valid agents: filesystem, http, llm, tool_executor`

**Fix:** Use one of the 4 supported agents:
```yaml
agent: llm  # ← Use llm instead of gpt
```

### Invalid Action for Agent

**Error:** `Step 1: action 'execute' not allowed for agent 'filesystem'. Must be one of: read, write, stat`

**Fix:** Use an action supported by that agent:
```yaml
agent: filesystem
action: read  # ← Use read instead of execute
```

## Example Valid Workflows

### Simple LLM Workflow
```yaml
name: "AI Greeting Generator"
description: "Generate a creative greeting using AI"

steps:
  - step: 1
    agent: llm
    action: complete
    parameters:
      prompt: "Generate a creative greeting"
      max_tokens: 50
```

### Multi-Step Workflow
```yaml
name: "Data Processing Pipeline"
description: "Read data, process with AI, save results"

steps:
  - step: 1
    agent: filesystem
    action: read
    parameters:
      path: "./data/input.txt"

  - step: 2
    agent: llm
    action: complete
    parameters:
      prompt: "Summarize this data: {previous_output}"
      max_tokens: 100

  - step: 3
    agent: filesystem
    action: write
    parameters:
      path: "./data/summary.txt"
      content: "{previous_output}"
```

## Template Customization

When you customize templates (like `templates/hello-workflow.yml`), the validation ensures your changes don't break the basic structure.

### Safe Customizations

These changes are validated and will work:

```yaml
# ✅ Change parameters
parameters:
  prompt: "Your custom prompt here"
  max_tokens: 100

# ✅ Change agent config
config:
  provider: grok
  model: grok-3

# ✅ Add new steps (following the structure)
- step: 4
  agent: filesystem
  action: write
  parameters:
    path: "./output.txt"
    content: "Done!"
```

### What Won't Work

These will trigger validation errors:

```yaml
# ❌ Wrong agent name
agent: openai  # Use 'llm' instead

# ❌ Invalid action
action: generate_text  # Use 'complete' instead

# ❌ Missing required fields
- step: 1
  agent: llm
  # Missing 'action' and 'parameters'
```

## Validation Behavior

### When Validation Passes
- ✅ Workflow executes normally
- ✅ No validation messages shown
- ✅ Zero performance impact

### When Validation Fails
- ❌ Workflow stops before execution
- ❌ Clear error message explaining the problem
- ❌ Helpful guidance on how to fix it

### Example Error Flow

```
$ ./akios run workflow.yml
Error: Workflow validation failed:
- Error: Invalid workflow configuration
  Step 2 is missing the 'action' field

  Each step needs: agent, action, parameters
  Hint: Check your workflow.yml and compare with the original template.

Please fix workflow.yml and try again.
```

## Advanced Usage

### Environment Variable Substitution

Your workflows can use environment variables that get validated:

```yaml
config:
  provider: "${AKIOS_LLM_PROVIDER:-grok}"  # Validated as string
  model: "${AKIOS_LLM_MODEL:-grok-3}"     # Validated as string
```

### Template Variable References

Use outputs from previous steps (these are validated as strings):

```yaml
parameters:
  prompt: "Process this: {previous_output}"
  data: "{step_1_output}"
```

## Troubleshooting

### "Workflow validation failed" Errors

1. **Check the error message** - It tells you exactly what's wrong
2. **Compare with templates** - Look at working templates for correct structure
3. **Validate field names** - Ensure all required fields are present
4. **Check agent/action combinations** - Use the tables above for valid combinations

### Common Issues

| Problem | Symptom | Solution |
|---------|---------|----------|
| Missing action | `missing required field 'action'` | Add `action:` to your step |
| Wrong agent | `unknown agent 'xyz'` | Use one of: llm, http, filesystem, tool_executor |
| Invalid action | `action not allowed` | Check the action table for your agent |
| Wrong structure | `must be a dictionary` | Ensure proper YAML indentation |

### Graceful Degradation

**What happens if schema validation fails to load?**

AKIOS is designed to be resilient. If the workflow schema file cannot be loaded (due to corruption, missing files, or development environments), validation is **silently skipped** with a development-mode warning:

```
Warning: Workflow schema not found - skipping validation (development mode)
Workflow execution continues normally...
```

**This ensures:**
- ✅ **No workflow failures** due to schema loading issues
- ✅ **Development flexibility** - you can work without schema files
- ✅ **Production safety** - schema validation works when files are present
- ✅ **User experience** - workflows run even in edge cases

### Getting Help

If you encounter validation errors:

1. Read the specific error message - it's designed to be helpful
2. Check this documentation for examples
3. Compare your workflow with the provided templates
4. Look at the `templates/` directory for working examples

## Technical Details

- **Validation Timing:** Happens when you run `akios run workflow.yml`
- **Performance Impact:** <50ms overhead (not noticeable)
- **Error Format:** Clear, actionable messages with helpful hints
- **Backwards Compatibility:** All existing valid workflows continue to work
- **Graceful Degradation:** If schema files are missing, validation is skipped with warnings
- **Future Compatibility:** Foundation for enhanced validation in future versions

## Summary

Workflow validation is your safety net for creating reliable AKIOS workflows. It ensures your customizations work correctly while providing clear guidance when issues arise. The validation is designed to be helpful, not restrictive - think of it as a friendly co-pilot that catches obvious mistakes before they cause problems.

For questions or issues not covered here, check the main AKIOS documentation or visit our community forums.
