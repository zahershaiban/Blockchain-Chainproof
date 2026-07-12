"""Tab 1: Registry-Übersicht — was ist on-chain registriert?"""

import streamlit as st

from ui import components as ui
from ui import format as fmt


def render(state: dict) -> None:
    st.header("Registry-Übersicht")
    record = state.get("record")
    hashes_local = state["hashes_local"]

    if record:
        col1, col2, col3 = st.columns(3)
        col1.metric("Modell", record["modelName"])
        col2.metric("Version", record["version"])
        col3.metric("Record-ID", record["recordId"])

        st.subheader("Registrierung")
        st.dataframe(
            [
                {"Feld": "Registriert von", "Wert": record["registeredBy"]},
                {
                    "Feld": "Zeitstempel",
                    "Wert": fmt.format_timestamp(record["timestamp"]),
                },
                {"Feld": "Datensatz", "Wert": hashes_local.get("dataset_name", "—")},
            ],
            hide_index=True,
            use_container_width=True,
        )

        st.subheader("On-chain registrierte Beweise")
        ui.proof_list(
            [
                ("dataset_merkle_root", record["datasetMerkleRoot"]),
                ("model_hash", record["modelHash"]),
                ("config_hash", record["configHash"]),
            ],
            source="chain",
        )
    elif state["source"] == "fallback":
        st.markdown(
            ui.status_badge(fmt.UNVERIFIED)
            + " Anzeige aus lokaler hashes.json — nicht on-chain bestätigt.",
            unsafe_allow_html=True,
        )
        col1, col2 = st.columns(2)
        col1.metric("Modell", hashes_local.get("model_name", "—"))
        col2.metric("Version", hashes_local.get("version", "—"))
        st.subheader("Beweise (lokal, ungeprüft)")
        ui.proof_list(
            [
                ("dataset_merkle_root", hashes_local.get("dataset_merkle_root", "")),
                ("model_hash", hashes_local.get("model_hash", "")),
                ("config_hash", hashes_local.get("config_hash", "")),
            ],
            source="fallback",
        )
    else:
        ui.empty_state("Keine Registrierungsdaten verfügbar.")
