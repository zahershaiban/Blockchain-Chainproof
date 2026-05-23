# ChainProof – Tamper-Proof AI Model Registry

ChainProof is a blockchain-based audit prototype for AI model training. The project proves that a model, its configuration, and its training dataset can be registered in a tamper-evident way.

The current version uses a **Merkle Tree** for the dataset. Instead of storing or rehashing the entire CSV file every time, ChainProof stores one **dataset Merkle Root**. An auditor can verify one selected row with a short Merkle proof.

---

## 1. What problem does ChainProof solve?

Companies train AI models using datasets that may change over time. Later, an auditor may ask:

- Was this model trained with the approved dataset?
- Was a patient/transaction/training record modified after training?
- Is the model file the same file that was originally registered?
- Is the training configuration the same configuration used originally?

A normal database can be changed later. ChainProof uses hashes, Merkle Trees, and blockchain storage to make changes detectable.

---

## 2. Main idea

The program creates three important proofs:

1. **Dataset Merkle Root**
   - Every CSV row is hashed.
   - Row hashes are combined into a Merkle Tree.
   - The final root hash represents the whole dataset.

2. **Model hash**
   - The trained `model.pkl` file is hashed with SHA-256.
   - If the model file changes, the hash changes.

3. **Config hash**
   - The `config.json` file is hashed with SHA-256.
   - If training settings change, the hash changes.

These values are saved into:

```text
artifacts/hashes.json
```

The most important value for dataset auditing is:

```text
dataset_merkle_root
```

---

## 3. Project structure

```text
chainproof/
├── artifacts/
│   ├── config.json
│   ├── dataset_merkle.json
│   ├── hashes.json
│   └── model.pkl
│
├── backend/
│   ├── hash_files.py
│   ├── merkle_tree.py
│   ├── register_model.py
│   ├── train_model.py
│   └── verify_row.py
│
├── contracts/
│   ├── contracts/
│   │   └── ModelRegistry.sol
│   ├── scripts/
│   │   └── deploy.js
│   ├── test/
│   │   └── ModelRegistry.test.js
│   ├── hardhat.config.js
│   └── package.json
│
├── data/
│   ├── dataset.csv
│   └── health_dataset_1000.csv
│
├── docs/
│   └── demo_script.md
│
└── frontend/
    └── app.py
```

---

## 4. How the program works from start to finish

### Step 1: Train the model

Run:

```bash
python backend/train_model.py
```

This script reads:

```text
data/health_dataset_1000.csv
```

It trains a Random Forest model that predicts:

```text
risk_level
```

It saves:

```text
artifacts/model.pkl
artifacts/config.json
```

### Step 2: Hash the model, config, and dataset

Run:

```bash
python backend/hash_files.py
```

This script:

- loads the dataset rows,
- creates a Merkle Tree from the rows,
- calculates the dataset Merkle Root,
- hashes `model.pkl`,
- hashes `config.json`,
- saves the results into `artifacts/hashes.json`,
- saves the full Merkle Tree into `artifacts/dataset_merkle.json`.

### Step 3: Verify one row locally

Run:

```bash
python backend/verify_row.py
```

This script verifies one selected row against the Merkle Root stored in `hashes.json`.

Expected result:

```text
Proof valid: True
```

### Step 4: Use the Streamlit frontend

Run:

```bash
streamlit run frontend/app.py
```

The app shows the registered model metadata and allows the auditor to upload a CSV file and verify one row.

### Step 5: Tampering demo

Upload the original dataset:

```text
data/health_dataset_1000.csv
```

Verify row index `1`. It should pass.

Then upload a tampered dataset where one value in row `1` was changed. The verification should fail.

This proves that even a small dataset change produces a different Merkle proof result.

---

## 5. Explanation of each file

### `backend/train_model.py`

Job: trains the machine-learning model.

What it does:

- Loads the health dataset with pandas.
- Selects `risk_level` as the target label.
- Removes identifier columns such as `patient_id` and `audit_record_id`.
- Splits the data into training and testing sets.
- Uses `OneHotEncoder` for categorical values.
- Uses `RandomForestClassifier` as the model.
- Saves the trained pipeline as `artifacts/model.pkl`.
- Saves training metadata as `artifacts/config.json`.

Important functions/objects:

- `ColumnTransformer`: applies preprocessing to categorical and numeric columns.
- `Pipeline`: combines preprocessing and model training.
- `RandomForestClassifier`: the AI model.
- `joblib.dump`: saves the model file.

---

### `backend/merkle_tree.py`

Job: builds and verifies Merkle Trees.

This is the core security/audit logic.

Functions:

#### `sha256(data: str) -> str`

Hashes one string using SHA-256.

#### `hash_pair(left: str, right: str) -> str`

Combines two child hashes into one parent hash.

#### `build_merkle_tree(rows: List[str]) -> List[List[str]]`

Builds the full Merkle Tree.

- First level: hash of every dataset row.
- Next levels: pairwise hashes.
- Final level: one root hash.

#### `get_merkle_root(rows: List[str]) -> str`

Returns only the final root hash of the dataset.

#### `generate_merkle_proof(rows: List[str], row_index: int)`

Creates the proof needed to verify one row.

The proof contains sibling hashes and their positions. This allows an auditor to rebuild the path from one row to the root without using the entire dataset.

#### `verify_merkle_proof(row, proof, root) -> bool`

Checks if a row belongs to the dataset represented by the Merkle Root.

Returns:

```text
True
```

if the row is valid, otherwise:

```text
False
```

#### `save_merkle_data(rows, output_path)`

Saves the full Merkle Tree to JSON for debugging and demonstration.

---

### `backend/hash_files.py`

Job: creates all audit hashes.

What it creates:

```text
artifacts/hashes.json
artifacts/dataset_merkle.json
```

What it does:

- Loads the dataset rows.
- Builds the dataset Merkle Root.
- Hashes the trained model file.
- Hashes the config file.
- Saves all important values as JSON.
- Prints an example Merkle proof.

Main output:

```json
{
  "model_name": "Health Risk Classifier",
  "version": "1.0.0",
  "dataset_name": "health_dataset_1000.csv",
  "dataset_merkle_root": "...",
  "model_hash": "...",
  "config_hash": "..."
}
```

---

### `backend/verify_row.py`

Job: local command-line test for Merkle proof verification.

What it does:

- Loads the dataset.
- Loads the trusted Merkle Root from `hashes.json`.
- Selects row index `1`.
- Generates a Merkle proof for that row.
- Verifies the row against the trusted root.
- Prints whether the proof is valid.

This file is useful before testing the frontend.

---

### `frontend/app.py`

Job: provides the auditor web interface.

What the auditor can do:

- See the registered model metadata.
- Upload a dataset CSV file.
- Choose one row index.
- Generate a Merkle proof for that row.
- Verify whether the uploaded row matches the original registered dataset root.

How it works:

1. Loads `artifacts/hashes.json`.
2. Reads the uploaded CSV file.
3. Converts rows into strings.
4. Generates a Merkle proof for the selected row.
5. Compares the proof result with `dataset_merkle_root`.
6. Shows success or failure.

---

### `contracts/contracts/ModelRegistry.sol`

Job: stores model audit metadata on-chain.

Main structure:

```solidity
struct ModelRecord 
```

This stores:

- `modelName`
- `version`
- `datasetMerkleRoot`
- `modelHash`
- `configHash`
- `registeredBy`
- `timestamp`

Main functions:

#### `registerModel(...)`

Stores one model record on-chain.

In the final architecture, this function should receive the Merkle Root from `hashes.json` and store it permanently.

#### `getModel(recordId)`

Reads a registered model record from the blockchain.

---

### `contracts/scripts/deploy.js`

Job: deploys the Solidity smart contract using Hardhat.

Run it from the `contracts/` folder with:

```bash
npx hardhat run scripts/deploy.js --network localhost
```

It prints the deployed contract address.

---

### `backend/register_model.py`

Job: sends the generated hashes to the deployed smart contract.

It uses:

- `web3.py`
- `.env`
- contract ABI
- private key
- deployed contract address

This file is for blockchain integration after the local Merkle proof and frontend demo work.

---

## 6. How the files work together

```text
health_dataset_1000.csv
        ↓
train_model.py
        ↓
model.pkl + config.json
        ↓
hash_files.py
        ↓
hashes.json + dataset_merkle.json
        ↓
frontend/app.py
        ↓
Auditor uploads CSV and verifies one row
```

Blockchain extension:

```text
hashes.json
        ↓
register_model.py
        ↓
ModelRegistry.sol
        ↓
On-chain model registry
```

---

## 7. Why Merkle Trees are used

Without Merkle Trees, an auditor would need to rehash the whole dataset.

With a Merkle Tree, the auditor can verify one row using only:

- the row itself,
- a short Merkle proof,
- the trusted Merkle Root.

For 1000 rows, the proof is about 10 hashes because:

```text
log2(1000) ≈ 10
```

That is why Merkle proofs are scalable.

---

## 8. Commands

From the `chainproof/` folder:

```bash
python backend/train_model.py
python backend/hash_files.py
python backend/verify_row.py
streamlit run frontend/app.py
```

For the Solidity part, from the `chainproof/contracts/` folder:

```bash
npm install
npx hardhat compile
npx hardhat node
npx hardhat run scripts/deploy.js --network localhost
```

---

## 9. Demo script

1. Train the model.
2. Generate the Merkle Root and hashes.
3. Open the frontend.
4. Upload the original health dataset.
5. Verify row index `1`.
6. Show that verification succeeds.
7. Upload a tampered copy of the dataset.
8. Verify the same row index.
9. Show that verification fails.
10. Explain that one changed value breaks the Merkle proof.

---

## 10. Important note for the blockchain step

The local Merkle and frontend parts are working as the main MVP. The blockchain step should store this value:

```text
dataset_merkle_root
```

on-chain in `ModelRegistry.sol`.

The final production-style flow is:

```text
Dataset → Merkle Root → Blockchain Registry → Auditor Verification
```
