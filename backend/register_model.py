"""
Optional script for registering hashes on a local Hardhat blockchain.

Before using:
1. Start Hardhat node.
2. Deploy the contract.
3. Copy the contract address into .env.
"""

# Imports Path to build safe file paths.
from pathlib import Path
# Imports json to read hashes.json and the compiled contract ABI.
import json
# Imports os to read environment variables from .env.
import os
# Imports load_dotenv to load RPC_URL, PRIVATE_KEY, and CONTRACT_ADDRESS from .env.
from dotenv import load_dotenv
# Imports Web3 to connect Python to the local blockchain.
from web3 import Web3

# Finds the main chainproof/ project folder.
ROOT = Path(__file__).resolve().parents[1]
# Points to the metadata file containing dataset/model/config hashes.
HASHES_PATH = ROOT / "artifacts" / "hashes.json"
# Points to the compiled contract JSON file that contains the ABI.
CONTRACT_ABI_PATH = ROOT / "contracts" / "artifacts" / "contracts" / "ModelRegistry.sol" / "ModelRegistry.json"

# Loads environment variables from chainproof/.env.
load_dotenv(ROOT / ".env")

# Reads the blockchain RPC URL, defaulting to a local Hardhat node.
RPC_URL = os.getenv("RPC_URL", "http://127.0.0.1:8545")
# Reads the private key used to sign the registration transaction.
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
# Reads the deployed ModelRegistry contract address.
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")


# Main function that sends the registration transaction to the blockchain.
def main() -> None:
    # Stops if required blockchain credentials are missing.
    if not PRIVATE_KEY or not CONTRACT_ADDRESS:
        # Raises a clear setup error.
        raise ValueError("Set PRIVATE_KEY and CONTRACT_ADDRESS in .env")

    # Loads the generated hashes and metadata from artifacts/hashes.json.
    hashes = json.loads(HASHES_PATH.read_text(encoding="utf-8"))
    # Loads the compiled contract JSON file.
    contract_json = json.loads(CONTRACT_ABI_PATH.read_text(encoding="utf-8"))
    # Extracts the ABI needed to call contract functions.
    abi = contract_json["abi"]

    # Connects Web3 to the configured RPC endpoint.
    web3 = Web3(Web3.HTTPProvider(RPC_URL))
    # Creates an account object from the private key.
    account = web3.eth.account.from_key(PRIVATE_KEY)
    # Creates a contract object for the deployed ModelRegistry contract.
    contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)

    # Gets the account nonce needed for the next transaction.
    nonce = web3.eth.get_transaction_count(account.address)
    # Builds a transaction that calls registerModel on the smart contract.
    tx = contract.functions.registerModel(
        # Record/model identifier sent to the contract.
        "LoanRiskClassifier",
        # Version sent to the contract.
        "1.0.0",
        # Dataset hash value from hashes.json.
        hashes["dataset_hash"],
        # Model file hash from hashes.json.
        hashes["model_hash"],
        # Config file hash from hashes.json.
        hashes["config_hash"],
    ).build_transaction({
        # Sender wallet address.
        "from": account.address,
        # Transaction nonce.
        "nonce": nonce,
        # Gas limit for the transaction.
        "gas": 500000,
        # Current network gas price.
        "gasPrice": web3.eth.gas_price,
    })

    # Signs the transaction locally using the private key.
    signed_tx = web3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    # Sends the signed transaction to the blockchain.
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    # Waits until the transaction is mined.
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    # Prints the final transaction hash.
    print(f"Registered model. Transaction hash: {receipt.transactionHash.hex()}")


# Runs main() only when this file is executed directly.
if __name__ == "__main__":
    # Starts blockchain registration.
    main()
