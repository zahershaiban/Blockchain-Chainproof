"""
Register the current ChainProof hashes on the ModelRegistry smart contract.

Works with:
- local Hardhat network, using RPC_URL and CONTRACT_ADDRESS
- Sepolia Ethereum testnet, using SEPOLIA_RPC_URL/RPC_URL and CONTRACT_ADDRESS
"""

from pathlib import Path
import json
import os
from typing import Any, Dict

from dotenv import load_dotenv
from web3 import Web3

ROOT = Path(__file__).resolve().parents[1]
HASHES_PATH = ROOT / "artifacts" / "hashes.json"
DEPLOYMENT_PATH = ROOT / "artifacts" / "deployment-latest.json"
CONTRACT_ABI_PATH = (
    ROOT
    / "contracts"
    / "artifacts"
    / "contracts"
    / "ModelRegistry.sol"
    / "ModelRegistry.json"
)

load_dotenv(ROOT / ".env")


def load_contract_address() -> str:
    env_address = os.getenv("CONTRACT_ADDRESS")
    if env_address:
        return env_address

    if DEPLOYMENT_PATH.exists():
        deployment = json.loads(DEPLOYMENT_PATH.read_text(encoding="utf-8"))
        if deployment.get("contractAddress"):
            return deployment["contractAddress"]

    raise ValueError("Set CONTRACT_ADDRESS in .env or run the deploy script first.")


def load_hashes() -> Dict[str, Any]:
    if not HASHES_PATH.exists():
        raise FileNotFoundError("artifacts/hashes.json not found. Run backend/hash_files.py first.")
    return json.loads(HASHES_PATH.read_text(encoding="utf-8"))


def load_abi() -> Any:
    if not CONTRACT_ABI_PATH.exists():
        raise FileNotFoundError("Contract ABI not found. Run `npm run compile` inside contracts/ first.")
    contract_json = json.loads(CONTRACT_ABI_PATH.read_text(encoding="utf-8"))
    return contract_json["abi"]


def build_record_id(model_name: str, version: str) -> str:
    safe_name = "".join(ch if ch.isalnum() else "-" for ch in model_name).strip("-")
    return f"{safe_name}-{version}"


def main() -> None:
    rpc_url = os.getenv("RPC_URL") or os.getenv("SEPOLIA_RPC_URL") or "http://127.0.0.1:8545"
    private_key = os.getenv("PRIVATE_KEY")
    contract_address = load_contract_address()

    if not private_key:
        raise ValueError("Set PRIVATE_KEY in .env")

    hashes = load_hashes()
    abi = load_abi()

    model_name = hashes.get("model_name", "Health Risk Classifier")
    version = hashes.get("version", "1.0.0")
    record_id = hashes.get("record_id") or build_record_id(model_name, version)
    dataset_merkle_root = hashes["dataset_merkle_root"]
    model_hash = hashes["model_hash"]
    config_hash = hashes["config_hash"]

    web3 = Web3(Web3.HTTPProvider(rpc_url))
    if not web3.is_connected():
        raise ConnectionError(f"Could not connect to RPC endpoint: {rpc_url}")

    account = web3.eth.account.from_key(private_key)
    contract = web3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=abi)

    if contract.functions.exists(record_id).call():
        print(f"Record already exists on-chain: {record_id}")
        existing = contract.functions.getModel(record_id).call()
        print(json.dumps({
            "recordId": existing[0],
            "modelName": existing[1],
            "version": existing[2],
            "datasetMerkleRoot": existing[3],
            "modelHash": existing[4],
            "configHash": existing[5],
            "registeredBy": existing[6],
            "timestamp": existing[7],
        }, indent=2))
        return

    nonce = web3.eth.get_transaction_count(account.address)
    chain_id = web3.eth.chain_id

    tx = contract.functions.registerModel(
        record_id,
        model_name,
        version,
        dataset_merkle_root,
        model_hash,
        config_hash,
    ).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "chainId": chain_id,
        "gas": 800000,
        "gasPrice": web3.eth.gas_price,
    })

    signed_tx = web3.eth.account.sign_transaction(tx, private_key=private_key)
    raw_tx = getattr(signed_tx, "rawTransaction", None) or signed_tx.raw_transaction
    tx_hash = web3.eth.send_raw_transaction(raw_tx)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

    output = {
        "recordId": record_id,
        "modelName": model_name,
        "version": version,
        "contractAddress": contract_address,
        "transactionHash": receipt.transactionHash.hex(),
        "registeredBy": account.address,
        "blockNumber": receipt.blockNumber,
    }

    (ROOT / "artifacts" / "last-registration.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print("Registered model on-chain:")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
