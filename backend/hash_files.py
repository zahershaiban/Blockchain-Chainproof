import csv
import hashlib
import json
import os
from pathlib import Path

from merkle_tree import get_merkle_root, generate_merkle_proof, save_merkle_data


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"


def load_env_file(path: Path) -> None:
    """
    Loads simple KEY=VALUE pairs from .env into os.environ.
    This avoids requiring python-dotenv.
    Existing environment variables are not overwritten.
    """
    if not path.exists():
        return

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            os.environ.setdefault(key, value)


def resolve_path(value: str) -> Path:
    """
    Converts a path from .env into an absolute path.
    If the path is relative, it is resolved from the project root.
    """
    path = Path(value)

    if path.is_absolute():
        return path

    return BASE_DIR / path


load_env_file(ENV_PATH)


MODEL_NAME = os.getenv("CHAINPROOF_MODEL_NAME", "Health Risk Classifier")
MODEL_VERSION = os.getenv("CHAINPROOF_MODEL_VERSION", "1.0.0")

DATASET_PATH = resolve_path(
    os.getenv("CHAINPROOF_DATASET_PATH", "data/health_dataset_1000.csv")
)

DATASET_NAME = os.getenv("CHAINPROOF_DATASET_NAME", DATASET_PATH.name)

MODEL_PATH = resolve_path(
    os.getenv("CHAINPROOF_MODEL_PATH", "artifacts/model.pkl")
)

CONFIG_PATH = resolve_path(
    os.getenv("CHAINPROOF_CONFIG_PATH", "artifacts/config.json")
)

HASHES_PATH = resolve_path(
    os.getenv("CHAINPROOF_HASHES_PATH", "artifacts/hashes.json")
)

MERKLE_PATH = resolve_path(
    os.getenv("CHAINPROOF_MERKLE_PATH", "artifacts/dataset_merkle.json")
)

EXAMPLE_ROW_INDEX = int(os.getenv("CHAINPROOF_EXAMPLE_ROW_INDEX", "1"))


def sha256_file(path: Path) -> str:
    """
    Calculates the SHA-256 hash of a file.
    The file is read in chunks, so large files do not need to be loaded fully into memory.
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    hasher = hashlib.sha256()

    with open(path, "rb") as file:
        while chunk := file.read(8192):
            hasher.update(chunk)

    return hasher.hexdigest()


def load_csv_rows(path: Path) -> list[str]:
    """
    Loads the CSV dataset row by row.
    Each row is converted into one comma-separated string before hashing.
    """
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    rows = []

    with open(path, "r", encoding="utf-8") as file:
        reader = csv.reader(file)

        for row in reader:
            row_as_string = ",".join(row)
            rows.append(row_as_string)

    if not rows:
        raise ValueError(f"Dataset is empty: {path}")

    return rows


def main():
    HASHES_PATH.parent.mkdir(parents=True, exist_ok=True)
    MERKLE_PATH.parent.mkdir(parents=True, exist_ok=True)

    rows = load_csv_rows(DATASET_PATH)

    if EXAMPLE_ROW_INDEX < 0 or EXAMPLE_ROW_INDEX >= len(rows):
        raise ValueError(
            f"CHAINPROOF_EXAMPLE_ROW_INDEX={EXAMPLE_ROW_INDEX} is invalid. "
            f"Dataset has {len(rows)} rows."
        )

    dataset_merkle_root = get_merkle_root(rows)
    model_hash = sha256_file(MODEL_PATH)
    config_hash = sha256_file(CONFIG_PATH)

    hashes = {
        "model_name": MODEL_NAME,
        "version": MODEL_VERSION,
        "dataset_name": DATASET_NAME,
        "dataset_path": str(DATASET_PATH.relative_to(BASE_DIR))
        if DATASET_PATH.is_relative_to(BASE_DIR)
        else str(DATASET_PATH),
        "dataset_merkle_root": dataset_merkle_root,
        "model_hash": model_hash,
        "config_hash": config_hash,
    }

    with open(HASHES_PATH, "w", encoding="utf-8") as file:
        json.dump(hashes, file, indent=4)

    save_merkle_data(rows, str(MERKLE_PATH))

    proof = generate_merkle_proof(rows, EXAMPLE_ROW_INDEX)

    print("Model name:", MODEL_NAME)
    print("Model version:", MODEL_VERSION)
    print("Dataset:", DATASET_PATH)
    print("Hashes saved to:", HASHES_PATH)
    print("Merkle data saved to:", MERKLE_PATH)
    print("Dataset Merkle Root:", dataset_merkle_root)
    print("Example row index:", EXAMPLE_ROW_INDEX)
    print("Example row:", rows[EXAMPLE_ROW_INDEX])
    print("Example proof:", json.dumps(proof, indent=4))


if __name__ == "__main__":
    main()