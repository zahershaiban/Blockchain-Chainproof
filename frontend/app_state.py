"""Zentraler App-Zustand: gecachte Chain-Verbindung und gecachte Datei-Reads.

Die Semantik von load_state() entspricht dem bisherigen app.py: Chain zuerst;
bei JEDEM Fehler kontrollierter Fallback auf artifacts/hashes.json mit
source == 'fallback' und sichtbar bleibender Fehlermeldung. Fehler beim
Verbinden werden von Streamlit NICHT gecacht — ein Rerun versucht es erneut.
"""

import json
from pathlib import Path

import streamlit as st

import chain

BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"
DATA_DIR = BASE_DIR / "data"
TAMPERED_PATH = DATA_DIR / "tampered_dataset.csv"


@st.cache_data(ttl=10, show_spinner=False)
def read_json(path_str: str) -> dict:
    """Liest eine JSON-Datei tolerant; gibt {} bei Fehler/Fehlen zurück."""
    try:
        return json.loads(Path(path_str).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


@st.cache_resource(ttl=30, show_spinner=False)
def get_connection():
    """Web3 + Contract, über Reruns hinweg wiederverwendet.

    Kein Neuverbinden bei jeder Widget-Interaktion; TTL 30 s, damit ein
    neu gestarteter Node zeitnah erkannt wird. 'Neu laden' leert den Cache.
    """
    return chain.connect()


@st.cache_data(ttl=10, show_spinner=False)
def get_latest_record(model_name: str) -> dict:
    """Neueste Registrierung, kurz gecacht (Registry ist append-only)."""
    _, contract, _, _ = get_connection()
    return chain.get_latest_model(contract, model_name)


def load_state() -> dict:
    """Wie bisheriges load_state(), plus Kontextfelder für Sidebar und Views."""
    last_reg = read_json(str(ARTIFACTS_DIR / "last-registration.json"))
    hashes_local = read_json(str(ARTIFACTS_DIR / "hashes.json"))
    deployment_local = read_json(str(ARTIFACTS_DIR / "deployment-latest.json"))

    model_name = (
        last_reg.get("modelName")
        or hashes_local.get("model_name")
        or "Health Risk Classifier"
    )
    record_id = last_reg.get("recordId") or hashes_local.get("record_id")

    state = {
        "connected": False,
        "abi_available": chain.abi_available(),
        "address": None,
        "rpc": chain.get_rpc_url(),
        "expected": None,
        "source": "chain",
        "error": None,
        "web3": None,
        "contract": None,
        "record": None,
        "model_name": model_name,
        "record_id": record_id,
        "last_reg": last_reg,
        "hashes_local": hashes_local,
        "deployment_local": deployment_local,
    }
    try:
        web3, contract, address, rpc = get_connection()
        record = get_latest_record(model_name)
        state.update(
            connected=True,
            address=address,
            rpc=rpc,
            web3=web3,
            contract=contract,
            record=record,
            expected={
                "dataset_merkle_root": record["datasetMerkleRoot"],
                "model_hash": record["modelHash"],
                "config_hash": record["configHash"],
            },
            source="chain",
        )
    except Exception as exc:  # bewusst breit: jede Störung -> Fallback
        state["error"] = str(exc)
        if hashes_local:
            state["expected"] = {
                "dataset_merkle_root": hashes_local.get("dataset_merkle_root"),
                "model_hash": hashes_local.get("model_hash"),
                "config_hash": hashes_local.get("config_hash"),
            }
            state["source"] = "fallback"
    return state


def expected_value(state: dict, key: str) -> str:
    """Erwarteten Wert (on-chain oder Fallback) für einen Beweis lesen."""
    return (state["expected"] or {}).get(key) or ""


def refresh() -> None:
    """Alle Caches leeren und die App neu ausführen ('Neu laden')."""
    st.cache_data.clear()
    st.cache_resource.clear()
    st.rerun()
