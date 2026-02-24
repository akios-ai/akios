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

from pathlib import Path

# Try development mode first (pyproject.toml in grandparent directory)
try:
    pyproject_path = Path(__file__).parent.parent.parent.parent / "pyproject.toml"
    if pyproject_path.exists():
        with open(pyproject_path, "r") as f:
            for line in f:
                if line.startswith("version = "):
                    __version__ = line.split('"')[1]
                    raise StopIteration  # Found it, exit early
    # If we get here, pyproject.toml exists but no version found
    raise FileNotFoundError
except StopIteration:
    pass  # Successfully found version
except (FileNotFoundError, OSError):
    # Installed package mode: Read from package metadata
    try:
        from importlib.metadata import version
        __version__ = version("akios")
    except Exception:
        __version__ = "unknown"

try:
    __version_info__ = tuple(int(x) for x in __version__.split("."))
except (ValueError, AttributeError):
    __version_info__ = (0, 0, 0)

# Version metadata
VERSION_MAJOR = 1
VERSION_MINOR = 0
VERSION_PATCH = 16
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
