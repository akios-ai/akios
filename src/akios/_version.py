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

from pathlib import Path

# Try development mode first (pyproject.toml in parent directory)
try:
    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
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
