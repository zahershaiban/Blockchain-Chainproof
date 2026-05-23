# Imports csv so the dataset can be read row by row.
import csv
# Imports json so the saved hashes.json file can be loaded.
import json
# Imports Path to build file paths that work on Windows, macOS, and Linux.
from pathlib import Path

# Imports Merkle proof functions from backend/merkle_tree.py.
from merkle_tree import generate_merkle_proof, verify_merkle_proof


# Finds the main chainproof/ project folder by going one level above backend/.
BASE_DIR = Path(__file__).resolve().parent.parent

# Points to the dataset that will be used to generate a proof for one row.
DATASET_PATH = BASE_DIR / "data" / "health_dataset_1000.csv"
# Points to the saved metadata file that contains the trusted Merkle Root.
HASHES_PATH = BASE_DIR / "artifacts" / "hashes.json"


# Loads all CSV rows as comma-separated strings.
def load_csv_rows(path: Path) -> list[str]:
    # Creates an empty list for dataset rows.
    rows = []

    # Opens the dataset file in text mode.
    with open(path, "r", encoding="utf-8") as file:
        # Creates a CSV reader for the file.
        reader = csv.reader(file)

        # Loops through each row in the CSV file.
        for row in reader:
            # Converts the list of columns into one string and adds it to rows.
            rows.append(",".join(row))

    # Returns the dataset rows as strings.
    return rows


# Main function that verifies one selected row against the saved Merkle Root.
def main():
    # Loads all rows from the dataset.
    rows = load_csv_rows(DATASET_PATH)

    # Opens hashes.json, which contains the trusted dataset Merkle Root.
    with open(HASHES_PATH, "r", encoding="utf-8") as file:
        # Parses the JSON metadata into a Python dictionary.
        hashes = json.load(file)

    # Reads the trusted Merkle Root from hashes.json.
    root = hashes["dataset_merkle_root"]

    # Selects the row index to verify; 1 means the first data row after the CSV header.
    row_index = 1
    # Gets the actual row string from the dataset.
    row = rows[row_index]

    # Generates the Merkle proof for the selected row.
    proof = generate_merkle_proof(rows, row_index)
    # Verifies the selected row against the trusted Merkle Root.
    is_valid = verify_merkle_proof(row, proof, root)

    # Prints the tested row index.
    print("Row index:", row_index)
    # Prints the row content that was verified.
    print("Row:", row)
    # Prints the trusted Merkle Root.
    print("Merkle Root:", root)
    # Prints True if the row is valid, otherwise False.
    print("Proof valid:", is_valid)


# Runs main() only when this file is executed directly.
if __name__ == "__main__":
    # Starts the row verification test.
    main()
