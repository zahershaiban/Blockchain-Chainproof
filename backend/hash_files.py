# Imports the csv module so the dataset can be read row by row.
import csv
# Imports hashlib so files can be converted into SHA-256 hashes.
import hashlib
# Imports json so generated hashes and metadata can be saved as JSON files.
import json
# Imports Path to build operating-system-safe file paths.
from pathlib import Path

# Imports the Merkle Tree helper functions from backend/merkle_tree.py.
from merkle_tree import get_merkle_root, generate_merkle_proof, save_merkle_data


# Finds the main chainproof/ project folder by going one level above backend/.
BASE_DIR = Path(__file__).resolve().parent.parent
# Points to the health dataset that will be converted into Merkle Tree leaves.
DATASET_PATH = BASE_DIR / "data" /"health_dataset_1000.csv"
# Older hashes path variable; it is overwritten below by the artifacts/hashes.json path.
HASHES_PATH = BASE_DIR / "hashes.json"
# Points to the trained machine-learning model file created by train_model.py.
MODEL_PATH = BASE_DIR / "artifacts" / "model.pkl"
# Points to the model configuration JSON created by train_model.py.
CONFIG_PATH = BASE_DIR / "artifacts" / "config.json"
# Points to the final hash metadata file used by the frontend and blockchain registration script.
HASHES_PATH = BASE_DIR / "artifacts" / "hashes.json"
# Points to the full saved Merkle Tree data file.
MERKLE_PATH = BASE_DIR / "artifacts" / "dataset_merkle.json"


# Defines a function that calculates the SHA-256 hash of a whole file.
def sha256_file(path: Path) -> str:
    # Creates a new SHA-256 hash object.
    hasher = hashlib.sha256()

    # Opens the file in binary mode so every byte is hashed exactly.
    with open(path, "rb") as file:
        # Reads the file in chunks to support large files without loading everything into memory.
        while chunk := file.read(8192):
            # Adds the current file chunk into the SHA-256 calculation.
            hasher.update(chunk)

    # Returns the final SHA-256 hash as a hexadecimal string.
    return hasher.hexdigest()


# Defines a function that loads every CSV row as one string.
def load_csv_rows(path: Path) -> list[str]:
    # Creates an empty list that will store the dataset rows.
    rows = []

    # Opens the CSV file in text mode using UTF-8 encoding.
    with open(path, "r", encoding="utf-8") as file:
        # Creates a CSV reader that correctly separates columns.
        reader = csv.reader(file)

        # Loops through every row in the CSV file.
        for row in reader:
            # Converts the row list back into one comma-separated string for hashing.
            row_as_string = ",".join(row)
            # Adds the row string to the list of rows.
            rows.append(row_as_string)

    # Returns all rows as strings.
    return rows


# Main function that creates dataset Merkle root, model hash, config hash, and output JSON files.
def main():
    # Loads all dataset rows from health_dataset_1000.csv.
    rows = load_csv_rows(DATASET_PATH)

    # Builds a Merkle Tree from the dataset rows and returns only the final root hash.
    dataset_merkle_root = get_merkle_root(rows)
    # Hashes the trained model file so later changes to model.pkl can be detected.
    model_hash = sha256_file(MODEL_PATH)
    # Hashes the config file so later changes to training settings can be detected.
    config_hash = sha256_file(CONFIG_PATH)

    # Creates the metadata object that represents the registered model version.
    hashes = {
    # Human-readable model name shown in the frontend.
    "model_name": "Health Risk Classifier",
    # Version number for this model and dataset registration.
    "version": "1.0.0",
    # Name of the dataset file used to build the Merkle root.
    "dataset_name": "health_dataset_1000.csv",
    # Merkle Root of the dataset; this is the value that should be stored on-chain.
    "dataset_merkle_root": dataset_merkle_root,
    # SHA-256 hash of the trained ML model file.
    "model_hash": model_hash,
    # SHA-256 hash of the model configuration file.
    "config_hash": config_hash
}

    # Opens artifacts/hashes.json for writing.
    with open(HASHES_PATH, "w", encoding="utf-8") as file:
        # Saves the metadata dictionary as readable JSON.
        json.dump(hashes, file, indent=4)

    # Saves the full Merkle Tree structure to artifacts/dataset_merkle.json.
    save_merkle_data(rows, str(MERKLE_PATH))

    # Selects one example row to demonstrate Merkle proof generation.
    example_row_index = 1
    # Generates the Merkle proof for the selected example row.
    proof = generate_merkle_proof(rows, example_row_index)

    # Prints where the hashes JSON file was saved.
    print("Hashes saved to:", HASHES_PATH)
    # Prints where the Merkle Tree JSON file was saved.
    print("Merkle data saved to:", MERKLE_PATH)
    # Prints the dataset Merkle Root for easy copying to the blockchain step.
    print("Dataset Merkle Root:", dataset_merkle_root)
    # Prints the selected example row.
    print("Example row:", rows[example_row_index])
    # Prints the Merkle proof for the selected example row in formatted JSON.
    print("Example proof:", json.dumps(proof, indent=4))


# Runs main() only when this file is executed directly.
if __name__ == "__main__":
    # Starts the hashing and Merkle generation process.
    main()
