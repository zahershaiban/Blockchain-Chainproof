# Imports hashlib to create SHA-256 hashes.
import hashlib
# Imports json to save the Merkle Tree structure as a JSON file.
import json
# Imports type hints to make function inputs and outputs easier to understand.
from typing import List, Dict, Any


# Converts one text value into a SHA-256 hexadecimal hash.
def sha256(data: str) -> str:
    # Encodes the string as UTF-8 bytes, hashes it, and returns the hex digest.
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


# Combines two child hashes into one parent hash.
def hash_pair(left: str, right: str) -> str:
    # Concatenates the left and right hashes, then hashes the combined string.
    return sha256(left + right)


# Builds the complete Merkle Tree from a list of dataset rows.
def build_merkle_tree(rows: List[str]) -> List[List[str]]:
    # Stops the program if the dataset is empty, because an empty tree has no root.
    if not rows:
        # Raises a clear error message for missing or empty datasets.
        raise ValueError("Dataset has no rows")

    # Creates the first tree level by hashing every dataset row separately.
    leaves = [sha256(row) for row in rows]
    # Stores all tree levels; level 0 is the list of leaf hashes.
    tree = [leaves]

    # Starts building upward from the leaf level.
    current_level = leaves

    # Continues until only one hash remains, which becomes the Merkle Root.
    while len(current_level) > 1:
        # Creates an empty list for the next upper level of the tree.
        next_level = []

        # Processes hashes in pairs: index 0 with 1, index 2 with 3, and so on.
        for i in range(0, len(current_level), 2):
            # Takes the left hash in the current pair.
            left = current_level[i]

            # Checks whether a matching right hash exists.
            if i + 1 < len(current_level):
                # Uses the next hash as the right hash.
                right = current_level[i + 1]
            else:
                # Duplicates the left hash if the number of hashes is odd.
                right = left

            # Hashes the pair and stores the parent hash in the next level.
            next_level.append(hash_pair(left, right))

        # Adds the new level to the full tree.
        tree.append(next_level)
        # Moves upward and repeats the process with the newly created level.
        current_level = next_level

    # Returns the complete tree, where tree[-1][0] is the Merkle Root.
    return tree


# Returns only the Merkle Root for a dataset.
def get_merkle_root(rows: List[str]) -> str:
    # Builds the full Merkle Tree.
    tree = build_merkle_tree(rows)
    # Returns the only hash in the final level.
    return tree[-1][0]


# Generates the proof needed to verify one row without rehashing the whole dataset.
def generate_merkle_proof(rows: List[str], row_index: int) -> List[Dict[str, str]]:
    # Builds the Merkle Tree so sibling hashes can be collected.
    tree = build_merkle_tree(rows)

    # Validates that the requested row index exists in the dataset.
    if row_index < 0 or row_index >= len(rows):
        # Raises a clear error when the row index is invalid.
        raise IndexError("Row index out of range")

    # Creates an empty proof list that will store sibling hashes and their positions.
    proof = []
    # Starts from the selected row index at the leaf level.
    index = row_index

    # Loops over every level except the root level.
    for level in tree[:-1]:
        # Checks whether the current hash is a left child.
        if index % 2 == 0:
            # The sibling of a left child is normally one position to the right.
            sibling_index = index + 1
            # Records that the sibling hash should be placed on the right during verification.
            position = "right"
        else:
            # The sibling of a right child is one position to the left.
            sibling_index = index - 1
            # Records that the sibling hash should be placed on the left during verification.
            position = "left"

        # Handles the case where this hash has no sibling because the level length is odd.
        if sibling_index >= len(level):
            # Uses the same hash as its own sibling, matching the tree-building logic.
            sibling_hash = level[index]
        else:
            # Uses the real sibling hash from the current level.
            sibling_hash = level[sibling_index]

        # Adds one proof step containing the sibling position and sibling hash.
        proof.append({
            # Stores whether the sibling is left or right of the current hash.
            "position": position,
            # Stores the sibling hash value.
            "hash": sibling_hash
        })

        # Moves the index upward to the parent position in the next tree level.
        index = index // 2

    # Returns the full Merkle proof for the selected row.
    return proof


# Verifies whether a row belongs to a dataset represented by a Merkle Root.
def verify_merkle_proof(row: str, proof: List[Dict[str, str]], root: str) -> bool:
    # Starts by hashing the row being verified.
    current_hash = sha256(row)

    # Rebuilds the path from the row hash up to the root using the proof.
    for item in proof:
        # Reads the sibling hash for this proof step.
        sibling_hash = item["hash"]

        # Checks whether the sibling hash belongs on the left side.
        if item["position"] == "left":
            # Recreates the parent hash using sibling first, then current hash.
            current_hash = hash_pair(sibling_hash, current_hash)
        else:
            # Recreates the parent hash using current hash first, then sibling hash.
            current_hash = hash_pair(current_hash, sibling_hash)

    # Verification succeeds only if the reconstructed root equals the trusted root.
    return current_hash == root


# Saves the full Merkle Tree and useful metadata into a JSON file.
def save_merkle_data(rows: List[str], output_path: str) -> None:
    # Builds the Merkle Tree from the dataset rows.
    tree = build_merkle_tree(rows)
    # Reads the Merkle Root from the final tree level.
    root = tree[-1][0]

    # Creates a JSON-serializable dictionary containing the tree data.
    data: Dict[str, Any] = {
        # Stores the Merkle Root.
        "merkle_root": root,
        # Stores the number of dataset rows/leaves.
        "leaf_count": len(rows),
        # Stores all leaf hashes.
        "leaves": tree[0],
        # Stores every tree level from leaves to root.
        "tree": tree
    }

    # Opens the output file path for writing.
    with open(output_path, "w", encoding="utf-8") as file:
        # Writes the Merkle data as formatted JSON.
        json.dump(data, file, indent=4)
