"""
Testing utilities for automatic issue tracking and test environment management.

This module provides automatic logging of testing limitations, partial tests,
and environmental constraints to ensure comprehensive test coverage tracking.
"""

from .tracker import TestingIssueTracker, log_testing_issue, get_testing_tracker

__all__ = ['TestingIssueTracker', 'log_testing_issue', 'get_testing_tracker']
