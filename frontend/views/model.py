"""Tab 3: Modell- & Config-Audit — SHA-256-Abgleich von model.pkl und config.json."""

import streamlit as st

import app_state
import audit
from ui import components as ui
from ui import format as fmt


def _file_check(state: dict, label: str, file, expected: str):
    """Gemeinsamer Ablauf für model.pkl / config.json. Gibt Status oder None."""
    if file is None:
        ui.empty_state(f"Noch keine Datei für {label} hochgeladen.")
        return None
    ui.file_summary(file.name, file.size)
    try:
        computed = audit.sha256_bytes(file.getvalue())
    except audit.AuditError as exc:
        st.error(str(exc))
        return None
    return ui.hash_compare_card(label, expected, computed, state["source"])


def render(state: dict) -> None:
    st.header("Modell- & Config-Audit (SHA-256)")
    st.write(
        "Lade `model.pkl` und `config.json` hoch. Die SHA-256-Hashes werden neu "
        "berechnet und gegen die registrierten Werte verglichen."
    )

    st.subheader("model_hash")
    model_file = st.file_uploader("model.pkl hochladen", type=None, key="model")
    status = _file_check(
        state, "model_hash", model_file, app_state.expected_value(state, "model_hash")
    )
    if status == fmt.VERIFIED:
        st.caption("model.pkl ist unverändert.")
    elif status == fmt.MISMATCH:
        st.caption("model.pkl weicht vom registrierten Hash ab.")
    elif status == fmt.UNVERIFIED:
        st.caption(
            "Abgleich nur gegen lokalen Fallback-Wert möglich — nicht on-chain "
            "bestätigt."
        )

    st.divider()

    st.subheader("config_hash")
    config_file = st.file_uploader(
        "config.json hochladen", type=["json"], key="config"
    )
    status = _file_check(
        state,
        "config_hash",
        config_file,
        app_state.expected_value(state, "config_hash"),
    )
    if status == fmt.VERIFIED:
        st.caption("config.json ist unverändert.")
    elif status == fmt.MISMATCH:
        st.caption("config.json weicht vom registrierten Hash ab.")
        # Konditionaler Hinweis auf die bekannte Backend-Inkonsistenz.
        # Das Ergebnis wird NICHT verfälscht — nur erklärt.
        st.warning(
            "Hinweis (bekannte mögliche Inkonsistenz): Falls die hochgeladene "
            "config.json korrekt ist, kann der on-chain registrierte config_hash "
            "aus einem veralteten Build stammen. Abhilfe im Backend: "
            "hash_files.py erneut ausführen und das Modell neu registrieren. "
            "Das angezeigte Prüfergebnis bleibt unverändert ehrlich."
        )
    elif status == fmt.UNVERIFIED:
        st.caption(
            "Abgleich nur gegen lokalen Fallback-Wert möglich — nicht on-chain "
            "bestätigt."
        )
