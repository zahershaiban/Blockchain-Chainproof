"""Reine Formatierungs- und Statuslogik — ohne Streamlit-Import, damit testbar.

Hier lebt die Drei-Zustand-Semantik des Audits:
- VERIFIED   : Wert stimmt überein UND die Referenz wurde on-chain gelesen.
- MISMATCH   : Wert weicht von der Referenz ab (wird niemals beschönigt).
- UNVERIFIED : keine on-chain-Bestätigung möglich (Fallback oder Wert fehlt).
"""

from datetime import datetime, timezone

VERIFIED = "verified"
MISMATCH = "mismatch"
UNVERIFIED = "unverified"

# Badge-Darstellung: Text + Form-Marker, damit Status nie nur über Farbe läuft.
BADGE_TEXT = {
    VERIFIED: "Verifiziert",
    MISMATCH: "Abweichend",
    UNVERIFIED: "Unbestätigt",
}
BADGE_MARKER = {
    VERIFIED: "●",
    MISMATCH: "✕",
    UNVERIFIED: "◌",
}


def hashes_match(expected: str, computed: str) -> bool:
    """Vergleicht zwei Hex-Hashes case-insensitiv (Semantik wie bisher)."""
    return bool(expected) and bool(computed) and expected.lower() == computed.lower()


def derive_status(expected: str, computed: str, source: str) -> str:
    """Leitet den Drei-Zustand eines Beweises ab.

    - Abweichung ist IMMER 'mismatch' (wird nie beschönigt).
    - Übereinstimmung ist nur dann 'verified', wenn der erwartete Wert
      on-chain gelesen wurde (source == 'chain').
    - Übereinstimmung gegen den lokalen Fallback ist 'unverified'.
    - Ohne Vergleichswert(e) ebenfalls 'unverified'.
    """
    if not expected or not computed:
        return UNVERIFIED
    if not hashes_match(expected, computed):
        return MISMATCH
    return VERIFIED if source == "chain" else UNVERIFIED


def truncate_middle(value: str, prefix: int = 6, suffix: int = 6) -> str:
    """Kürzt lange Hashes mittig: 'a1b2c3…9f8e7d'. Kurze Werte unverändert."""
    # +1: Platz für das einzelne Ellipsen-Zeichen (U+2026).
    if not value or len(value) <= prefix + suffix + 1:
        return value or ""
    return f"{value[:prefix]}…{value[-suffix:]}"


def diff_positions(a: str, b: str) -> set:
    """Indizes, an denen sich zwei Strings unterscheiden (inkl. Längen-Überhang)."""
    positions = set()
    for i in range(max(len(a), len(b))):
        ca = a[i] if i < len(a) else None
        cb = b[i] if i < len(b) else None
        if ca != cb:
            positions.add(i)
    return positions


def format_timestamp(ts) -> str:
    """Unix-Sekunden lesbar formatieren (Semantik wie bisheriges fmt_timestamp)."""
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )
    except (ValueError, TypeError, OSError):
        return str(ts)


def format_bytes(num) -> str:
    """Dateigröße lesbar (B/KB/MB/GB). Erwartet eine Zahl >= 0 (kein None)."""
    for unit in ("B", "KB", "MB", "GB"):
        if unit == "GB" or num < 1024:
            return f"{num:.0f} {unit}" if unit == "B" else f"{num:.1f} {unit}"
        num /= 1024
