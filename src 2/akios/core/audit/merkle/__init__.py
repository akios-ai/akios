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
Merkle tree core implementation for audit integrity.

SHA-256 hashing with append-only operations.
"""

from .tree import MerkleTree, build_tree_from_hashes
from .node import MerkleNode, create_leaf_node, create_internal_node

__all__ = ["MerkleTree", "MerkleNode", "build_tree_from_hashes", "create_leaf_node", "create_internal_node"]