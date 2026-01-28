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
AKIOS Core Runtime Module

Execution heart of AKIOS - parses sequential YAML workflows,
runs core agents (LLM, HTTP, filesystem, tool_executor), enforces cost/loop kills,
coordinates with security/audit for secure workflow execution.
"""

from .engine import RuntimeEngine
from .workflow import parse_workflow
from .output.manager import get_output_manager, create_output_directory, generate_output_summary

__all__ = ["RuntimeEngine", "parse_workflow", "get_output_manager", "create_output_directory", "generate_output_summary"]
