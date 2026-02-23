---- MODULE AKIOSEnforcement ----
\* =========================================================================
\* AKIOS Enforcement Pipeline — TLA+ Formal Specification
\* Version: 1.0.11
\* Date: 2026-02-19
\*
\* Model-checks safety invariants for the AKIOS security cage:
\*   1. PII redaction is ALWAYS applied before output leaves the cage.
\*   2. Cost kill-switch triggers when budget is exceeded.
\*   3. Audit events are logged for every agent execution.
\*   4. Sandbox must be active for any agent to execute.
\*
\* Run with TLC:
\*   tlc AKIOSEnforcement.tla -config AKIOSEnforcement.cfg
\* =========================================================================

EXTENDS Integers, Sequences, FiniteSets

CONSTANTS
    MaxSteps,       \* Maximum workflow steps (e.g. 10)
    MaxBudget,      \* Budget limit in cents (e.g. 100 = $1.00)
    Agents          \* Set of agent types {"llm", "http", "filesystem", "tool_executor"}

VARIABLES
    step,           \* Current step index (0..MaxSteps)
    budget_spent,   \* Cumulative cost in cents
    audit_log,      \* Sequence of audit events
    sandbox_up,     \* Boolean: sandbox is active
    pii_redacted,   \* Boolean: PII redaction has been applied to current output
    killed,         \* Boolean: execution has been killed
    workflow_status \* "running" | "completed" | "killed" | "error"

vars == <<step, budget_spent, audit_log, sandbox_up, pii_redacted, killed, workflow_status>>

TypeInvariant ==
    /\ step \in 0..MaxSteps
    /\ budget_spent \in 0..MaxBudget * 2   \* Allow overshoot to test kill-switch
    /\ sandbox_up \in BOOLEAN
    /\ pii_redacted \in BOOLEAN
    /\ killed \in BOOLEAN
    /\ workflow_status \in {"init", "running", "completed", "killed", "error"}

\* ── Safety Invariants ─────────────────────────────────────────────

\* INV-1: No output is produced without PII redaction
\* (modeled as: whenever a step completes, pii_redacted must be TRUE)
PIIAlwaysRedacted ==
    workflow_status = "completed" => pii_redacted

\* INV-2: Budget kill-switch fires before overspend exceeds 2x limit
CostKillSwitchWorks ==
    budget_spent > MaxBudget => killed

\* INV-3: Every step execution has a corresponding audit event
AuditCompleteness ==
    Len(audit_log) >= step

\* INV-4: No agent runs without the sandbox being up
SandboxRequired ==
    workflow_status = "running" => sandbox_up

SafetyInvariant ==
    /\ PIIAlwaysRedacted
    /\ CostKillSwitchWorks
    /\ AuditCompleteness
    /\ SandboxRequired

\* ── Initial State ─────────────────────────────────────────────────

Init ==
    /\ step = 0
    /\ budget_spent = 0
    /\ audit_log = <<>>
    /\ sandbox_up = TRUE
    /\ pii_redacted = FALSE
    /\ killed = FALSE
    /\ workflow_status = "init"

\* ── Actions ───────────────────────────────────────────────────────

\* Start workflow execution
StartWorkflow ==
    /\ workflow_status = "init"
    /\ sandbox_up = TRUE
    /\ workflow_status' = "running"
    /\ audit_log' = Append(audit_log, [type |-> "workflow_start", step_num |-> 0])
    /\ UNCHANGED <<step, budget_spent, sandbox_up, pii_redacted, killed>>

\* Execute a step (costs between 0 and 10 cents)
ExecuteStep(cost) ==
    /\ workflow_status = "running"
    /\ ~killed
    /\ step < MaxSteps
    /\ sandbox_up
    /\ step' = step + 1
    /\ budget_spent' = budget_spent + cost
    /\ pii_redacted' = TRUE   \* PII redaction always applied
    /\ audit_log' = Append(audit_log, [type |-> "step_complete", step_num |-> step + 1])
    \* Check kill-switch AFTER step
    /\ IF budget_spent + cost > MaxBudget
       THEN /\ killed' = TRUE
            /\ workflow_status' = "killed"
       ELSE /\ killed' = FALSE
            /\ workflow_status' = "running"
    /\ UNCHANGED <<sandbox_up>>

\* Complete workflow successfully
CompleteWorkflow ==
    /\ workflow_status = "running"
    /\ ~killed
    /\ step = MaxSteps
    /\ workflow_status' = "completed"
    /\ audit_log' = Append(audit_log, [type |-> "workflow_complete", step_num |-> step])
    /\ UNCHANGED <<step, budget_spent, sandbox_up, pii_redacted, killed>>

\* Sandbox failure (fault injection for model checking)
SandboxFault ==
    /\ workflow_status = "running"
    /\ sandbox_up' = FALSE
    /\ workflow_status' = "error"
    /\ audit_log' = Append(audit_log, [type |-> "sandbox_fault", step_num |-> step])
    /\ UNCHANGED <<step, budget_spent, pii_redacted, killed>>

\* ── Next-state relation ───────────────────────────────────────────

Next ==
    \/ StartWorkflow
    \/ \E cost \in 0..10 : ExecuteStep(cost)
    \/ CompleteWorkflow
    \/ SandboxFault

\* ── Fairness ──────────────────────────────────────────────────────

Spec == Init /\ [][Next]_vars /\ WF_vars(Next)

\* ── Liveness ──────────────────────────────────────────────────────

\* Every workflow eventually terminates (completed or killed)
WorkflowTerminates ==
    <>(workflow_status \in {"completed", "killed", "error"})

====
