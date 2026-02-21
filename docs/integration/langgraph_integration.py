# Copyright (C) 2025-2026 AKIOUD AI, SAS <contact@akioud.ai>
# SPDX-License-Identifier: GPL-3.0-or-later

"""
LangGraph ↔ AKIOS Integration Example
======================================

Demonstrates how to wrap AKIOS agents as LangGraph tool-calling nodes so that
every tool invocation runs inside the AKIOS security cage (PII redaction,
audit, cost kill-switches, sandbox isolation).

Prerequisites
-------------
    pip install langgraph langchain-core akios

Architecture
~~~~~~~~~~~~
    ┌──────────────┐       tool call        ┌──────────────────┐
    │  LangGraph   │ ──────────────────────► │  AKIOS Agent     │
    │  (planner)   │ ◄────────────────────── │  (sandboxed)     │
    └──────────────┘       result + PII      └──────────────────┘
                           redacted

Usage
-----
    # 1. Export your LLM API key
    export OPENAI_API_KEY="sk-..."

    # 2. Run the example
    python docs/integration/langgraph_integration.py
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, Sequence

# ── Guard: check dependencies ──────────────────────────────────────
_MISSING: list[str] = []
try:
    from langchain_core.tools import tool as lc_tool       # type: ignore[import-untyped]
except ImportError:
    _MISSING.append("langchain-core")

try:
    from langgraph.graph import StateGraph, END              # type: ignore[import-untyped]
    from langgraph.prebuilt import ToolNode                  # type: ignore[import-untyped]
except ImportError:
    _MISSING.append("langgraph")

try:
    from akios.core.runtime.agents import get_agent_class
    from akios.config import get_settings
except ImportError:
    _MISSING.append("akios")

if _MISSING:
    print(
        f"Missing dependencies: {', '.join(_MISSING)}\n"
        f"Install with: pip install {' '.join(_MISSING)}",
        file=sys.stderr,
    )
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════════
# 1. Wrap AKIOS agents as LangChain tools
# ═══════════════════════════════════════════════════════════════════

@lc_tool
def akios_filesystem_read(path: str) -> str:
    """Read a file through the AKIOS security cage. PII is automatically redacted."""
    AgentClass = get_agent_class("filesystem")
    agent = AgentClass(allowed_paths=["./data"], read_only=True)
    result = agent.execute("read", {
        "path": path,
        "workflow_id": "langgraph_demo",
        "step": 1,
        "workflow_name": "langgraph_integration",
    })
    return result.get("content", str(result))


@lc_tool
def akios_tool_run(command: str) -> str:
    """Run a whitelisted shell command inside the AKIOS sandbox."""
    settings = get_settings()
    AgentClass = get_agent_class("tool_executor")
    agent = AgentClass(
        allowed_commands=settings.allowed_commands,
        timeout=30,
    )
    result = agent.execute("run", {
        "command": command,
        "workflow_id": "langgraph_demo",
        "step": 2,
        "workflow_name": "langgraph_integration",
    })
    return result.get("stdout", str(result))


@lc_tool
def akios_http_get(url: str) -> str:
    """Fetch a URL through the AKIOS HTTP agent (domain whitelist enforced)."""
    AgentClass = get_agent_class("http")
    settings = get_settings()
    agent = AgentClass(
        allowed_domains=settings.allowed_domains,
        timeout=30,
    )
    result = agent.execute("get", {
        "url": url,
        "workflow_id": "langgraph_demo",
        "step": 3,
        "workflow_name": "langgraph_integration",
    })
    return result.get("content", str(result))[:2000]


# ═══════════════════════════════════════════════════════════════════
# 2. Build a minimal LangGraph agent
# ═══════════════════════════════════════════════════════════════════

AKIOS_TOOLS = [akios_filesystem_read, akios_tool_run, akios_http_get]


def build_graph():
    """
    Build a LangGraph state-graph with AKIOS tools.

    The graph has two nodes:
      • **agent** — calls the LLM to decide which tool to use.
      • **tools** — executes the chosen AKIOS tool inside the cage.
    """
    from langchain_core.messages import BaseMessage, HumanMessage

    class AgentState(dict):
        messages: Sequence[BaseMessage]

    tool_node = ToolNode(AKIOS_TOOLS)

    def should_continue(state: AgentState) -> str:
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return END

    def call_model(state: AgentState) -> Dict[str, Any]:
        """Invoke the LLM with tool descriptions."""
        # Use whichever LangChain chat model the user has configured
        try:
            from langchain_openai import ChatOpenAI  # type: ignore[import-untyped]
            model = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(AKIOS_TOOLS)
        except ImportError:
            raise RuntimeError(
                "This example requires langchain-openai.  "
                "Install with: pip install langchain-openai"
            )
        response = model.invoke(state["messages"])
        return {"messages": [response]}

    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()


# ═══════════════════════════════════════════════════════════════════
# 3. Run an example query
# ═══════════════════════════════════════════════════════════════════

def main():
    print("╔════════════════════════════════════════════════════════╗")
    print("║  LangGraph ↔ AKIOS Integration Demo                  ║")
    print("║  Every tool call runs inside the AKIOS security cage  ║")
    print("╚════════════════════════════════════════════════════════╝\n")

    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Set OPENAI_API_KEY to run the full demo.", file=sys.stderr)
        print("   Showing graph structure instead.\n")
        print("Available AKIOS tools for LangGraph:")
        for t in AKIOS_TOOLS:
            print(f"  • {t.name}: {t.description}")
        return

    from langchain_core.messages import HumanMessage
    app = build_graph()

    query = "List the files in the ./data/input directory"
    print(f"Query: {query}\n")

    result = app.invoke({"messages": [HumanMessage(content=query)]})

    print("\n─── Agent Response ───")
    for msg in result["messages"]:
        role = getattr(msg, "type", "unknown")
        content = getattr(msg, "content", str(msg))
        if content:
            print(f"[{role}] {content[:500]}")
    print("─────────────────────\n")
    print("✅ All tool calls executed inside AKIOS security cage")
    print("   • PII redaction: active")
    print("   • Audit logging: active")
    print("   • Sandbox: active")


if __name__ == "__main__":
    main()
