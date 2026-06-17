"""Read ChainProof registry records from the deployed ModelRegistry smart contract."""

from pathlib import Path
import json
import os
from typing import Any

from dotenv import load_dotenv
from web3 import Web3

ROOT = Path(__file__).resolve().parents[1]
DEPLOYMENT_PATH = ROOT / "artifacts" / "deployment-latest.json"
CONTRACT_ABI_PATH = ROOT / "contracts" / "artifacts" / "contracts" / "ModelRegistry.sol" / "ModelRegistry.json"
HASHES_PATH = ROOT / "artifacts" / "hashes.json"

load_dotenv(ROOT / ".env")


def load_contract_address() -> str:
    if os.getenv("CONTRACT_ADDRESS"):
        return os.getenv("CONTRACT_ADDRESS")
    if DEPLOYMENT_PATH.exists():
        return json.loads(DEPLOYMENT_PATH.read_text(encoding="utf-8"))["contractAddress"]
    raise ValueError("Set CONTRACT_ADDRESS or deploy the contract first.")


def load_abi() -> Any:
    return json.loads(CONTRACT_ABI_PATH.read_text(encoding="utf-8"))["abi"]


def record_to_dict(record: Any) -> dict:
    return {
        "recordId": record[0],
        "modelName": record[1],
        "version": record[2],
        "datasetMerkleRoot": record[3],
        "modelHash": record[4],
        "configHash": record[5],
        "registeredBy": record[6],
        "timestamp": record[7],
    }


def main() -> None:
    rpc_url = os.getenv("RPC_URL") or os.getenv("SEPOLIA_RPC_URL") or "http://127.0.0.1:8545"
    contract_address = load_contract_address()

    web3 = Web3(Web3.HTTPProvider(rpc_url))
    if not web3.is_connected():
        raise ConnectionError(f"Could not connect to RPC endpoint: {rpc_url}")

    contract = web3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=load_abi())

    hashes = json.loads(HASHES_PATH.read_text(encoding="utf-8")) if HASHES_PATH.exists() else {}
    model_name = hashes.get("model_name", "Health Risk Classifier")

    total = contract.functions.getTotalRecords().call()
    ids = contract.functions.getAllRecordIds().call()
    history = contract.functions.getModelHistory(model_name).call()

    print(json.dumps({
        "contractAddress": contract_address,
        "totalRecords": total,
        "allRecordIds": ids,
        "historyForCurrentModel": history,
        "records": [record_to_dict(contract.functions.getModel(record_id).call()) for record_id in ids],
    }, indent=2))


if __name__ == "__main__":
    main()
