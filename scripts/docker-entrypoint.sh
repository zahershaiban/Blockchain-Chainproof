#!/usr/bin/env bash
set -euo pipefail

cd /app
mkdir -p artifacts

export RPC_URL="${RPC_URL:-http://127.0.0.1:8545}"
export PRIVATE_KEY="${PRIVATE_KEY:-0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80}"

printf '\n[ChainProof] Compiling smart contract...\n'
cd /app/contracts
npx hardhat compile

printf '\n[ChainProof] Starting local Hardhat node...\n'
npx hardhat node --hostname 0.0.0.0 > /tmp/chainproof-hardhat.log 2>&1 &
HARDHAT_PID=$!
trap 'kill ${HARDHAT_PID} 2>/dev/null || true' EXIT

printf '[ChainProof] Waiting for Hardhat RPC on http://127.0.0.1:8545 ...\n'
for i in $(seq 1 60); do
  if curl -s -X POST \
    -H 'Content-Type: application/json' \
    --data '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}' \
    http://127.0.0.1:8545 >/dev/null; then
    break
  fi
  sleep 1
  if [ "$i" -eq 60 ]; then
    echo "Hardhat node did not start. Log output:"
    cat /tmp/chainproof-hardhat.log
    exit 1
  fi
done

printf '\n[ChainProof] Deploying ModelRegistry locally...\n'
npm run deploy:local

cd /app
printf '\n[ChainProof] Training model...\n'
python backend/train_model.py

printf '\n[ChainProof] Generating hashes and Merkle Root...\n'
python backend/hash_files.py

printf '\n[ChainProof] Registering proof values on-chain...\n'
python backend/register_model.py

printf '\n[ChainProof] Reading registry state...\n'
python backend/read_registry.py

printf '\n[ChainProof] Starting Streamlit frontend on http://0.0.0.0:8501 ...\n'
exec streamlit run frontend/app.py --server.address=0.0.0.0 --server.port=8501
