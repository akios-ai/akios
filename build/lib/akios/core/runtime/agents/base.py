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
Base agent class for AKIOS V1.0 core agents.

All agents must inherit from this base class and implement the execute method.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from akios.config import get_settings


class AgentError(Exception):
    """Base exception for agent errors"""
    pass


class BaseAgent(ABC):
    """
    Base class for all AKIOS V1.0 agents.

    Provides common functionality and enforces security boundaries.
    """

    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__
        self.settings = get_settings()

    @abstractmethod
    def execute(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an action with the given parameters.

        Args:
            action: Action to perform
            parameters: Action parameters

        Returns:
            Action result dictionary

        Raises:
            AgentError: If action fails
        """
        pass

    def validate_parameters(self, action: str, parameters: Dict[str, Any]) -> None:
        """
        Validate action parameters.

        Args:
            action: Action being performed
            parameters: Parameters to validate

        Raises:
            AgentError: If parameters are invalid
        """
        # Default implementation - subclasses can override
        pass

    def get_supported_actions(self) -> List[str]:
        """
        Get list of supported actions for this agent.

        Returns:
            List of action names
        """
        # Default implementation - subclasses should override
        return []

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
