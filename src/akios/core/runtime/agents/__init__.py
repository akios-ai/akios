# Copyright (C) 2025-2026 AKIOUD AI, SAS <contact@akioud.ai>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Agents module - Registry for AKIOS agents

Core agents: LLM, HTTP, Filesystem, Tool Executor
v1.1.0 agents: Webhook, Database
v1.1.0: Plugin system — pip-installable agent packages via entry points
"""
import logging
from typing import List, Dict, Any

from .base import BaseAgent, AgentError
from .llm import LLMAgent
from .http import HTTPAgent
from .filesystem import FilesystemAgent
from .tool_executor import ToolExecutorAgent
from .webhook import WebhookAgent
from .database import DatabaseAgent

_logger = logging.getLogger(__name__)

# Agent registry — core agents
AGENT_CLASSES = {
    'llm': LLMAgent,
    'http': HTTPAgent,
    'filesystem': FilesystemAgent,
    'tool_executor': ToolExecutorAgent,
    'webhook': WebhookAgent,
    'database': DatabaseAgent,
}

# Plugin agent registry (populated by discover_plugins)
PLUGIN_AGENTS = {}


def discover_plugins() -> Dict[str, type]:
    """
    Discover pip-installed agent plugins via entry points (v1.1.0).

    Plugin packages declare entry points in pyproject.toml:
        [project.entry-points."akios.agents"]
        redis = "akios_agent_redis:RedisAgent"

    Only classes that extend BaseAgent are registered.
    """
    discovered = {}
    try:
        from importlib.metadata import entry_points
        eps = entry_points(group='akios.agents')
        for ep in eps:
            try:
                agent_cls = ep.load()
                if isinstance(agent_cls, type) and issubclass(agent_cls, BaseAgent) and agent_cls is not BaseAgent:
                    AGENT_CLASSES[ep.name] = agent_cls
                    PLUGIN_AGENTS[ep.name] = agent_cls
                    discovered[ep.name] = agent_cls
                    _logger.info("Plugin agent registered: %s (%s)", ep.name, agent_cls.__name__)
                else:
                    _logger.warning("Plugin %s rejected: not a BaseAgent subclass", ep.name)
            except Exception as e:
                _logger.warning("Failed to load plugin %s: %s", ep.name, e)
    except Exception:
        pass  # importlib.metadata not available — no plugins
    return discovered


# Auto-discover plugins at import time
discover_plugins()


def get_agent_class(agent_type: str):
    """
    Get agent class by type.

    Args:
        agent_type: Type of agent ('llm', 'http', 'filesystem', 'tool_executor')

    Returns:
        Agent class

    Raises:
        ValueError: If agent type is not supported
    """
    if agent_type not in AGENT_CLASSES:
        raise ValueError(f"Unsupported agent type: {agent_type}. Must be one of: {list(AGENT_CLASSES.keys())}")

    return AGENT_CLASSES[agent_type]


def create_agent(agent_type: str, **kwargs):
    """
    Create an agent instance.

    Args:
        agent_type: Type of agent to create
        **kwargs: Agent initialization parameters

    Returns:
        Agent instance
    """
    agent_class = get_agent_class(agent_type)
    return agent_class(**kwargs)


def get_supported_agents() -> List[str]:
    """Get list of supported agent types"""
    return list(AGENT_CLASSES.keys())


def validate_agent_health(agent_type: str) -> Dict[str, Any]:
    """
    Validate that an agent type can be instantiated and is healthy.

    Args:
        agent_type: Type of agent to validate

    Returns:
        Dict with health status and any issues found
    """
    health_status = {
        'agent_type': agent_type,
        'healthy': True,
        'issues': [],
        'capabilities': {}
    }

    try:
        # Check if agent class exists
        agent_class = get_agent_class(agent_type)
        health_status['capabilities']['class_available'] = True

        # Try to instantiate agent with minimal config (may fail for some agents)
        try:
            # For validation purposes, try with empty config
            # This will fail for agents that require configuration, which is expected
            agent = agent_class()
            health_status['capabilities']['can_instantiate'] = True
        except Exception as e:
            # This is expected for agents that need configuration
            health_status['capabilities']['can_instantiate'] = False
            health_status['capabilities']['requires_config'] = True
            health_status['issues'].append(f"Agent requires configuration: {str(e)}")

    except ValueError as e:
        health_status['healthy'] = False
        health_status['issues'].append(f"Unsupported agent type: {str(e)}")
    except Exception as e:
        health_status['healthy'] = False
        health_status['issues'].append(f"Agent health check failed: {str(e)}")

    return health_status


def get_agent_capabilities(agent_type: str) -> Dict[str, Any]:
    """
    Get capabilities and requirements for an agent type.

    Args:
        agent_type: Type of agent

    Returns:
        Dict with agent capabilities and requirements
    """
    capabilities = {
        'agent_type': agent_type,
        'supported_actions': [],
        'requires_config': False,
        'config_parameters': [],
        'idempotent': False,
        'retryable': False
    }

    # Define capabilities per agent type
    if agent_type == 'llm':
        capabilities.update({
            'supported_actions': ['complete', 'chat', 'generate'],
            'requires_config': True,
            'config_parameters': ['provider', 'model', 'api_key'],
            'idempotent': True,
            'retryable': True
        })
    elif agent_type == 'http':
        capabilities.update({
            'supported_actions': ['get', 'post', 'put', 'delete', 'patch'],
            'requires_config': False,
            'config_parameters': ['timeout', 'max_redirects'],
            'idempotent': False,  # Depends on HTTP method
            'retryable': True
        })
    elif agent_type == 'filesystem':
        capabilities.update({
            'supported_actions': ['read', 'write', 'list', 'exists', 'stat'],
            'requires_config': True,
            'config_parameters': ['allowed_paths', 'read_only'],
            'idempotent': True,  # Most operations are idempotent
            'retryable': False  # File operations shouldn't be retried
        })
    elif agent_type == 'tool_executor':
        capabilities.update({
            'supported_actions': ['execute', 'run', 'call'],
            'requires_config': False,
            'config_parameters': ['allowed_commands', 'timeout', 'max_output_size'],
            'idempotent': False,  # Commands may have side effects
            'retryable': False  # Commands shouldn't be retried
        })
    elif agent_type == 'webhook':
        capabilities.update({
            'supported_actions': ['notify', 'send'],
            'requires_config': True,
            'config_parameters': ['webhook_url', 'platform', 'timeout'],
            'idempotent': False,
            'retryable': True
        })
    elif agent_type == 'database':
        capabilities.update({
            'supported_actions': ['query', 'execute', 'count'],
            'requires_config': True,
            'config_parameters': ['database_url', 'allow_write', 'timeout', 'max_rows'],
            'idempotent': True,
            'retryable': False
        })

    return capabilities


__all__ = [
    "BaseAgent",
    "AgentError",
    "LLMAgent",
    "HTTPAgent",
    "FilesystemAgent",
    "ToolExecutorAgent",
    "WebhookAgent",
    "DatabaseAgent",
    "PLUGIN_AGENTS",
    "discover_plugins",
    "get_agent_class",
    "create_agent",
    "get_supported_agents",
    "validate_agent_health",
    "get_agent_capabilities"
]
