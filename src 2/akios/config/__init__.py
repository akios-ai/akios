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
Configuration module - Secure, type-safe settings management

Provides centralized configuration loading and validation for all AKIOS components.
"""

from .settings import Settings
from .loader import get_settings, validate_config
from .validation import validate_env_file
from .modes import switch_to_real_api_mode, get_current_mode

__all__ = ["Settings", "get_settings", "validate_config", "validate_env_file", "switch_to_real_api_mode", "get_current_mode"]
