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
Merkle node structure and hashing for tamper-evident audit ledger.

Binary Merkle tree nodes with SHA-256 cryptographic integrity.
"""

import hashlib
from typing import Optional


class MerkleNode:
    """
    A node in the Merkle tree.

    Each node contains a hash and references to left/right children.
    """

    def __init__(self,
                 left: Optional['MerkleNode'] = None,
                 right: Optional['MerkleNode'] = None,
                 data: Optional[str] = None,
                 hash_value: Optional[str] = None):
        self.left = left
        self.right = right
        self.data = data
        if hash_value is not None:
            # Pre-computed hash - use it directly
            self._hash = hash_value
            self._precomputed = True
        else:
            # Compute hash normally
            self._hash = self._compute_hash()
            self._precomputed = False

    @property
    def hash(self) -> str:
        """Get the cryptographic hash of this node"""
        return self._hash

    def _compute_hash(self) -> str:
        """Compute the SHA-256 hash for this node"""
        if self.is_leaf():
            # Leaf node: hash the data (unless pre-computed hash provided)
            if self.data is None:
                # This should not happen - leaves should have data unless hash is pre-computed
                raise ValueError("Leaf node must have data or pre-computed hash")
            if self.data == "":
                # Special case: empty data for pre-computed hashes
                return hashlib.sha256(b"").hexdigest()
            data_bytes = self.data.encode('utf-8')
            return hashlib.sha256(data_bytes).hexdigest()
        else:
            # Internal node: hash concatenation of child hashes
            if self.left is None or self.right is None:
                raise ValueError("Internal node must have both children")
            combined = self.left.hash + self.right.hash
            combined_bytes = combined.encode('utf-8')
            return hashlib.sha256(combined_bytes).hexdigest()

    def is_leaf(self) -> bool:
        """Check if this is a leaf node"""
        return self.left is None and self.right is None

    def is_internal(self) -> bool:
        """Check if this is an internal node"""
        return not self.is_leaf()


def create_leaf_node(data: str) -> MerkleNode:
    """Create a leaf node with data"""
    return MerkleNode(data=data)


def create_internal_node(left: MerkleNode, right: MerkleNode) -> MerkleNode:
    """Create an internal node from two child nodes"""
    return MerkleNode(left=left, right=right)