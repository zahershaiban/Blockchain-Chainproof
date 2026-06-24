"""ChainProof - Audit-Frontend (Streamlit).

Vollstaendiges Audit aller drei on-chain registrierten Beweise eines ML-Modells:
- dataset_merkle_root (Merkle-Root ueber die CSV-Zeilen, Kopfzeile = Blatt 0)
- model_hash          (SHA-256 von model.pkl)
- config_hash         (SHA-256 von config.json)

Vertrauensanker ist die Chain (web3.py -> ModelRegistry). Lokale hashes.json dient
nur als deutlich gekennzeichneter Fallback, wenn die Chain nicht erreichbar ist.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

# Eigenes Verzeichnis in den Importpfad legen, damit chain.py/audit.py laden.
sys.path.append(str(Path(__file__).resolve().parent))

import audit  # noqa: E402
import chain  # noqa: E402

BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"
DATA_DIR = BASE_DIR / "data"
TAMPERED_PATH = DATA_DIR / "tampered_dataset.csv"

st.set_page_config(page_title="ChainProof", layout="wide")


# --------------------------------------------------------------------------- #
# Hilfsfunktionen
# --------------------------------------------------------------------------- #
def read_json(path: Path) -> dict:
    """Liest eine JSON-Datei tolerant; gibt {} bei Fehler/Fehlen zurueck."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def fmt_timestamp(ts) -> str:
    """Unix-Sekunden lesbar formatieren."""
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )
    except (ValueError, TypeError, OSError):
        return str(ts)


def hashes_match(expected: str, computed: str) -> bool:
    """Vergleicht zwei Hex-Hashes case-insensitiv."""
    return bool(expected) and bool(computed) and expected.lower() == computed.lower()


def render_proof_result(label: str, expected: str, computed: str):
    """Zeigt erwarteten Wert, berechneten Wert und Status fuer einen Beweis."""
    match = hashes_match(expected, computed)
    st.markdown(f"**{label}** — {'✅ uebereinstimmend' if match else '❌ abweichend'}")

    left, right = st.columns(2)

    with left:
        st.caption("Erwartet (on-chain / Fallback)")
        st.code(expected or "(nicht verfuegbar)", language="text")

    with right:
        st.caption("Neu berechnet")
        st.code(computed or "(nicht verfuegbar)", language="text")

    return match


# Lookup-Schluessel (reine Schluessel, KEINE Vertrauenswerte): aus lokalen Dateien.
LAST_REG = read_json(ARTIFACTS_DIR / "last-registration.json")
HASHES_LOCAL = read_json(ARTIFACTS_DIR / "hashes.json")
DEPLOYMENT_LOCAL = read_json(ARTIFACTS_DIR / "deployment-latest.json")

MODEL_NAME = (
        LAST_REG.get("modelName")
        or HASHES_LOCAL.get("model_name")
        or "Health Risk Classifier"
)

RECORD_ID = LAST_REG.get("recordId") or HASHES_LOCAL.get("record_id")


def load_state() -> dict:
    """Verbindet zur Chain und liest die neueste Registrierung.

    Faellt bei jedem Fehler kontrolliert auf die lokale hashes.json zurueck und
    markiert das deutlich (source == 'fallback').
    """
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
    }

    try:
        web3, contract, address, rpc = chain.connect()
        record = chain.get_latest_model(contract, MODEL_NAME)

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

    except Exception as exc:  # bewusst breit: jede Stoerung -> Fallback
        state["error"] = str(exc)

        if HASHES_LOCAL:
            state["expected"] = {
                "dataset_merkle_root": HASHES_LOCAL.get("dataset_merkle_root"),
                "model_hash": HASHES_LOCAL.get("model_hash"),
                "config_hash": HASHES_LOCAL.get("config_hash"),
            }
            state["source"] = "fallback"

    return state


STATE = load_state()
EXPECTED = STATE["expected"] or {}


def expected_value(key: str) -> str:
    return (EXPECTED or {}).get(key) or ""


# --------------------------------------------------------------------------- #
# Kopfbereich + globaler Verbindungsstatus
# --------------------------------------------------------------------------- #
st.title("ChainProof")
st.caption("Tamper-proof AI Model Registry — On-Chain-Audit der drei Beweise")

if STATE["source"] == "chain":
    st.success(
        f"Mit Chain verbunden ({STATE['rpc']}) — Vertrauensanker ist der Contract "
        f"{STATE['address']}. Erwartete Werte werden on-chain gelesen."
    )
else:
    st.error("Keine Chain-Verbindung. " + (STATE["error"] or ""))

    if STATE["source"] == "fallback":
        st.warning(
            "⚠️ FALLBACK aktiv: Erwartete Werte stammen aus der lokalen "
            "artifacts/hashes.json und sind NICHT on-chain verifiziert. Fuer ein "
            "echtes Audit den Hardhat-Node starten und ggf. die ABI kompilieren."
        )
    else:
        st.warning(
            "Auch kein lokaler Fallback (hashes.json) verfuegbar — es koennen keine "
            "erwarteten Werte angezeigt werden."
        )


tab_overview, tab_dataset, tab_model, tab_status = st.tabs(
    [
        "Registry-Uebersicht",
        "Dataset-Audit",
        "Modell- & Config-Audit",
        "On-Chain-Status",
    ]
)


# --------------------------------------------------------------------------- #
# Tab 1: Registry-Uebersicht
# --------------------------------------------------------------------------- #
with tab_overview:
    st.header("Registry-Uebersicht")
    record = STATE.get("record")

    if record:
        col1, col2, col3 = st.columns(3)
        col1.metric("Modell", record["modelName"])
        col2.metric("Version", record["version"])
        col3.metric("Record-ID", record["recordId"])

        st.subheader("Registrierung")
        meta_rows = [
            {"Feld": "Registriert von", "Wert": record["registeredBy"]},
            {"Feld": "Zeitstempel", "Wert": fmt_timestamp(record["timestamp"])},
            {"Feld": "Datensatz", "Wert": HASHES_LOCAL.get("dataset_name", "—")},
        ]
        st.dataframe(meta_rows, hide_index=True, use_container_width=True)

        st.subheader("On-chain registrierte Beweise")
        proof_rows = [
            {"Beweis": "dataset_merkle_root", "Wert": record["datasetMerkleRoot"]},
            {"Beweis": "model_hash", "Wert": record["modelHash"]},
            {"Beweis": "config_hash", "Wert": record["configHash"]},
        ]
        st.dataframe(proof_rows, hide_index=True, use_container_width=True)

    elif STATE["source"] == "fallback":
        st.warning(
            "⚠️ FALLBACK: Anzeige aus lokaler hashes.json (nicht on-chain bestaetigt)."
        )

        col1, col2 = st.columns(2)
        col1.metric("Modell", HASHES_LOCAL.get("model_name", "—"))
        col2.metric("Version", HASHES_LOCAL.get("version", "—"))

        st.subheader("Beweise (lokal, ungeprueft)")
        st.dataframe(
            [
                {
                    "Beweis": "dataset_merkle_root",
                    "Wert": HASHES_LOCAL.get("dataset_merkle_root", "—"),
                },
                {
                    "Beweis": "model_hash",
                    "Wert": HASHES_LOCAL.get("model_hash", "—"),
                },
                {
                    "Beweis": "config_hash",
                    "Wert": HASHES_LOCAL.get("config_hash", "—"),
                },
            ],
            hide_index=True,
            use_container_width=True,
        )

    else:
        st.info("Keine Registrierungsdaten verfuegbar.")


# --------------------------------------------------------------------------- #
# Tab 2: Dataset-Audit
# --------------------------------------------------------------------------- #
with tab_dataset:
    st.header("Dataset-Audit (Merkle-Root)")
    st.write(
        "Lade die registrierte CSV oder eine manipulierte CSV hoch. Der Merkle-Root "
        "wird neu berechnet und gegen den registrierten Root verglichen. "
        "Die Kopfzeile ist Blatt 0, Zeile 1 ist der erste Datensatz."
    )

    expected_root = expected_value("dataset_merkle_root")

    use_tamper = st.toggle(
        "Tamper-Demo: manipulierte Datei (data/tampered_dataset.csv) verwenden"
    )

    uploaded = st.file_uploader("Dataset-CSV hochladen", type=["csv"], key="ds")

    data = None
    source_label = None

    if use_tamper:
        if TAMPERED_PATH.exists():
            data = TAMPERED_PATH.read_bytes()
            source_label = "data/tampered_dataset.csv (Tamper-Demo)"
        else:
            st.error("data/tampered_dataset.csv nicht gefunden.")

    elif uploaded is not None:
        data = uploaded.getvalue()
        source_label = uploaded.name

    if data is not None:
        st.caption(f"Geprueft wird: {source_label}")

        try:
            rows = audit.load_csv_rows_from_bytes(data)
        except audit.AuditError as exc:
            st.error(str(exc))
            rows = None

        if rows is not None:
            # Sanity-Check zuerst (erklaert WARUM, statt nur 'fehlgeschlagen').
            ok, messages = audit.sanity_check(rows)

            if not ok:
                for msg in messages:
                    st.warning(msg)

            # ---------------------------------------------------------------- #
            # Ganzdatei-Abgleich
            # ---------------------------------------------------------------- #
            st.subheader("Ganzdatei-Abgleich")

            computed_root = audit.get_merkle_root(rows)
            render_proof_result("dataset_merkle_root", expected_root, computed_root)

            whole_dataset_matches = hashes_match(expected_root, computed_root)

            if whole_dataset_matches:
                st.success("Der komplette Datensatz entspricht dem registrierten Root.")
            else:
                st.error("Der Datensatz weicht vom registrierten Root ab.")

            # ---------------------------------------------------------------- #
            # Welche Zeilen weichen ab?
            # ---------------------------------------------------------------- #
            registered = audit.load_registered_leaves(expected_root)

            if registered is not None:
                leaves, _ = registered
                diffs = audit.diff_rows_against_leaves(rows, leaves)

                if diffs:
                    st.error(f"{len(diffs)} abweichende Zeile(n) gefunden:")

                    st.dataframe(
                        [
                            {
                                "Zeilenindex": d["index"],
                                "patient_id": d["patient_id"],
                                "Status": "geaendert/fehlt",
                            }
                            for d in diffs
                        ],
                        hide_index=True,
                        use_container_width=True,
                    )
                else:
                    st.info("Zeilenweiser Abgleich: keine Abweichungen.")

            else:
                st.caption(
                    "Zeilenweiser Abgleich nicht moeglich "
                    "(dataset_merkle.json fehlt oder ist nicht mit dem "
                    "registrierten Root konsistent)."
                )

            # ---------------------------------------------------------------- #
            # Einzelzeilen-Verifikation mit Merkle-Proof
            #
            # Wichtig:
            # Der Proof wird aus dem registrierten/originalen Merkle Tree geladen,
            # nicht aus dem hochgeladenen Datensatz. Dadurch kann eine einzelne
            # unveraenderte Zeile auch dann erfolgreich sein, wenn eine andere
            # Zeile im hochgeladenen Datensatz manipuliert wurde.
            # ---------------------------------------------------------------- #
            st.subheader("Einzelzeilen-Verifikation (Merkle-Proof)")

            st.info(
                "Diese Pruefung verwendet die ausgewaehlte Zeile aus der "
                "hochgeladenen Datei, aber den Merkle-Proof aus dem registrierten "
                "Original-Merkle-Tree (`artifacts/dataset_merkle.json`)."
            )

            max_index = len(rows) - 1

            row_index = st.number_input(
                "Zu pruefender Zeilenindex (0 = Kopfzeile)",
                min_value=0,
                max_value=max_index,
                value=min(1, max_index),
                step=1,
            )

            try:
                (
                    row,
                    proof,
                    is_valid,
                    uploaded_leaf,
                    registered_leaf,
                ) = audit.verify_uploaded_row_against_registered_tree(
                    rows,
                    int(row_index),
                    expected_root,
                )

                patient_id = row.split(",")[0]

                st.caption(f"Ausgewaehlte Zeile (patient_id: {patient_id})")
                st.code(row, language="text")

                left, right = st.columns(2)

                with left:
                    st.caption("Hash der hochgeladenen Zeile")
                    st.code(uploaded_leaf, language="text")

                with right:
                    st.caption("Registrierter Zeilen-Hash")
                    st.code(registered_leaf, language="text")

                if is_valid:
                    st.success(
                        "Verifiziert: diese konkrete Zeile stimmt mit dem "
                        "registrierten Originaldatensatz ueberein."
                    )

                    if not whole_dataset_matches:
                        st.info(
                            "Hinweis: Der komplette Datensatz weicht ab, aber diese "
                            "einzelne ausgewaehlte Zeile ist unveraendert. "
                            "Die tatsaechlich abweichende Zeile steht oben in der "
                            "Abweichungstabelle."
                        )
                else:
                    st.error(
                        "Verifikation fehlgeschlagen: diese konkrete Zeile stimmt "
                        "nicht mit dem registrierten Originaldatensatz ueberein."
                    )

                with st.expander("Merkle-Proof anzeigen"):
                    st.json(proof)

            except audit.AuditError as exc:
                st.error(str(exc))

    else:
        st.info("Bitte eine CSV hochladen oder die Tamper-Demo aktivieren.")


# --------------------------------------------------------------------------- #
# Tab 3: Modell- & Config-Audit
# --------------------------------------------------------------------------- #
with tab_model:
    st.header("Modell- & Config-Audit (SHA-256)")
    st.write(
        "Lade `model.pkl` und `config.json` hoch. Die SHA-256-Hashes werden neu "
        "berechnet und gegen die registrierten Werte verglichen."
    )

    expected_model = expected_value("model_hash")
    expected_config = expected_value("config_hash")

    st.subheader("model_hash")
    model_file = st.file_uploader("model.pkl hochladen", type=None, key="model")

    if model_file is not None:
        try:
            computed = audit.sha256_bytes(model_file.getvalue())
            render_proof_result("model_hash", expected_model, computed)

            if hashes_match(expected_model, computed):
                st.success("model.pkl ist unveraendert.")
            else:
                st.error("model.pkl weicht vom registrierten Hash ab.")

        except audit.AuditError as exc:
            st.error(str(exc))

    else:
        st.info("Noch keine model.pkl hochgeladen.")

    st.divider()

    st.subheader("config_hash")
    config_file = st.file_uploader("config.json hochladen", type=["json"], key="config")

    if config_file is not None:
        try:
            computed = audit.sha256_bytes(config_file.getvalue())
            match = render_proof_result("config_hash", expected_config, computed)

            if match:
                st.success("config.json ist unveraendert.")
            else:
                st.error("config.json weicht vom registrierten Hash ab.")

                # Konditionaler Hinweis auf die bekannte Backend-Inkonsistenz.
                # Das Ergebnis wird NICHT verfaelscht - nur erklaert.
                st.warning(
                    "Hinweis (bekannte moegliche Inkonsistenz): Falls die hochgeladene "
                    "config.json korrekt ist, kann der on-chain registrierte config_hash "
                    "aus einem veralteten Build stammen. Abhilfe im Backend: "
                    "hash_files.py erneut ausfuehren und das Modell neu registrieren. "
                    "Das angezeigte Pruefergebnis bleibt unveraendert ehrlich."
                )

        except audit.AuditError as exc:
            st.error(str(exc))

    else:
        st.info("Noch keine config.json hochgeladen.")


# --------------------------------------------------------------------------- #
# Tab 4: On-Chain-Status
# --------------------------------------------------------------------------- #
with tab_status:
    st.header("On-Chain-Status")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("RPC-Knoten erreichbar", "Ja" if STATE["connected"] else "Nein")
        st.metric("ABI kompiliert", "Ja" if STATE["abi_available"] else "Nein")

    with col2:
        network = DEPLOYMENT_LOCAL.get("network", "—")
        st.metric("Netzwerk", network)
        st.metric("RPC-URL", STATE["rpc"])

    address = STATE["address"] or DEPLOYMENT_LOCAL.get("contractAddress")

    st.write("**Contract-Adresse:**")
    st.code(address or "(unbekannt)", language="text")

    explorer_url = DEPLOYMENT_LOCAL.get("explorerUrl")

    if explorer_url:
        st.link_button("Contract im Explorer oeffnen", explorer_url)
    else:
        st.caption("Lokales Netzwerk — kein Block-Explorer verfuegbar.")

    if not STATE["abi_available"]:
        st.error(
            "Contract-ABI fehlt. Einmalig kompilieren (in contracts/): "
            "npm install && npx hardhat compile."
        )

    if not STATE["connected"] and STATE["error"]:
        st.error(STATE["error"])

    if STATE["connected"]:
        try:
            info = chain.chain_info(STATE["web3"])
            records = chain.list_records(STATE["contract"])

            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Chain-ID", info["chainId"])
            col_b.metric("Block", info["blockNumber"])
            col_c.metric("Registrierungen gesamt", records["total"])

            if records["ids"]:
                st.write("**Alle Record-IDs:**")

                st.dataframe(
                    [{"recordId": rid} for rid in records["ids"]],
                    hide_index=True,
                    use_container_width=True,
                )

        except Exception as exc:  # Lesefehler nicht als Stacktrace zeigen
            st.error(f"On-chain-Lesefehler: {exc}")

    if LAST_REG:
        st.subheader("Letzte Registrierung (lokal protokolliert)")

        st.dataframe(
            [{"Feld": k, "Wert": str(v)} for k, v in LAST_REG.items()],
            hide_index=True,
            use_container_width=True,
        )