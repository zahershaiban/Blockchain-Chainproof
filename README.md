# ChainProof - Tamper-Proof AI Model Registry

ChainProof is a blockchain-based audit system for machine-learning models. It verifies whether a trained model, its configuration, and its dataset have been changed after registration.

The project does **not** store datasets or model files on-chain. It stores only:

- SHA-256 hash of `model.pkl`
- SHA-256 hash of `config.json`
- Merkle Root of the dataset
- model name, version, wallet address, and timestamp

---

## Architecture

```text
Health dataset
      |
      v
Python training pipeline
      |
      +--> artifacts/model.pkl
      +--> artifacts/config.json
      |
      v
SHA-256 hashing + Merkle Tree
      |
      +--> model hash
      +--> config hash
      +--> dataset Merkle Root
      |
      v
Python Web3 registration
      |
      v
Solidity ModelRegistry smart contract
      |
      v
Local Hardhat blockchain
      |
      v
Streamlit frontend
      |
      +--> Registry overview
      +--> Dataset verification
      +--> Model/config verification
      +--> On-chain status
```

The blockchain stores only cryptographic proof values and metadata. The original dataset, model, and configuration remain off-chain.

---

## Repository Structure

```text
.
├── backend/
│   ├── train_model.py
│   ├── hash_files.py
│   ├── merkle_tree.py
│   ├── register_model.py
│   ├── read_registry.py
│   └── verify_row.py
├── contracts/
│   ├── contracts/ModelRegistry.sol
│   ├── scripts/deploy.js
│   ├── test/ModelRegistry.test.js
│   ├── hardhat.config.js
│   └── package.json
├── frontend/
│   ├── app.py
│   ├── audit.py
│   └── chain.py
├── data/
│   ├── health_dataset_1000.csv
│   └── tampered_dataset.csv
├── artifacts/
├── scripts/docker-entrypoint.sh
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Run with Docker

Docker is the easiest way to run the complete demo.

### Requirements

- Docker Desktop
- Docker Compose

From the project root:

```bash
docker compose up --build
```

Then open:

```text
http://localhost:8501
```

Do not open `http://0.0.0.0:8501`. That is only the address used by Streamlit inside the container.

To stop the project:

```bash
docker compose down
```

For a completely fresh demo:

```bash
docker compose down -v
docker compose up --build
```

The Docker startup performs the complete workflow:

```text
1. Start the local Hardhat blockchain
2. Compile and deploy the smart contract
3. Train the machine-learning model
4. Generate SHA-256 hashes and the dataset Merkle Root
5. Register the proof values on-chain
6. Read the registered record
7. Start the Streamlit frontend
```

---

## Run Manually

### Requirements

- Python 3.10 or newer
- Node.js 18 or newer
- npm

### 1. Create the Python environment

```bash
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install the dependencies:

```bash
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

### 2. Create `.env`

Linux/macOS:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
copy .env.example .env
```

For the local Hardhat demo, the important values are:

```env
RPC_URL=http://127.0.0.1:8545
PRIVATE_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
```

The private key above belongs to a default Hardhat development account. Never use it with real funds.

### 3. Install and test the smart contract

```bash
cd contracts
npm install
npm run compile
npm test
```

### 4. Start the local blockchain

Keep this terminal open:

```bash
npm run node
```

### 5. Deploy the contract

Open a second terminal from the project root:

```bash
cd contracts
npm run deploy:local
cd ..
```

### 6. Train, hash, register, and read

```bash
python backend/train_model.py
python backend/hash_files.py
python backend/register_model.py
python backend/read_registry.py
```

### 7. Start the frontend

```bash
streamlit run frontend/app.py
```

Open:

```text
http://localhost:8501
```

---

## Demo Flow

1. Open **On-Chain Status** and confirm that the blockchain and contract are connected.
2. Open **Registry Overview** and show the registered model version and proof values.
3. In **Dataset Audit**, upload:

```text
data/health_dataset_1000.csv
```

The verification should pass.

4. Upload:

```text
data/tampered_dataset.csv
```

The verification should fail because the Merkle Root is different.

5. In **Model & Config Audit**, upload:

```text
artifacts/model.pkl
artifacts/config.json
```

The hashes should match the values stored on-chain.

---

## Important Files

`backend/train_model.py` trains the model and creates `artifacts/model.pkl` and `artifacts/config.json`.

`backend/hash_files.py` calculates the model hash, config hash, and dataset Merkle Root.

`backend/register_model.py` registers the proof values in the smart contract.

`contracts/contracts/ModelRegistry.sol` stores immutable model-version records and prevents duplicate record IDs.

`frontend/app.py` provides the Streamlit interface for registry display and verification.

---

## Common Problems

### `env: 'bash\r': No such file or directory`

The file `scripts/docker-entrypoint.sh` has Windows `CRLF` line endings.

Change the file to Unix `LF` line endings and rebuild:

```bash
docker compose down
docker compose build --no-cache
docker compose up
```

### `Could not connect to RPC endpoint`

Start the Hardhat node:

```bash
cd contracts
npm run node
```

### `Contract ABI not found`

Compile the smart contract:

```bash
cd contracts
npm run compile
```

### `record already exists`

The same record ID is already registered. Use a new model version or restart a fresh local blockchain.

### Docker container exits unexpectedly

Check the logs:

```bash
docker compose logs --tail=200
docker compose ps -a
```

Then try a clean rebuild:

```bash
docker compose down -v
docker compose build --no-cache
docker compose up
```

---

## Notes

- The local Hardhat blockchain is used for the project demo.
- Sepolia deployment is optional.
- The blockchain proves integrity after registration; it does not prove that the model is accurate or that the original dataset was correct.
