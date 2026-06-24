# ChainProof - Tamper-Proof AI Model Registry

ChainProof is a small blockchain-based audit system for machine-learning models. It proves that a trained model, its training configuration, and the dataset used during training have not been silently changed after registration.

The project does **not** store private datasets or model files on the blockchain. Instead, it stores cryptographic fingerprints:

- `model_hash` - SHA-256 hash of the trained `model.pkl`
- `config_hash` - SHA-256 hash of the training `config.json`
- `dataset_merkle_root` - Merkle Root calculated from all CSV dataset rows
- metadata such as model name, version, wallet address, and timestamp

This makes the blockchain an immutable audit log for model versions.

---

## 1. Project Concept

Companies often train many versions of AI models. Later, it can be difficult to prove which exact model, dataset, and configuration were used. Normal databases can be changed by administrators, so they are not ideal for audit evidence.

ChainProof solves this by registering model proofs on a blockchain:

```text
Dataset + Model + Config
        |
        v
SHA-256 Hashes + Merkle Root
        |
        v
Solidity Smart Contract
        |
        v
Blockchain Registry
        |
        v
Frontend Verification
```

During verification, the uploaded files are hashed again. If the new values match the on-chain values, the files are authentic. If even one dataset row or one model byte changes, verification fails.

---

## 2. Current Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Machine Learning | Python, pandas, scikit-learn | Train the health risk classifier |
| Hashing | Python hashlib | Create SHA-256 hashes |
| Dataset Proof | Merkle Tree | Verify dataset integrity efficiently |
| Blockchain | Solidity, Hardhat, ethers.js | Store immutable registry records |
| Blockchain Access | web3.py | Register and read model records from Python |
| Frontend | Streamlit | Dashboard and verification UI |
| Containerization | Docker, Docker Compose | Run the whole demo more easily |

---

## 3. Repository Structure

```text
.
├── backend/
│   ├── train_model.py       # Trains the ML model and writes model.pkl/config.json
│   ├── hash_files.py        # Creates model/config hashes and dataset Merkle Root
│   ├── merkle_tree.py       # Merkle Tree implementation and proof verification
│   ├── register_model.py    # Writes the proof values to the smart contract
│   ├── read_registry.py     # Reads registered records from the smart contract
│   └── verify_row.py        # CLI check for row-level Merkle verification
│
├── contracts/
│   ├── contracts/ModelRegistry.sol  # Main Solidity smart contract
│   ├── scripts/deploy.js            # Deploys the contract and saves deployment JSON
│   ├── test/ModelRegistry.test.js   # Hardhat unit tests
│   ├── hardhat.config.js            # Local/Sepolia network configuration
│   └── package.json                 # Hardhat commands and dependencies
│
├── frontend/
│   ├── app.py       # Streamlit UI
│   ├── audit.py     # Frontend hashing/Merkle verification helpers
│   └── chain.py     # Frontend blockchain read access
│
├── data/
│   ├── health_dataset_1000.csv  # Main dataset
│   └── tampered_dataset.csv     # Manipulated dataset for demo failure
│
├── artifacts/       # Generated outputs: model, hashes, Merkle tree, deployments
├── docs/            # Planning/demo documentation
├── Dockerfile       # Docker image definition
├── docker-compose.yml
├── .env.example     # Example runtime configuration
└── README.md
```

---

## 4. Main Workflow

The normal workflow is:

```text
1. Train model
2. Generate hashes and Merkle Root
3. Start local blockchain
4. Deploy smart contract
5. Register proof values on-chain
6. Open frontend
7. Verify original or tampered files
```

---

## 5. Run Locally Without Docker

### 5.1 Prerequisites

Install:

- Python 3.10 or newer
- Node.js 18 or newer
- npm
- Git

### 5.2 Install Python Dependencies

From the project root:

```bash
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
# .venv\Scripts\activate       # Windows PowerShell

pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

### 5.3 Install Contract Dependencies

```bash
cd contracts
npm install
npm run compile
npm test
cd ..
```

### 5.4 Create `.env`

Copy the example file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
copy .env.example .env
```

For local Hardhat testing, use:

```env
RPC_URL=http://127.0.0.1:8545
PRIVATE_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
```

This private key is the first default Hardhat local test account. It is safe only for local development. Never use it with real funds.

You can also use `.env` to change the model metadata and file paths without editing the Python code. This is useful if you want to register another model, another version, or another dataset.

```env
# Model and dataset metadata used by backend/hash_files.py
CHAINPROOF_MODEL_NAME=Health Risk Classifier
CHAINPROOF_MODEL_VERSION=1.0.0
CHAINPROOF_DATASET_PATH=data/health_dataset_1000.csv
CHAINPROOF_DATASET_NAME=health_dataset_1000.csv

# Generated model/config artifacts
CHAINPROOF_MODEL_PATH=artifacts/model.pkl
CHAINPROOF_CONFIG_PATH=artifacts/config.json

# Output files generated by the hashing/Merkle step
CHAINPROOF_HASHES_PATH=artifacts/hashes.json
CHAINPROOF_MERKLE_PATH=artifacts/dataset_merkle.json

# Example row index used only for printing a Merkle proof demo
CHAINPROOF_EXAMPLE_ROW_INDEX=1
```

For example, to use another dataset/model, change only `.env`:

```env
CHAINPROOF_MODEL_NAME=Loan Risk Classifier
CHAINPROOF_MODEL_VERSION=1.0.0
CHAINPROOF_DATASET_PATH=data/loan_dataset.csv
CHAINPROOF_DATASET_NAME=loan_dataset.csv
```

Then rerun:

```bash
python backend/hash_files.py
python backend/register_model.py
```

So the default demo uses `Health Risk Classifier`, but the registry concept is not limited to healthcare data.

### 5.5 Terminal 1 - Start Local Blockchain

```bash
cd contracts
npm run node
```

Keep this terminal open.

### 5.6 Terminal 2 - Deploy Contract

```bash
cd contracts
npm run deploy:local
cd ..
```

This creates files such as:

```text
artifacts/deployment-localhost.json
artifacts/deployment-latest.json
```

### 5.7 Train, Hash, Register, Read

From the project root:

```bash
python backend/train_model.py
python backend/hash_files.py
python backend/register_model.py
python backend/read_registry.py
```

Expected result: the model proof is registered on the local blockchain and can be read back.

### 5.8 Start Frontend

```bash
streamlit run frontend/app.py
```

Open the URL shown by Streamlit, usually:

```text
http://localhost:8501
```

---

## 6. Run With Docker

Docker is the easiest way to run the demo because it starts the local blockchain, deploys the contract, trains the model, registers the proof, and starts the Streamlit UI.

### 6.1 Build and Run With Docker Compose

```bash
docker compose up --build
```

Then open:

```text
http://localhost:8501
```

The Hardhat RPC is exposed at:

```text
http://localhost:8545
```

### 6.2 Run With Plain Docker

```bash
docker build -t chainproof .
docker run --rm -p 8501:8501 -p 8545:8545 chainproof
```

### 6.3 What the Docker Container Does

The container entrypoint automatically runs:

```text
1. npm install / compile smart contract
2. start Hardhat local node
3. deploy ModelRegistry.sol
4. train the ML model
5. generate hashes and Merkle Root
6. register the proof on-chain
7. start Streamlit frontend
```

This is intended for a local demo. For a real deployment, the blockchain node, backend, and frontend should be separated into different services.

---

## 7. Optional Sepolia Deployment

Sepolia is an Ethereum test network. It is **not required** for the project, but it is useful for a more professional demo.

To use Sepolia, add the following to `.env`:

```env
SEPOLIA_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/YOUR_API_KEY
PRIVATE_KEY=0xYOUR_TEST_WALLET_PRIVATE_KEY
```

Then run:

```bash
cd contracts
npm run deploy:sepolia
cd ..
python backend/register_model.py
python backend/read_registry.py
```

Important:

- Use only a test wallet.
- Never commit `.env`.
- You need Sepolia test ETH.
- The same contract can be deployed locally or on Sepolia.

---

## 8. Smart Contract Summary

The main contract is:

```text
contracts/contracts/ModelRegistry.sol
```

It stores one immutable `ModelRecord` per model version:

```text
recordId
modelName
version
datasetMerkleRoot
modelHash
configHash
registeredBy
timestamp
```

Important functions:

| Function | Purpose |
|---|---|
| `registerModel(...)` | Registers one model version |
| `exists(recordId)` | Checks if a record already exists |
| `getModel(recordId)` | Reads one registration |
| `getModelHistory(modelName)` | Lists all versions of one model |
| `getLatestModel(modelName)` | Returns newest model version |
| `getAllRecordIds()` | Lists all records for the frontend |
| `getTotalRecords()` | Returns registry size |

The contract prevents duplicate `recordId` values, so an old model version cannot be overwritten.

---

## 9. Frontend Usage

The Streamlit app contains four main areas:

1. **Registry Overview** - shows the registered model information.
2. **Dataset Audit** - uploads a CSV and compares its Merkle Root to the registered root.
3. **Model & Config Audit** - uploads `model.pkl` and `config.json` and compares SHA-256 hashes.
4. **On-Chain Status** - shows RPC connection, contract address, chain ID, block number, and registered IDs.

For the tamper demo, use:

```text
data/tampered_dataset.csv
```

The expected result is verification failure.

---

## 10. Team Responsibilities

### Person 1 - Blockchain and Smart Contracts

Responsible for:

- `contracts/contracts/ModelRegistry.sol`
- `contracts/scripts/deploy.js`
- `contracts/hardhat.config.js`
- `contracts/test/ModelRegistry.test.js`
- `backend/register_model.py`
- `backend/read_registry.py`
- `.env.example`

Main goal: prove that hashes and Merkle Roots are stored immutably on-chain and can be read back.

### Person 2 - AI and Backend

Responsible for:

- `backend/train_model.py`
- `backend/hash_files.py`
- `backend/merkle_tree.py`
- `backend/verify_row.py`
- `data/health_dataset_1000.csv`
- generated files in `artifacts/`

Main goal: train a repeatable model, generate correct hashes, generate the dataset Merkle Root, and support tamper detection.

### Person 3 - Frontend, Demo, and Presentation

Responsible for:

- `frontend/app.py`
- `frontend/audit.py`
- `frontend/chain.py`
- UI screenshots
- demo script
- presentation and diagrams

Main goal: make the project understandable and demonstrable for users and supervisors.

---

## 11. Final Demo Script

Recommended live demo:

```text
1. Start app with Docker or local commands.
2. Show blockchain connection in the On-Chain Status tab.
3. Show registered model record.
4. Upload the original dataset and show verification passed.
5. Enable or upload the tampered dataset and show verification failed.
6. Upload original model.pkl and config.json and show hash match.
7. Explain that the blockchain stores only fingerprints, not private data.
8. Explain that any modification changes the hash/root and is detected.
```

---

## 12. Common Problems

### `Contract ABI not found`

Run:

```bash
cd contracts
npm run compile
```

### `Could not connect to RPC endpoint`

Start Hardhat:

```bash
cd contracts
npm run node
```

### `Set PRIVATE_KEY in .env`

Create `.env` and add a local Hardhat private key.

### `record already exists`

This is normal if the same model version was already registered. Change `CHAINPROOF_MODEL_VERSION` in `.env`, rerun `python backend/hash_files.py`, or restart a fresh Hardhat node and redeploy.

### Frontend shows fallback data

The app could not reach the blockchain. Check that:

- Hardhat node is running
- contract is deployed
- `artifacts/deployment-latest.json` exists
- `RPC_URL` is correct

---

## 13. Git Safety

Do not commit:

```text
.env
node_modules/
contracts/node_modules/
contracts/artifacts/
contracts/cache/
.venv/
__pycache__/
```

Commit these:

```text
source code
README.md
Dockerfile
docker-compose.yml
.env.example
scripts/docker-entrypoint.sh
docs/
```

---

## 14. Project Status

The current version is suitable for local end-to-end testing and demonstration:

- ML training exists
- hash generation exists
- Merkle Tree verification exists
- smart contract exists
- Hardhat tests exist
- blockchain registration and readback scripts exist
- Streamlit frontend exists
- Docker support has been added

Remaining optional improvements:

- React frontend instead of Streamlit
- Sepolia public testnet deployment
- CI pipeline for tests
- cleaner backend API separation
- more model versions in the demo
