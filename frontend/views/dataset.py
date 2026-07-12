"""Tab 2: Dataset-Audit — Merkle-Root-Abgleich, Zeilen-Diff, Einzelzeilen-Proof.

Das Ergebnis (Verdict-Banner) steht VOR allen Details. Die Prüfsemantik kommt
unverändert aus audit.py; audit_ext liefert nur Anzeige-Kontext.
"""

import streamlit as st

import app_state
import audit
import audit_ext
from ui import components as ui
from ui import format as fmt


def _load_data(state: dict):
    """Ermittelt die zu prüfenden Bytes (Tamper-Demo oder Upload) + Label."""
    left, right = st.columns([2, 1])
    with left:
        uploaded = st.file_uploader("Dataset-CSV hochladen", type=["csv"], key="ds")
    with right:
        use_tamper = st.toggle(
            "Tamper-Demo: manipulierte Datei (data/tampered_dataset.csv) verwenden"
        )
    if use_tamper:
        if app_state.TAMPERED_PATH.exists():
            return (
                app_state.TAMPERED_PATH.read_bytes(),
                "data/tampered_dataset.csv (Tamper-Demo)",
            )
        st.error("data/tampered_dataset.csv nicht gefunden.")
        return None, None
    if uploaded is not None:
        return uploaded.getvalue(), uploaded.name
    return None, None


def render(state: dict) -> None:
    st.header("Dataset-Audit (Merkle-Root)")
    st.write(
        "Lade `health_dataset_1000.csv` hoch. Der Merkle-Root wird neu berechnet "
        "und gegen den registrierten Root verglichen. Die Kopfzeile ist Blatt 0, "
        "Zeile 1 ist der erste Datensatz (P0001). Zum Zurücksetzen die Datei "
        "über das ✕ im Uploader entfernen bzw. den Toggle deaktivieren."
    )

    expected_root = app_state.expected_value(state, "dataset_merkle_root")
    data, source_label = _load_data(state)

    if data is None:
        ui.empty_state("Bitte eine CSV hochladen oder die Tamper-Demo aktivieren.")
        return

    ui.file_summary(source_label, len(data))

    try:
        rows = audit.load_csv_rows_from_bytes(data)
    except audit.AuditError as exc:
        st.error(str(exc))
        return

    # Sanity-Check zuerst (erklärt WARUM, statt nur 'fehlgeschlagen').
    ok, messages = audit.sanity_check(rows)
    if not ok:
        for msg in messages:
            st.warning(msg)

    # --- Ergebnis zuerst: Ganzdatei-Abgleich ---
    computed_root = audit.get_merkle_root(rows)
    status = fmt.derive_status(expected_root, computed_root, state["source"])
    if status == fmt.VERIFIED:
        ui.verdict(
            status, "Der komplette Datensatz entspricht dem registrierten Root."
        )
    elif status == fmt.MISMATCH:
        ui.verdict(status, "Der Datensatz weicht vom registrierten Root ab.")
    elif not expected_root:
        ui.verdict(status, "Kein Referenzwert verfügbar — Abgleich nicht möglich.")
    else:
        ui.verdict(
            status,
            "Übereinstimmung nur mit lokalem Fallback-Wert — nicht on-chain "
            "bestätigt.",
        )

    ui.hash_compare_card(
        "dataset_merkle_root", expected_root, computed_root, state["source"]
    )

    # --- Welche Zeilen weichen ab? (gegen registrierte Blätter) ---
    registered = audit.load_registered_leaves(expected_root)
    if registered is not None:
        leaves, _ = registered
        diffs = audit_ext.enrich_diffs(rows, leaves, audit_ext.load_original_rows())
        if diffs:
            st.subheader(f"Abweichende Zeilen ({len(diffs)})")
            flt = st.text_input(
                "Filter (patient_id oder Status)", key="ds_filter"
            ).strip().lower()
            table = [
                {
                    "Zeilenindex": d["index"],
                    "patient_id": d["patient_id"],
                    "Status": d["status"],
                    "Hochgeladen (neu)": d["hochgeladen"] or "—",
                    "Registriert (alt)": d["registriert"]
                    or "(nur Hash registriert)",
                }
                for d in diffs
                if not flt
                or flt in d["patient_id"].lower()
                or flt in d["status"].lower()
            ]
            st.dataframe(table, hide_index=True, use_container_width=True)
            st.caption(
                "Sortierung per Klick auf den Spaltenkopf. 'Registriert (alt)' wird "
                "nur gezeigt, wenn der Inhalt kryptografisch zum registrierten "
                "Blatt-Hash passt."
            )
        else:
            st.caption("Zeilenweiser Abgleich: keine Abweichungen.")
    else:
        st.caption(
            "Zeilenweiser Abgleich nicht möglich (dataset_merkle.json fehlt "
            "oder ist nicht mit dem on-chain-Root konsistent)."
        )

    # --- Einzelzeilen-Verifikation mit Merkle-Proof ---
    st.subheader("Einzelzeilen-Verifikation (Merkle-Proof)")
    if not expected_root:
        # Ohne Referenz-Root ist jede Proof-Prüfung definitionsgemäß unmöglich —
        # ehrlich als 'unbestätigt' ausweisen statt fälschlich als Manipulation.
        ui.verdict(
            fmt.UNVERIFIED,
            "Kein Referenzwert verfügbar — Einzelzeilen-Verifikation nicht möglich.",
        )
        return

    def _row_label(i: int) -> str:
        pid = rows[i].split(",")[0]
        return "0 — Kopfzeile" if i == 0 else f"{i} — {pid}"

    row_index = st.selectbox(
        "Zu prüfende Zeile (Auswahl über patient_id)",
        list(range(len(rows))),
        index=min(1, len(rows) - 1),
        format_func=_row_label,
    )
    try:
        row, proof, is_valid = audit.verify_row_against_root(
            rows, int(row_index), expected_root
        )
    except audit.AuditError as exc:
        st.error(str(exc))
        return

    st.caption(f"Ausgewählte Zeile (patient_id: {row.split(',')[0]})")
    st.code(row, language="text")
    if is_valid:
        if state["source"] == "chain":
            ui.verdict(
                fmt.VERIFIED,
                "Verifiziert: diese Zeile gehört zum registrierten Datensatz.",
            )
        else:
            ui.verdict(
                fmt.UNVERIFIED,
                "Zeile passt zum lokalen Fallback-Root — nicht on-chain bestätigt.",
            )
    else:
        ui.verdict(
            fmt.MISMATCH,
            "Verifikation fehlgeschlagen: Zeile oder Datensatz wurde verändert.",
        )

    with st.expander("Merkle-Proof anzeigen (Pfad Blatt → Root)"):
        ui.proof_path(
            audit_ext.compute_proof_steps(rows, int(row_index), expected_root)
        )
