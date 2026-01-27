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
Core Services Version Information

Provides version information for the AKIOS core services package.
"""

__version__ = "1.0.0"
__version_info__ = (1, 0, 0)

# Version metadata
VERSION_MAJOR = 1
VERSION_MINOR = 0
VERSION_PATCH = 0
VERSION_SUFFIX = ""

# Build information (populated by CI/CD)
BUILD_DATE = None
BUILD_COMMIT = None
BUILD_BRANCH = None

def get_version_info():
    """
    Get detailed version information.

    Returns:
        dict: Version information including build details
    """
    return {
        "version": __version__,
        "version_info": __version_info__,
        "major": VERSION_MAJOR,
        "minor": VERSION_MINOR,
        "patch": VERSION_PATCH,
        "suffix": VERSION_SUFFIX,
        "build_date": BUILD_DATE,
        "build_commit": BUILD_COMMIT,
        "build_branch": BUILD_BRANCH
    }

def get_version_string():
    """
    Get a human-readable version string.

    Returns:
        str: Formatted version string with build info if available
    """
    version_str = __version__

    if BUILD_COMMIT:
        version_str += f" ({BUILD_COMMIT[:8]})"

    if BUILD_DATE:
        version_str += f" - {BUILD_DATE}"

    return version_str
