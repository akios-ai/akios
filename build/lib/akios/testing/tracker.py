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
Automatic Testing Issue Tracker

Provides intelligent tracking of testing limitations, partial tests, and environmental
constraints to ensure comprehensive test coverage without manual intervention.
"""

import os
import sys
import json
import time
import platform
from typing import Dict, List, Optional, Any
from pathlib import Path


class TestingIssueTracker:
    """
    Automatic tracker for testing issues and limitations.

    Intelligently detects and logs testing constraints, partial implementations,
    environmental limitations, and platform-specific issues during test execution.
    """

    def __init__(self, log_file: str = ".akios/testing_issues.json"):
        """
        Initialize the testing issue tracker.

        Args:
            log_file: Path to the testing issues log file (relative to project root)
        """
        self.log_file = Path(log_file)
        self.issues: List[Dict[str, Any]] = []
        self.session_start = time.time()
        self.platform_info = self._get_platform_info()

        # Load existing issues if file exists
        self._load_existing_issues()

        # Register automatic detection hooks
        self._register_detection_hooks()

    def _get_platform_info(self) -> Dict[str, Any]:
        """Get comprehensive platform information for issue context"""
        return {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'is_docker': os.path.exists('/.dockerenv'),
            'has_seccomp': self._check_seccomp_available(),
            'has_gpu': self._check_gpu_available(),
            'network_connectivity': self._check_network_connectivity()
        }

    def _check_seccomp_available(self) -> bool:
        """Check if seccomp syscall filtering is available"""
        try:
            import seccomp
            return True
        except ImportError:
            return False

    def _check_gpu_available(self) -> bool:
        """Check if GPU acceleration is available"""
        # Simple GPU detection - could be enhanced
        try:
            import subprocess
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.SubprocessError):
            return False

    def _check_network_connectivity(self) -> bool:
        """Check basic network connectivity"""
        try:
            import socket
            # Try to connect to a well-known host on port 53 (DNS)
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except (socket.error, OSError):
            return False

    def _load_existing_issues(self):
        """Load existing testing issues from log file"""
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r') as f:
                    data = json.load(f)
                    self.issues = data.get('issues', [])
            except (json.JSONDecodeError, FileNotFoundError):
                self.issues = []

    def _register_detection_hooks(self):
        """Register automatic detection hooks for common testing limitations"""
        # These will be called during testing to automatically detect issues
        pass

    def log_issue(self, category: str, severity: str, title: str,
                  description: str, impact: str = "", recommendation: str = "",
                  auto_detected: bool = True, context: Optional[Dict[str, Any]] = None):
        """
        Log a testing issue with comprehensive metadata and deduplication.

        Args:
            category: Issue category (environment, platform, dependency, etc.)
            severity: Issue severity (minor, important, critical)
            title: Brief issue title
            description: Detailed issue description
            impact: Impact on testing or functionality
            recommendation: Recommended action or workaround
            auto_detected: Whether this was automatically detected
            context: Additional context information
        """
        # Check for duplicate issues to prevent clutter
        issue_key = self._generate_issue_key(category, title, description)

        # Look for existing issue with same key
        existing_issue = self._find_existing_issue(issue_key)

        if existing_issue:
            # Increment occurrence count instead of creating duplicate
            existing_issue['occurrence_count'] = existing_issue.get('occurrence_count', 1) + 1
            existing_issue['last_occurrence'] = time.time()
            self._save_issues()
            return

        # Create new issue
        issue = {
            'id': f"TEST-{int(time.time() * 1000)}",
            'timestamp': time.time(),
            'category': category,
            'severity': severity,
            'title': title,
            'description': description,
            'impact': impact,
            'recommendation': recommendation,
            'auto_detected': auto_detected,
            'platform_context': self.platform_info,
            'context': context or {},
            'session_duration': time.time() - self.session_start,
            'issue_key': issue_key,
            'occurrence_count': 1,
            'first_occurrence': time.time(),
            'last_occurrence': time.time()
        }

        self.issues.append(issue)
        self._save_issues()

        if os.getenv("AKIOS_DEBUG_ENABLED") == "1":
            detection_note = " [AUTO-DETECTED]" if auto_detected else ""
            print(f"📋 Testing Issue Logged{detection_note}: {title}", file=sys.stderr)

    def _generate_issue_key(self, category: str, title: str, description: str) -> str:
        """
        Generate a unique key for issue deduplication.

        Args:
            category: Issue category
            title: Issue title
            description: Issue description

        Returns:
            Unique string key for this issue type
        """
        import hashlib

        # Create a normalized key from the essential issue characteristics
        key_components = [
            category.lower().strip(),
            title.lower().strip(),
            description.lower().strip()[:200]  # Limit description length for key
        ]

        key_string = "|".join(key_components)
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()[:16]

    def _find_existing_issue(self, issue_key: str) -> Optional[Dict[str, Any]]:
        """
        Find an existing issue with the given key.

        Args:
            issue_key: Unique issue identifier

        Returns:
            Existing issue dict if found, None otherwise
        """
        for issue in self.issues:
            if issue.get('issue_key') == issue_key:
                return issue
        return None

    def detect_environment_limitation(self, feature: str, reason: str,
                                    impact: str = "Cannot fully test feature",
                                    recommendation: str = "Test on appropriate environment"):
        """
        Automatically log environment-related testing limitations.

        Args:
            feature: Feature or functionality that cannot be tested
            reason: Reason why it cannot be tested
            impact: Testing impact description
            recommendation: Recommended testing approach
        """
        self.log_issue(
            category="environment",
            severity="important",
            title=f"Environment limitation: {feature}",
            description=f"Cannot test {feature} due to: {reason}",
            impact=impact,
            recommendation=recommendation,
            context={'feature': feature, 'limitation_reason': reason}
        )

    def detect_platform_limitation(self, feature: str, required_platform: str,
                                 current_platform: Optional[str] = None):
        """
        Automatically log platform-specific testing limitations.

        Args:
            feature: Feature limited to specific platforms
            required_platform: Platform requirement description
            current_platform: Current platform (auto-detected if None)
        """
        current = current_platform or self.platform_info['system']
        self.log_issue(
            category="platform",
            severity="important",
            title=f"Platform limitation: {feature} not available on {current}",
            description=f"Feature '{feature}' requires {required_platform}, but running on {current}",
            impact="Platform-specific functionality cannot be tested",
            recommendation=f"Test on {required_platform} environment for full coverage",
            context={
                'feature': feature,
                'required_platform': required_platform,
                'current_platform': current
            }
        )

    def detect_dependency_limitation(self, feature: str, dependency: str,
                                   reason: str = "not installed or available"):
        """
        Automatically log dependency-related testing limitations.

        Args:
            feature: Feature requiring the dependency
            dependency: Missing or unavailable dependency
            reason: Why the dependency is not available
        """
        self.log_issue(
            category="dependency",
            severity="important",
            title=f"Dependency limitation: {dependency} {reason}",
            description=f"Feature '{feature}' requires '{dependency}' which is {reason}",
            impact="Dependency-related functionality cannot be tested",
            recommendation=f"Install {dependency} or test in environment where it's available",
            context={'feature': feature, 'dependency': dependency, 'reason': reason}
        )

    def detect_partial_test(self, feature: str, tested_aspects: List[str],
                          untested_aspects: List[str], reason: str):
        """
        Log partial testing coverage for specific features.

        Args:
            feature: Feature being partially tested
            tested_aspects: List of aspects that were tested
            untested_aspects: List of aspects that could not be tested
            reason: Reason for partial testing
        """
        self.log_issue(
            category="coverage",
            severity="minor",
            title=f"Partial testing: {feature}",
            description=f"Feature '{feature}' partially tested. Tested: {', '.join(tested_aspects)}. "
                       f"Untested: {', '.join(untested_aspects)}. Reason: {reason}",
            impact="Incomplete test coverage for feature",
            recommendation="Consider additional testing scenarios or environments",
            context={
                'feature': feature,
                'tested_aspects': tested_aspects,
                'untested_aspects': untested_aspects,
                'reason': reason
            }
        )

    def detect_performance_limitation(self, test_type: str, limitation: str,
                                    impact: str = "Cannot measure performance accurately"):
        """
        Log performance testing limitations.

        Args:
            test_type: Type of performance test (cpu, memory, network, etc.)
            limitation: Specific limitation encountered
            impact: Impact on performance testing
        """
        self.log_issue(
            category="performance",
            severity="minor",
            title=f"Performance testing limitation: {test_type}",
            description=f"Cannot fully test {test_type} performance due to: {limitation}",
            impact=impact,
            recommendation="Consider testing in environment with appropriate resources",
            context={'test_type': test_type, 'limitation': limitation}
        )

    def detect_security_limitation(self, security_feature: str, limitation: str,
                                 impact: str = "Security testing incomplete"):
        """
        Log security testing limitations.

        Args:
            security_feature: Security feature being tested
            limitation: Security testing limitation
            impact: Impact on security validation
        """
        self.log_issue(
            category="security",
            severity="important",
            title=f"Security testing limitation: {security_feature}",
            description=f"Cannot fully validate {security_feature} due to: {limitation}",
            impact=impact,
            recommendation="Test in environment with full security capabilities",
            context={'security_feature': security_feature, 'limitation': limitation}
        )

    def _save_issues(self):
        """Save all issues to the log file"""
        try:
            data = {
                'session_info': {
                    'start_time': self.session_start,
                    'platform_info': self.platform_info,
                    'total_issues': len(self.issues)
                },
                'issues': self.issues
            }

            # Ensure parent directory exists
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.log_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)

        except OSError:
            # If we can't save, continue without logging
            pass

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of logged testing issues"""
        categories = {}
        severities = {'minor': 0, 'important': 0, 'critical': 0}
        unique_issues = 0
        total_occurrences = 0

        # Count unique issues by tracking issue keys
        seen_keys = set()

        for issue in self.issues:
            cat = issue.get('category', 'unknown')
            sev = issue.get('severity', 'unknown')
            occurrences = issue.get('occurrence_count', 1)
            issue_key = issue.get('issue_key')

            # Count each unique issue once
            if issue_key and issue_key not in seen_keys:
                seen_keys.add(issue_key)
                unique_issues += 1
                categories[cat] = categories.get(cat, 0) + 1
                if sev in severities:
                    severities[sev] += 1

            total_occurrences += occurrences

        return {
            'total_issues': len(self.issues),
            'unique_issues': unique_issues,
            'total_occurrences': total_occurrences,
            'by_category': categories,
            'by_severity': severities,
            'platform_info': self.platform_info,
            'session_duration': time.time() - self.session_start
        }


# Global instance for easy access
_global_tracker = None

def get_testing_tracker() -> TestingIssueTracker:
    """Get the global testing issue tracker instance"""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = TestingIssueTracker()
    return _global_tracker

def log_testing_issue(category: str, severity: str, title: str,
                      description: str, **kwargs):
    """
    Convenience function to log a testing issue using the global tracker.

    Args:
        category: Issue category
        severity: Issue severity
        title: Issue title
        description: Issue description
        **kwargs: Additional parameters passed to log_issue
    """
    tracker = get_testing_tracker()
    tracker.log_issue(category, severity, title, description, **kwargs)
