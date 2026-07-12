"""ChainProof — Audit-Frontend (Streamlit).

Schlanker Kompositions-Layer: Theme injizieren, Zustand laden, Statusbalken,
Sidebar-Kontext, Tabs an die Views delegieren. Die Prüflogik lebt unverändert
in audit.py (+ audit_ext.py für Anzeige), der Chain-Zugriff in chain.py
(+ app_state.py für Caching).
"""

import sys
from pathlib import Path

import streamlit as st

# Eigenes Verzeichnis in den Importpfad legen (wie bisher), damit die
# Schwester-Module (app_state, ui, views) unabhängig vom CWD laden.
sys.path.append(str(Path(__file__).resolve().parent))

import app_state  # noqa: E402
from ui import components as ui  # noqa: E402
from ui import format as fmt  # noqa: E402
from ui import theme  # noqa: E402
from views import chain_status, dataset, model, overview  # noqa: E402

st.set_page_config(page_title="ChainProof", layout="wide")
theme.inject()

st.title("ChainProof")
st.caption("Tamper-proof AI Model Registry — On-Chain-Audit der drei Beweise")

with st.spinner("Verbinde mit der Chain…"):
    STATE = app_state.load_state()

ui.status_bar(STATE)

with st.sidebar:
    st.subheader("Prüfkontext")
    record = STATE.get("record") or {}
    ui.sidebar_kv("Modell", STATE["model_name"])
    ui.sidebar_kv(
        "Version",
        record.get("version") or STATE["hashes_local"].get("version", "—"),
    )
    ui.sidebar_kv("Record-ID", STATE["record_id"] or "—")
    ui.sidebar_kv(
        "Contract",
        fmt.truncate_middle(
            STATE["address"]
            or STATE["deployment_local"].get("contractAddress", "")
            or "—",
            10,
            8,
        ),
    )
    ui.sidebar_kv("Netzwerk", STATE["deployment_local"].get("network", "—"))
    ui.sidebar_kv("RPC", STATE["rpc"])
    if st.button("Neu laden", use_container_width=True):
        app_state.refresh()

tab_overview, tab_dataset, tab_model, tab_status = st.tabs(
    ["Registry-Übersicht", "Dataset-Audit", "Modell- & Config-Audit", "On-Chain-Status"]
)
with tab_overview:
    overview.render(STATE)
with tab_dataset:
    dataset.render(STATE)
with tab_model:
    model.render(STATE)
with tab_status:
    chain_status.render(STATE)
