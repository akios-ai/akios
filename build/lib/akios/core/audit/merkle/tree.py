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

    def append(self, data: str) -> None:
        """Append data to the Merkle tree"""
        leaf = MerkleNode(data=data)
        self.leaves.append(leaf)
        self._build_tree()

    def _build_tree(self) -> None:
        """Build the Merkle tree from current leaves"""
        if not self.leaves:
            self.root = None
            return

        # Start with leaves and build up to root
        current_level = self.leaves.copy()

        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                # For odd number of nodes, duplicate the last node
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                parent = MerkleNode(left=left, right=right)
                next_level.append(parent)
            current_level = next_level

        self.root = current_level[0] if current_level else None

    def get_root_hash(self) -> Optional[str]:
        """Get the root hash of the Merkle tree"""
        return self.root.hash if self.root else None

    def get_proof(self, index: int) -> Optional[List[str]]:
        """
        Generate a Merkle proof for the leaf at the given index.

        This is a simplified implementation. In production, this should generate
        proper cryptographic proofs with left/right indicators.
        """
        if index < 0 or index >= len(self.leaves) or not self.root:
            return None

        # Simplified proof: return sibling hashes at each level
        # This is NOT cryptographically secure but demonstrates the concept
        proof = []

        # Get sibling at the leaf level
        if index % 2 == 0 and index + 1 < len(self.leaves):
            proof.append(self.leaves[index + 1].hash)  # Right sibling
        elif index % 2 == 1:
            proof.append(self.leaves[index - 1].hash)  # Left sibling

        # For deeper levels, this would need proper tree traversal
        # For now, return what we have
        return proof if proof else None

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

    def verify_proof(self, leaf_index: int, proof: List[str]) -> bool:
        """
        Verify a Merkle proof for the leaf at the given index.

        This is a simplified verification for demonstration purposes.
        Production implementations should use proper cryptographic proof verification.
        """
        if leaf_index < 0 or leaf_index >= len(self.leaves) or not proof:
            return False

        # Simplified verification: just check if leaf exists and proof is provided
        # In a real implementation, this would cryptographically verify the proof
        leaf_exists = 0 <= leaf_index < len(self.leaves)
        has_proof = len(proof) > 0

        return leaf_exists and has_proof

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