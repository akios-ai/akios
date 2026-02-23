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
Merkle tree implementation for audit integrity.

Builds tree from events, computes root hash, generates proofs.
"""

import hashlib
import math
from typing import List, Optional

from .node import MerkleNode


class MerkleTree:
    """A binary Merkle tree for cryptographic audit trails"""

    def __init__(self):
        self.leaves: List[MerkleNode] = []
        self.root: Optional[MerkleNode] = None
        self._levels: List[List[MerkleNode]] = []

    def append(self, data: str) -> None:
        """Append data to the Merkle tree"""
        leaf = MerkleNode(data=data)
        self.leaves.append(leaf)
        self._build_tree()

    def _build_tree(self) -> None:
        """Build the Merkle tree from current leaves, storing all levels for proof generation"""
        if not self.leaves:
            self.root = None
            self._levels = []
            return

        # Start with leaves and build up to root, storing each level
        current_level = self.leaves.copy()
        self._levels = [current_level]

        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                # For odd number of nodes, duplicate the last node
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                parent = MerkleNode(left=left, right=right)
                next_level.append(parent)
            current_level = next_level
            self._levels.append(current_level)

        self.root = current_level[0] if current_level else None

    def get_root_hash(self) -> Optional[str]:
        """Get the root hash of the Merkle tree"""
        return self.root.hash if self.root else None

    def get_proof(self, index: int) -> Optional[List[dict]]:
        """
        Generate a Merkle proof for the leaf at the given index.

        Returns O(log n) sibling hashes needed to recompute the root hash,
        enabling cryptographic verification that a leaf belongs to the tree.

        Each proof element is {"position": "left"|"right", "hash": "<hex>"}
        indicating the sibling's position relative to the current node.

        Returns:
            List of proof steps, or None if index is invalid.
            Empty list for single-leaf trees (leaf IS the root).
        """
        if index < 0 or index >= len(self.leaves) or not self.root:
            return None

        proof = []
        idx = index

        # Walk from leaf level up to (but not including) the root level
        for level in self._levels[:-1]:
            if idx % 2 == 0:
                # Current node is a left child; sibling is on the right
                sibling_idx = idx + 1
                if sibling_idx < len(level):
                    proof.append({"position": "right", "hash": level[sibling_idx].hash})
                else:
                    # Odd node count: node was duplicated during tree build
                    proof.append({"position": "right", "hash": level[idx].hash})
            else:
                # Current node is a right child; sibling is on the left
                sibling_idx = idx - 1
                proof.append({"position": "left", "hash": level[sibling_idx].hash})

            # Move to parent index
            idx = idx // 2

        return proof

    def _get_all_nodes(self) -> List['MerkleNode']:
        """Get all nodes in the tree (for proof generation)"""
        if not self.root:
            return []

        nodes = []
        queue = [self.root]

        while queue:
            node = queue.pop(0)
            nodes.append(node)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)

        return nodes

    def _get_height(self) -> int:
        """Calculate the height of the tree"""
        if not self.leaves:
            return 0
        # Height is the number of levels, minimum 1 for a single leaf
        return max(1, math.ceil(math.log2(len(self.leaves))))

    def verify_proof(self, leaf_index: int, proof: List[dict]) -> bool:
        """
        Cryptographically verify a Merkle proof for the leaf at the given index.

        Recomputes the root hash from the leaf hash and proof siblings,
        then compares against the tree's actual root hash.

        Args:
            leaf_index: Index of the leaf to verify
            proof: List of {"position": "left"|"right", "hash": "<hex>"} steps

        Returns:
            True if the proof cryptographically verifies against the root hash
        """
        if leaf_index < 0 or leaf_index >= len(self.leaves) or not self.root:
            return False

        # Empty proof is valid only for single-leaf trees
        if not proof:
            return len(self.leaves) == 1 and self.leaves[leaf_index].hash == self.root.hash

        try:
            current_hash = self.leaves[leaf_index].hash

            for step in proof:
                sibling_hash = step["hash"]
                position = step["position"]

                if position == "left":
                    # Sibling is on the left: H(sibling || current)
                    combined = sibling_hash + current_hash
                elif position == "right":
                    # Sibling is on the right: H(current || sibling)
                    combined = current_hash + sibling_hash
                else:
                    return False  # Invalid position

                current_hash = hashlib.sha256(combined.encode('utf-8')).hexdigest()

            return current_hash == self.root.hash

        except (KeyError, TypeError, AttributeError):
            return False

    def size(self) -> int:
        """Get the number of leaves in the tree"""
        return len(self.leaves)

    def __repr__(self) -> str:
        root_hash = self.get_root_hash()[:8] if self.get_root_hash() else None
        return f"MerkleTree(leaves={len(self.leaves)}, root={root_hash}...)"


def build_tree_from_hashes(leaf_hashes: List[str]) -> MerkleTree:
    """
    Build a Merkle tree from a list of pre-calculated leaf hashes.

    Args:
        leaf_hashes: List of SHA-256 hashes as hex strings

    Returns:
        MerkleTree instance with the given hashes as leaves
    """
    tree = MerkleTree()
    # Create leaf nodes with pre-computed hashes
    # Use empty data since hash is pre-computed and won't be recalculated
    tree.leaves = [MerkleNode(data="", hash_value=hash_val) for hash_val in leaf_hashes]
    tree._build_tree()
    return tree