"""ChainProof: Verbindung und Lesezugriff auf den ModelRegistry-Contract.

Vertrauensanker ist die Chain. Adresse aus deployment-latest.json (oder ENV),
ABI aus dem Hardhat-artifacts-Pfad, RPC aus .env (Default lokaler Hardhat-Node).
"""

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from web3 import Web3

# Projektpfade.
BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"
DEPLOYMENT_PATH = ARTIFACTS_DIR / "deployment-latest.json"
HASHES_PATH = ARTIFACTS_DIR / "hashes.json"
ABI_PATH = (
    BASE_DIR / "contracts" / "artifacts" / "contracts"
    / "ModelRegistry.sol" / "ModelRegistry.json"
)

# .env (falls vorhanden) laden - liefert RPC_URL / CONTRACT_ADDRESS.
load_dotenv(BASE_DIR / ".env")

DEFAULT_RPC = "http://127.0.0.1:8545"

# Reihenfolge der Struct-Felder (ModelRecord) wie vom Contract zurueckgegeben.
RECORD_FIELDS = [
    "recordId", "modelName", "version", "datasetMerkleRoot",
    "modelHash", "configHash", "registeredBy", "timestamp",
]


class ABINotFoundError(Exception):
    """ABI ist nicht kompiliert vorhanden."""


class DeploymentNotFoundError(Exception):
    """deployment-latest.json fehlt und keine ENV-Adresse gesetzt."""


class NodeConnectionError(Exception):
    """RPC-Knoten ist nicht erreichbar."""


def get_rpc_url() -> str:
    return os.getenv("RPC_URL") or os.getenv("SEPOLIA_RPC_URL") or DEFAULT_RPC


def load_deployment() -> dict:
    if not DEPLOYMENT_PATH.exists():
        raise DeploymentNotFoundError(
            "artifacts/deployment-latest.json fehlt. Bitte zuerst den Contract "
            "deployen (in contracts/: npx hardhat run scripts/deploy.js "
            "--network localhost)."
        )
    return json.loads(DEPLOYMENT_PATH.read_text(encoding="utf-8"))


def load_contract_address() -> str:
    env_address = os.getenv("CONTRACT_ADDRESS")
    if env_address:
        return env_address
    return load_deployment()["contractAddress"]


def abi_available() -> bool:
    return ABI_PATH.exists()


def load_abi() -> Any:
    if not ABI_PATH.exists():
        raise ABINotFoundError(
            "Contract-ABI nicht gefunden unter "
            "contracts/artifacts/contracts/ModelRegistry.sol/ModelRegistry.json. "
            "Bitte einmalig kompilieren (in contracts/): "
            "npm install && npx hardhat compile."
        )
    return json.loads(ABI_PATH.read_text(encoding="utf-8"))["abi"]


def connect():
    """Baut Web3-Verbindung + Contract auf. Wirft sprechende Fehler.

    Gibt (web3, contract, address, rpc_url) zurueck.
    """
    rpc_url = get_rpc_url()
    address = load_contract_address()
    abi = load_abi()
    web3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 5}))
    if not web3.is_connected():
        raise NodeConnectionError(
            f"Kein Kontakt zum RPC-Knoten unter {rpc_url}. Laeuft der Hardhat-Node? "
            f"Starten (in contracts/): npx hardhat node"
        )
    contract = web3.eth.contract(address=Web3.to_checksum_address(address), abi=abi)
    return web3, contract, address, rpc_url


def record_to_dict(record: Any) -> dict:
    """Mappt das vom Contract gelieferte Struct-Tupel auf benannte Felder."""
    return {name: record[i] for i, name in enumerate(RECORD_FIELDS)}


def get_latest_model(contract, model_name: str) -> dict:
    """Neueste Registrierung fuer einen Modellnamen (getLatestModel)."""
    return record_to_dict(contract.functions.getLatestModel(model_name).call())


def get_model(contract, record_id: str) -> dict:
    """Eine Registrierung per recordId (getModel)."""
    return record_to_dict(contract.functions.getModel(record_id).call())


def list_records(contract) -> dict:
    """Gesamtzahl und alle recordIds aus der Registry."""
    return {
        "total": contract.functions.getTotalRecords().call(),
        "ids": contract.functions.getAllRecordIds().call(),
    }


def chain_info(web3) -> dict:
    """Basis-Infos zum verbundenen Netzwerk."""
    return {"chainId": web3.eth.chain_id, "blockNumber": web3.eth.block_number}
