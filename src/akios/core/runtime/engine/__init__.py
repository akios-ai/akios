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
Engine module - Main runtime coordination for AKIOS

Orchestrates sequential workflow execution with security and audit integration.

Submodules:
  - engine:              RuntimeEngine orchestrator
  - condition_evaluator: AST-safe step condition evaluation
  - output_extractor:    Canonical output key probing
  - template_renderer:   Template substitution and output-path transforms
  - step_executor:       Single-step dispatch, retry, and validation
  - kills:               Cost and loop kill-switches
  - retry:               Retry and fallback handlers
"""

from .engine import RuntimeEngine, run_workflow
from .kills import CostKillSwitch, LoopKillSwitch, KillSwitchManager
from .retry import RetryHandler, FallbackHandler

__all__ = [
    "RuntimeEngine",
    "run_workflow",
    "CostKillSwitch",
    "LoopKillSwitch",
    "KillSwitchManager",
    "RetryHandler",
    "FallbackHandler",
]
