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
Testing utilities for automatic issue tracking and test environment management.

This module provides automatic logging of testing limitations, partial tests,
and environmental constraints to ensure comprehensive test coverage tracking.
"""

from .tracker import TestingIssueTracker, log_testing_issue, get_testing_tracker

__all__ = ['TestingIssueTracker', 'log_testing_issue', 'get_testing_tracker']
