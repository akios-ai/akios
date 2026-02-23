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
Kill Switches - Cost & loop detection + hard termination logic

Implements fail-fast kill switches for cost overruns and infinite loops.
"""

import time
from typing import Dict, Any

from akios.config import get_settings


class CostKillSwitch:
    """
    Cost-based kill switch.

    Monitors execution costs and terminates if budget exceeded.
    """

    def __init__(self):
        self.settings = get_settings()
        self.total_cost = 0.0
        self.tokens_input = 0
        self.tokens_output = 0
        self.llm_model = None
        self.start_time = time.time()

    def reset(self) -> None:
        """Reset the kill switch for a new execution"""
        self.total_cost = 0.0
        self.tokens_input = 0
        self.tokens_output = 0
        self.llm_model = None
        self.start_time = time.time()

    def add_cost(self, cost: float) -> None:
        """
        Add cost to the running total.

        Args:
            cost: Cost to add (in USD)
        """
        self.total_cost += cost

    def add_tokens(self, prompt_tokens: int = 0, completion_tokens: int = 0, model: str = None) -> None:
        """
        Track token usage by input/output.

        Args:
            prompt_tokens: Number of input (prompt) tokens
            completion_tokens: Number of output (completion) tokens
            model: LLM model identifier used for this call
        """
        self.tokens_input += prompt_tokens
        self.tokens_output += completion_tokens
        if model:
            self.llm_model = model

    def should_kill(self) -> bool:
        """
        Check if execution should be killed based on cost.

        Returns:
            True if cost limit exceeded
        """
        if not self.settings.cost_kill_enabled:
            return False

        return self.total_cost >= self.settings.budget_limit_per_run

    def get_status(self) -> Dict[str, Any]:
        """Get current cost and token usage status"""
        return {
            'enabled': self.settings.cost_kill_enabled,
            'total_cost': self.total_cost,
            'budget_limit': self.settings.budget_limit_per_run,
            'remaining_budget': max(0, self.settings.budget_limit_per_run - self.total_cost),
            'over_budget': self.total_cost > self.settings.budget_limit_per_run,
            'tokens_input': self.tokens_input,
            'tokens_output': self.tokens_output,
            'tokens_total': self.tokens_input + self.tokens_output,
            'llm_model': self.llm_model,
        }


class LoopKillSwitch:
    """
    Loop detection kill switch.

    Detects potential infinite loops and terminates execution.
    """

    def __init__(self, max_execution_time: int = 300, max_steps: int = 100):
        self.settings = get_settings()
        self.max_execution_time = max_execution_time  # 5 minutes default
        self.max_steps = max_steps  # 100 steps default
        self.start_time = time.time()
        self.step_count = 0

    def reset(self) -> None:
        """Reset the kill switch for a new execution"""
        self.start_time = time.time()
        self.step_count = 0

    def increment_step(self) -> None:
        """Increment the step counter"""
        self.step_count += 1

    def should_kill(self) -> bool:
        """
        Check if execution should be killed based on loop detection.

        Returns:
            True if loop detected or limits exceeded
        """
        current_time = time.time()
        execution_time = current_time - self.start_time

        # Check execution time limit
        if execution_time > self.max_execution_time:
            return True

        # Check step count limit
        if self.step_count > self.max_steps:
            return True

        return False

    def get_status(self) -> Dict[str, Any]:
        """Get current loop detection status"""
        current_time = time.time()
        execution_time = current_time - self.start_time

        return {
            'execution_time': execution_time,
            'max_execution_time': self.max_execution_time,
            'step_count': self.step_count,
            'max_steps': self.max_steps,
            'time_limit_exceeded': execution_time > self.max_execution_time,
            'step_limit_exceeded': self.step_count > self.max_steps
        }


class KillSwitchManager:
    """
    Manages all kill switches for workflow execution.
    """

    def __init__(self):
        self.cost_kill = CostKillSwitch()
        self.loop_kill = LoopKillSwitch()

    def reset_all(self) -> None:
        """Reset all kill switches"""
        self.cost_kill.reset()
        self.loop_kill.reset()

    def check_all(self) -> Dict[str, Any]:
        """
        Check all kill switches.

        Returns:
            Dict with kill status for each switch
        """
        cost_should_kill = self.cost_kill.should_kill()
        loop_should_kill = self.loop_kill.should_kill()

        return {
            'should_kill': cost_should_kill or loop_should_kill,
            'cost_kill': {
                'triggered': cost_should_kill,
                'status': self.cost_kill.get_status()
            },
            'loop_kill': {
                'triggered': loop_should_kill,
                'status': self.loop_kill.get_status()
            }
        }

    def add_cost(self, cost: float) -> None:
        """Add cost to cost kill switch"""
        self.cost_kill.add_cost(cost)

    def add_tokens(self, prompt_tokens: int = 0, completion_tokens: int = 0, model: str = None) -> None:
        """Track token usage through cost kill switch"""
        self.cost_kill.add_tokens(prompt_tokens, completion_tokens, model)

    def increment_step(self) -> None:
        """Increment step counter for loop detection"""
        self.loop_kill.increment_step()

    def get_status_report(self) -> Dict[str, Any]:
        """Get comprehensive status report"""
        return {
            'cost_kill': self.cost_kill.get_status(),
            'loop_kill': self.loop_kill.get_status(),
            'overall_status': self.check_all()
        }
