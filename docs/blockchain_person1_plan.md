# Person 1 – Blockchain Work Added

This document lists the blockchain improvements added for the final ChainProof phase.

## Added priorities

### 1. Safer immutable registration
The smart contract now prevents overwriting an existing record ID. Every registration is immutable, so a new model version must use a new `recordId`.

### 2. Required-field validation
`registerModel()` now checks that important values are not empty:

- `recordId`
- `modelName`
- `version`
- `datasetMerkleRoot`
- `modelHash`
- `configHash`

### 3. Version history
The contract now stores a list of versions for every model name.

Useful functions:

- `getModelHistory(modelName)`
- `getVersionCount(modelName)`
- `getLatestModel(modelName)`
- `getAllRecordIds()`
- `getTotalRecords()`

### 4. Sepolia deployment support
Hardhat now supports:

```bash
npm run deploy:sepolia
```

Sepolia is an Ethereum testnet. It gives a real blockchain deployment without using real ETH.

### 5. Deployment output
Deployment now writes:

```text
artifacts/deployment-latest.json
artifacts/deployment-<network>.json
```

These files include:

- network
- contract address
- deployer address
- deployment transaction hash
- explorer URL for Sepolia

### 6. Python registration fixed
`backend/register_model.py` now matches the updated smart contract and correctly registers:

- record ID
- model name
- version
- dataset Merkle root
- model hash
- config hash

### 7. Registry reader script
`backend/read_registry.py` was added to read blockchain records and model history.

## Demo commands

### Local blockchain

Terminal 1:

```bash
cd contracts
npm install
npm run compile
npm run node
```

Terminal 2:

```bash
cd contracts
npm run deploy:local
```

Project root:

```bash
cp .env.example .env
# Fill PRIVATE_KEY and CONTRACT_ADDRESS if needed.
python backend/hash_files.py
python backend/register_model.py
python backend/read_registry.py
```

### Sepolia

```bash
cp .env.example .env
# Fill SEPOLIA_RPC_URL and PRIVATE_KEY
cd contracts
npm install
npm run compile
npm run deploy:sepolia
cd ..
python backend/register_model.py
python backend/read_registry.py
```

## What to show in the presentation

1. The smart contract stores only hashes and Merkle roots, not private data.
2. A model registration cannot be overwritten.
3. Every model version gets a separate record ID.
4. `getModelHistory()` shows the audit trail.
5. Sepolia deployment proves the project can run on the Ethereum ecosystem.
