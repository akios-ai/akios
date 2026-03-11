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

"""Shared helpers for warning about seccomp availability."""

from typing import Optional

from ...core.ui.semantic_colors import print_warning

SEC_COMP_WARNING = (
    "⚠️ seccomp filter not installed or lacks privileges—run with sudo/akios[seccomp] for "
    "kernel-hard protection"
)


def warn_seccomp_disabled(detail: Optional[str] = None) -> None:
    """Show a persistent warning when seccomp cannot be enabled."""

    details = [detail] if detail else None
    print_warning(SEC_COMP_WARNING, details)
