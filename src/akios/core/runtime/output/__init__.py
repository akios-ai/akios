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
Output module - Workflow output management and organization

Provides human-readable output directory naming and secure output handling
for AKIOS workflows.
"""

from .manager import (
    OutputManager,
    get_output_manager,
    create_output_directory,
    generate_output_summary
)

__all__ = [
    "OutputManager",
    "get_output_manager",
    "create_output_directory",
    "generate_output_summary"
]
