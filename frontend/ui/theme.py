"""ChainProof UI-Theme: Design-Tokens und zentrales CSS an EINER Stelle.

Semantische Statusfarben (verified/mismatch/unverified) funktionieren auf
hellem UND dunklem Streamlit-Theme: Fließtext nutzt immer die Theme-Textfarbe,
die Statusfarbe trägt nur Marker, Rahmen und eine leichte Flächen-Tönung
(color-mix mit transparent). Status wird nie über Farbe allein kommuniziert —
immer Farbe + Form-Marker + Text (siehe ui/format.py BADGE_*).
"""

import streamlit as st

# Design-Tokens: einzige Quelle für Farben, Radien, Abstände, Typografie.
TOKENS = {
    "accent": "#4c8bf5",      # EIN Akzentton (Links, aktive Elemente)
    "verified": "#2da44e",    # Grün — on-chain bestätigt und übereinstimmend
    "mismatch": "#d1242f",    # Rot — Abweichung vom registrierten Wert
    "unverified": "#bf8700",  # Amber — nicht on-chain bestätigt (Fallback)
    "radius": "6px",
    "space": "0.75rem",
    "mono": "'Source Code Pro', ui-monospace, Consolas, monospace",
}

_CSS = f"""
<style>
:root {{
  --cp-accent: {TOKENS["accent"]};
  --cp-verified: {TOKENS["verified"]};
  --cp-mismatch: {TOKENS["mismatch"]};
  --cp-unverified: {TOKENS["unverified"]};
  --cp-radius: {TOKENS["radius"]};
  --cp-space: {TOKENS["space"]};
  --cp-mono: {TOKENS["mono"]};
}}

/* Statusbadge: Farbe + Form-Marker + Text — nie Farbe allein. */
.cp-badge {{
  display: inline-flex; align-items: center; gap: 0.4em;
  padding: 0.15em 0.6em; border-radius: 999px;
  border: 1px solid var(--cp-c);
  background: color-mix(in srgb, var(--cp-c) 12%, transparent);
  font-size: 0.85em; font-weight: 600; white-space: nowrap;
}}
.cp-badge .cp-marker {{ color: var(--cp-c); font-weight: 700; }}
.cp-badge--verified {{ --cp-c: var(--cp-verified); }}
.cp-badge--mismatch {{ --cp-c: var(--cp-mismatch); }}
.cp-badge--unverified {{ --cp-c: var(--cp-unverified); }}

/* Persistenter Statusbalken über den Tabs (sticky unter dem Streamlit-Header;
   falls sticky in einer Streamlit-Version nicht greift, degradiert er ohne
   Schaden zu einem normalen Balken). */
.cp-statusbar {{
  position: sticky; top: 3.75rem; z-index: 999;
  display: flex; align-items: center; gap: 0.75em; flex-wrap: wrap;
  padding: 0.5em 0.9em; margin-bottom: var(--cp-space);
  border: 1px solid var(--cp-c); border-left-width: 4px;
  border-radius: var(--cp-radius);
  background: color-mix(in srgb, var(--cp-c) 10%, transparent);
  font-size: 0.9em;
}}
.cp-statusbar .cp-marker {{ color: var(--cp-c); font-weight: 700; }}
.cp-statusbar--chain {{ --cp-c: var(--cp-verified); }}
.cp-statusbar--fallback {{ --cp-c: var(--cp-unverified); }}
.cp-statusbar--offline {{ --cp-c: var(--cp-mismatch); }}

/* Hashes: Monospace; Umbruch erlaubt, damit lange Werte das Layout nie sprengen. */
.cp-hash {{
  font-family: var(--cp-mono); font-size: 0.85em;
  overflow-wrap: anywhere; word-break: break-all;
}}
.cp-hash .cp-diff {{
  color: var(--cp-mismatch); font-weight: 700;
  text-decoration: underline; text-underline-offset: 2px;
}}

/* Vergleichskarte für einen Beweis. */
.cp-card {{
  border: 1px solid rgba(128,128,128,0.35);
  border-radius: var(--cp-radius);
  padding: 0.8em 1em; margin-bottom: var(--cp-space);
}}
.cp-card .cp-card-head {{
  display: flex; justify-content: space-between; align-items: center;
  gap: 1em; margin-bottom: 0.5em; flex-wrap: wrap;
}}
.cp-card .cp-card-label {{ font-weight: 600; font-family: var(--cp-mono); }}

/* Kleine Beschriftungen (Key-Value, Metadaten). */
.cp-kv {{ font-size: 0.8em; opacity: 0.75; margin-bottom: 0.15em; }}

/* Ruhiger Leerzustand statt blauer Info-Box. */
.cp-empty {{
  border: 1px dashed rgba(128,128,128,0.45);
  border-radius: var(--cp-radius);
  padding: 1.2em; text-align: center; opacity: 0.7; font-size: 0.9em;
}}

/* Verdict-Banner: das Ergebnis zuerst, gut sichtbar. */
.cp-verdict {{
  display: flex; align-items: center; gap: 0.6em;
  border: 1px solid var(--cp-c); border-left-width: 6px;
  border-radius: var(--cp-radius);
  background: color-mix(in srgb, var(--cp-c) 10%, transparent);
  padding: 0.8em 1em; margin: var(--cp-space) 0;
  font-size: 1.05em; font-weight: 600;
}}
.cp-verdict .cp-marker {{ color: var(--cp-c); font-weight: 700; }}
.cp-verdict--verified {{ --cp-c: var(--cp-verified); }}
.cp-verdict--mismatch {{ --cp-c: var(--cp-mismatch); }}
.cp-verdict--unverified {{ --cp-c: var(--cp-unverified); }}
</style>
"""


def inject() -> None:
    """Injiziert das zentrale CSS. Einmal pro Rerun in app.py aufrufen."""
    st.markdown(_CSS, unsafe_allow_html=True)
