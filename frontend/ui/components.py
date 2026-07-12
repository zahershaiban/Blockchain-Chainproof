"""Wiederverwendbare UI-Bausteine. Rendern ausschließlich — keine Prüflogik.

Alle dynamischen Werte werden vor HTML-Einbettung escaped. Der Kopier-Button
für Volltexte kommt von st.code (eingebauter Copy-Button von Streamlit).
"""

import html
from datetime import datetime

import streamlit as st

from ui import format as fmt


def status_badge(status: str) -> str:
    """HTML für einen Statusbadge (Farbe + Form-Marker + Text)."""
    return (
        f'<span class="cp-badge cp-badge--{html.escape(status)}">'
        f'<span class="cp-marker">{fmt.BADGE_MARKER[status]}</span>'
        f"{fmt.BADGE_TEXT[status]}</span>"
    )


def provenance_badge(source: str) -> str:
    """Herkunfts-Kennzeichnung eines Referenzwerts (on-chain vs. Fallback)."""
    if source == "chain":
        return (
            '<span class="cp-badge cp-badge--verified">'
            '<span class="cp-marker">●</span>on-chain gelesen</span>'
        )
    return (
        '<span class="cp-badge cp-badge--unverified">'
        '<span class="cp-marker">◌</span>lokaler Fallback — unbestätigt</span>'
    )


def hash_html(value: str, diff_at=None) -> str:
    """HTML für einen Hash: Monospace, umbruchsicher, Volltext im Tooltip.

    diff_at: Menge von Zeichenindizes, die als abweichend hervorgehoben werden.
    """
    if not value:
        return '<span class="cp-hash">(nicht verfügbar)</span>'
    diff_at = diff_at or set()
    parts = []
    for i, ch in enumerate(value):
        ch_esc = html.escape(ch)
        if i in diff_at:
            parts.append(f'<span class="cp-diff">{ch_esc}</span>')
        else:
            parts.append(ch_esc)
    return (
        f'<span class="cp-hash" title="{html.escape(value)}">{"".join(parts)}</span>'
    )


def hash_compare_card(label: str, expected: str, computed: str, source: str) -> str:
    """Vergleichskarte für einen Beweis. Rendert und gibt den Status zurück.

    Bei Mismatch werden die abweichenden Zeichen beider Hashes hervorgehoben.
    Volltext + Copy-Button liegen im Expander (st.code hat eingebauten Copy).
    """
    status = fmt.derive_status(expected, computed, source)
    diff = (
        fmt.diff_positions(expected or "", computed or "")
        if status == fmt.MISMATCH
        else set()
    )
    expected_caption = (
        "Erwartet (on-chain)"
        if source == "chain"
        else "Erwartet (lokaler Fallback — nicht on-chain bestätigt)"
    )
    st.markdown(
        f"""<div class="cp-card">
  <div class="cp-card-head">
    <span class="cp-card-label">{html.escape(label)}</span>
    {status_badge(status)}
  </div>
  <div class="cp-kv">{expected_caption}</div>
  <div>{hash_html(expected, diff)}</div>
  <div class="cp-kv" style="margin-top:0.5em">Neu berechnet</div>
  <div>{hash_html(computed, diff)}</div>
</div>""",
        unsafe_allow_html=True,
    )
    with st.expander(f"{label}: Volltext & Kopieren"):
        st.code(
            f"erwartet:  {expected or '—'}\nberechnet: {computed or '—'}",
            language="text",
        )
    return status


def proof_list(items, source: str) -> None:
    """Liste registrierter Beweise (nur Referenzwerte, kein Vergleich)."""
    for label, value in items:
        st.markdown(
            f'<div class="cp-card"><div class="cp-card-head">'
            f'<span class="cp-card-label">{html.escape(label)}</span>'
            f"{provenance_badge(source)}</div>"
            f"<div>{hash_html(value)}</div></div>",
            unsafe_allow_html=True,
        )
        with st.expander(f"{label}: Volltext & Kopieren"):
            st.code(value or "—", language="text")


def status_bar(state: dict) -> None:
    """Persistenter Verbindungs-Status über allen Tabs (chain/fallback/offline)."""
    if state["connected"]:
        cls, marker, text = "chain", "●", (
            f"Chain verbunden ({state['rpc']}) — Vertrauensanker ist der Contract "
            f"{fmt.truncate_middle(state['address'] or '', 10, 8)}. "
            "Erwartete Werte werden on-chain gelesen."
        )
    elif state["source"] == "fallback":
        cls, marker, text = "fallback", "◌", (
            "FALLBACK aktiv: Erwartete Werte stammen aus der lokalen "
            "artifacts/hashes.json und sind NICHT on-chain verifiziert. Für ein "
            "echtes Audit den Hardhat-Node starten und ggf. die ABI kompilieren."
        )
    else:
        cls, marker, text = "offline", "✕", (
            "Keine Chain-Verbindung und kein lokaler Fallback (hashes.json) — "
            "es können keine erwarteten Werte angezeigt werden."
        )
    st.markdown(
        f'<div class="cp-statusbar cp-statusbar--{html.escape(cls)}">'
        f'<span class="cp-marker">{marker}</span>'
        f"<span>{html.escape(text)}</span></div>",
        unsafe_allow_html=True,
    )
    if not state["connected"] and state["error"]:
        with st.expander("Details zur Verbindungsstörung"):
            st.code(state["error"], language="text")


def verdict(status: str, text: str) -> None:
    """Großes Ergebnis-Banner (Ergebnis zuerst, vor allen Details)."""
    st.markdown(
        f'<div class="cp-verdict cp-verdict--{html.escape(status)}">'
        f'<span class="cp-marker">{fmt.BADGE_MARKER[status]}</span>'
        f"<span>{fmt.BADGE_TEXT[status]} — {html.escape(text)}</span></div>",
        unsafe_allow_html=True,
    )


def empty_state(text: str) -> None:
    """Ruhiger Platzhalter für Leerzustände (statt blauer Info-Box)."""
    st.markdown(
        f'<div class="cp-empty">{html.escape(text)}</div>', unsafe_allow_html=True
    )


def file_summary(label: str, size_bytes=None) -> None:
    """Zeigt kompakt, welche Datei gerade geprüft wird (Name, Größe, Zeitpunkt)."""
    parts = [f"Geprüft wird: <b>{html.escape(label)}</b>"]
    if size_bytes is not None:
        parts.append(fmt.format_bytes(size_bytes))
    parts.append(datetime.now().strftime("geprüft um %H:%M:%S"))
    st.markdown(
        f'<div class="cp-kv">{" · ".join(parts)}</div>', unsafe_allow_html=True
    )


def sidebar_kv(label: str, value) -> None:
    """Key-Value-Zeile für die Sidebar (Volltext im Tooltip)."""
    value = str(value)
    st.markdown(
        f'<div class="cp-kv">{html.escape(label)}</div>'
        f'<div class="cp-hash" title="{html.escape(value)}">{html.escape(value)}</div>',
        unsafe_allow_html=True,
    )


def proof_path(path: dict) -> None:
    """Merkle-Pfad Blatt → Root lesbar darstellen (statt rohem JSON-Dump)."""
    st.markdown(
        '<div class="cp-kv">Ebene 0 — Blatt-Hash = SHA-256 der Zeile</div>'
        f'<div>{hash_html(path["leaf"])}</div>',
        unsafe_allow_html=True,
    )
    st.dataframe(
        [
            {
                "Ebene": step["ebene"],
                "Verknüpfung": (
                    "SHA-256(Partner + aktuell)"
                    if step["partner_position"] == "left"
                    else "SHA-256(aktuell + Partner)"
                ),
                "Partner-Hash": fmt.truncate_middle(step["partner_hash"], 10, 10),
                "Zwischenergebnis": fmt.truncate_middle(step["ergebnis"], 10, 10),
            }
            for step in path["steps"]
        ],
        hide_index=True,
        use_container_width=True,
    )
    diff = (
        fmt.diff_positions(path["expected_root"] or "", path["computed_root"])
        if not path["is_valid"]
        else set()
    )
    st.markdown(
        f'<div class="cp-kv">Rekonstruierter Root</div>'
        f'<div>{hash_html(path["computed_root"], diff)}</div>'
        f'<div class="cp-kv" style="margin-top:0.5em">Registrierter Root</div>'
        f'<div>{hash_html(path["expected_root"], diff)}</div>',
        unsafe_allow_html=True,
    )
