# Imports csv so uploaded CSV files can be read row by row.
import csv
# Imports json so saved model metadata can be loaded from hashes.json.
import json
# Imports sys so the backend folder can be added to the Python import path.
import sys
# Imports Path to build file paths that work across operating systems.
from pathlib import Path

# Imports Streamlit to build the web user interface.
import streamlit as st


# Finds the main chainproof/ project folder by going one level above frontend/.
BASE_DIR = Path(__file__).resolve().parent.parent
# Points to the backend folder where merkle_tree.py is stored.
BACKEND_DIR = BASE_DIR / "backend"
# Points to the artifacts folder where hashes.json is stored.
ARTIFACTS_DIR = BASE_DIR / "artifacts"

# Adds backend/ to Python's import path so this frontend can import merkle_tree.py.
sys.path.append(str(BACKEND_DIR))

# Imports Merkle proof creation and verification functions.
from merkle_tree import (
    # Generates the proof for a selected uploaded row.
    generate_merkle_proof,
    # Checks whether the row proof reconstructs the trusted Merkle Root.
    verify_merkle_proof
)


# Sets Streamlit browser tab title and page layout.
st.set_page_config(page_title="ChainProof", layout="centered")

# Shows the main app title.
st.title("ChainProof")
# Shows a short description under the title.
st.subheader("Tamper-proof AI Model Registry with Merkle Tree Verification")

# Defines the path to the saved hash metadata.
hashes_path = ARTIFACTS_DIR / "hashes.json"

# Checks whether hashes.json exists before starting the verification UI.
if not hashes_path.exists():
    # Tells the user which backend scripts must run first.
    st.warning("Run backend/train_model.py and backend/hash_files.py first.")
    # Stops the Streamlit app because trusted hashes are missing.
    st.stop()

# Opens hashes.json for reading.
with open(hashes_path, "r", encoding="utf-8") as file:
    # Loads the saved model metadata and trusted dataset Merkle Root.
    hashes = json.load(file)

# Shows a section title for the metadata.
st.header("Registered Model Metadata")

# Displays the metadata JSON in the UI.
st.json(hashes)


# Optional blockchain deployment information for the presentation demo.
deployment_path = ARTIFACTS_DIR / "deployment-latest.json"
registration_path = ARTIFACTS_DIR / "last-registration.json"

st.header("Blockchain Registry Status")

if deployment_path.exists():
    with open(deployment_path, "r", encoding="utf-8") as file:
        deployment = json.load(file)
    st.write("Deployment information:")
    st.json(deployment)
    if deployment.get("explorerUrl"):
        st.link_button("Open contract on explorer", deployment["explorerUrl"])
else:
    st.info("No blockchain deployment file found yet. Run the Hardhat deployment script first.")

if registration_path.exists():
    with open(registration_path, "r", encoding="utf-8") as file:
        registration = json.load(file)
    st.write("Last on-chain registration:")
    st.json(registration)
else:
    st.info("No on-chain registration file found yet. Run backend/register_model.py first.")

# Shows a section title for row verification.
st.header("Verify One Dataset Row")

# Creates a file uploader for the auditor to upload a CSV dataset.
uploaded_dataset = st.file_uploader("Upload dataset.csv", type=["csv"])

# Creates a numeric input for choosing which row index to verify.
row_index = st.number_input(
    # Label shown above the number input.
    "Row index to verify",
    # Prevents negative row indexes.
    min_value=0,
    # Default row index; 1 is the first data row if row 0 is the header.
    value=1,
    # Changes the number by one when clicking plus/minus.
    step=1
)

# Runs verification only after the auditor uploads a CSV file.
if uploaded_dataset is not None:
    # Reads the uploaded file bytes, decodes them into text, and splits into lines.
    decoded = uploaded_dataset.getvalue().decode("utf-8").splitlines()
    # Creates a CSV reader from the uploaded lines.
    reader = csv.reader(decoded)
    # Converts every uploaded CSV row into a comma-separated string.
    rows = [",".join(row) for row in reader]

    # Checks whether the selected row index exists in the uploaded file.
    if row_index >= len(rows):
        # Shows an error when the auditor selected a row outside the dataset.
        st.error("Row index is outside the dataset.")
    else:
        # Gets the selected row from the uploaded dataset.
        selected_row = rows[row_index]
        # Generates a Merkle proof for the selected uploaded row.
        proof = generate_merkle_proof(rows, row_index)

        # Verifies the row against the trusted Merkle Root stored in hashes.json.
        is_valid = verify_merkle_proof(
            # Row content being verified.
            selected_row,
            # Proof generated for this row.
            proof,
            # Trusted Merkle Root from the original registered dataset.
            hashes["dataset_merkle_root"]
        )

        # Labels the selected row output.
        st.write("Selected row:")
        # Displays the selected row in a code-style block.
        st.code(selected_row)

        # Labels the generated proof output.
        st.write("Generated Merkle Proof:")
        # Displays the proof as JSON.
        st.json(proof)

        # Checks whether verification succeeded.
        if is_valid:
            # Shows success if the uploaded row matches the registered dataset root.
            st.success("Verified: this row belongs to the original dataset.")
        else:
            # Shows failure if the row or dataset was changed.
            st.error("Verification failed: this row or dataset was changed.")
