# Frontend-Redesign ChainProof — Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Das Streamlit-Frontend unter `frontend/` von einem monolithischen Prototyp zu einem professionellen, modularen Audit-Tool umbauen — mit Design-Tokens, Drei-Zustand-Semantik (verified/mismatch/unverified) und unveränderter Prüflogik.

**Architecture:** `app.py` wird zu einem schlanken Kompositions-Layer; Prüflogik bleibt in `audit.py`/`chain.py` (unangetastet bis auf Umlaut-Korrektur in Meldungstexten). Neue Module: `ui/format.py` (pure, testbare Formatierungs- und Statuslogik), `ui/theme.py` (Design-Tokens + zentrales CSS), `ui/components.py` (Render-Bausteine), `audit_ext.py` (reine Anzeige-Helfer: Proof-Pfad, Diff mit Kontext), `app_state.py` (gecachter Zustand), `views/` (ein Modul pro Tab). Die alten Tabs bleiben lauffähig, bis alle Views fertig sind — `app.py` wird zuletzt ersetzt.

**Tech Stack:** Python 3.13, Streamlit 1.37.1, web3.py, pytest 9.1.0 (bereits installiert). Kein neues Framework, kein JS-Build.

---

## Invarianten (aus der Spezifikation — bei JEDER Task beachten)

1. **Keine Logikänderung.** Hash-Vergleich, Merkle-Proof-Verifikation, Fallback-Verhalten und Fehlermeldungen bleiben semantisch identisch. Die Views rufen weiterhin `audit.verify_row_against_root`, `audit.get_merkle_root`, `audit.sanity_check`, `audit.load_registered_leaves`, `audit.sha256_bytes` auf — neue Helfer dienen nur der Darstellung. Ein Mismatch wird nie beschönigt.
2. **Kein neues Framework.** CSS ausschließlich gebündelt in `ui/theme.py` via `st.markdown(..., unsafe_allow_html=True)`.
3. **Korrekte deutsche Umlaute** (ü/ä/ö) in allen UI-Strings. Alle Dateien UTF-8.
4. **`backend/` und `contracts/` nicht anfassen.** (`frontend/audit.py`/`chain.py` dürfen angefasst werden, aber nur Meldungs-Strings — Task 12.)
5. **Keine Emojis als Statusträger** (kein ✅/❌/⚠️). Status = Farbe + Form-Marker (`●`/`✕`/`◌`, reine Textglyphen) + Textlabel.
6. Keine Gradients, Glows, Animationen, Glassmorphism, erfundene Metriken.

## Drei-Zustand-Semantik (zentrale Designentscheidung)

| Zustand | Bedeutung | Farbe | Marker | Label |
|---|---|---|---|---|
| `verified` | Werte stimmen überein UND Referenz wurde on-chain gelesen | Grün | `●` | Verifiziert |
| `mismatch` | Werte weichen ab (egal welche Quelle — nie beschönigt) | Rot | `✕` | Abweichend |
| `unverified` | Keine on-chain-Bestätigung möglich (Fallback-Quelle oder Wert fehlt) | Amber | `◌` | Unbestätigt |

Wichtig: Eine Übereinstimmung gegen den **lokalen Fallback** ist `unverified`, nicht `verified` — das ist die geforderte „nicht als Erfolg getarnt"-Regel.

## Merkle-Fakten (aus `backend/merkle_tree.py`, verifiziert)

- Blatt: `sha256(zeilen_string)` (UTF-8, Hex-Digest); Zeilen-String = `",".join(csv_row)`; Kopfzeile = Blatt 0.
- Eltern-Hash: `hash_pair(left, right) = sha256(left + right)` (Konkatenation der Hex-Strings).
- Bei ungerader Ebene wird das letzte Element mit sich selbst gepaart.
- Proof-Format: `[{"position": "left"|"right", "hash": "<hex>"}, ...]`; Verifikation: `position == "left"` → `hash_pair(partner, aktuell)`, sonst `hash_pair(aktuell, partner)`; am Ende exakter String-Vergleich mit dem Root.
- CSV-Kopfzeile beginnt mit `patient_id`; `data/tampered_dataset.csv` unterscheidet sich vom Original in genau Zeile 1 (P0001, age 32→33).

## Ziel-Dateistruktur

```
frontend/
├── app.py                  ERSETZT (Task 11): schlanker Kompositions-Layer
├── app_state.py            NEU (Task 6): gecachter Zustand, load_state/refresh
├── audit.py                UNVERÄNDERT bis auf Umlaute in Meldungen (Task 12)
├── audit_ext.py            NEU (Task 3): reine Anzeige-Helfer (Proof-Pfad, Diff-Kontext)
├── chain.py                UNVERÄNDERT bis auf Umlaute in Meldungen (Task 12)
├── ui/
│   ├── __init__.py         NEU (Task 1, leer)
│   ├── format.py           NEU (Task 2): pure Formatierung + Drei-Zustand-Logik
│   ├── theme.py            NEU (Task 4): Design-Tokens + zentrales CSS
│   └── components.py       NEU (Task 5): Badges, Karten, Statusbalken, Leerzustände
├── views/
│   ├── __init__.py         NEU (Task 1, leer)
│   ├── overview.py         NEU (Task 7): Tab „Registry-Übersicht"
│   ├── dataset.py          NEU (Task 8): Tab „Dataset-Audit"
│   ├── model.py            NEU (Task 9): Tab „Modell- & Config-Audit"
│   └── chain_status.py     NEU (Task 10): Tab „On-Chain-Status"
└── tests/
    ├── __init__.py         NEU (Task 1, leer)
    ├── test_format.py      NEU (Task 2)
    └── test_audit_ext.py   NEU (Task 3)
```

**Import-Konvention:** Zur Laufzeit legt `app.py` (wie bisher) `frontend/` auf `sys.path`; alle App-Module importieren absolut (`from ui import components`, `import app_state`). Die Tests laufen vom Repo-Root und importieren als Paket (`from frontend.ui import format`) — deshalb brauchen `ui/`, `views/`, `tests/` je ein leeres `__init__.py` (`frontend/__init__.py` existiert schon). Die getesteten Module (`ui/format.py`, `audit_ext.py`) importieren **kein** anderes `frontend`-Modul und kein Streamlit, damit beide Importwelten funktionieren.

---

### Task 1: Branch und Paketgerüst

**Files:**
- Create: `frontend/ui/__init__.py` (leer)
- Create: `frontend/views/__init__.py` (leer)
- Create: `frontend/tests/__init__.py` (leer)

- [ ] **Step 1: Feature-Branch von `dev` erstellen**

```bash
git checkout dev
git checkout -b feature/frontend-redesign
```

- [ ] **Step 2: Prüfen, dass `frontend/__init__.py` leer ist**

```bash
cat frontend/__init__.py
```

Erwartet: keine Ausgabe (leere Datei). Falls die Datei Inhalt hat: Inhalt notieren und NICHT löschen — dann in den Testimports statt `from frontend.ui import format` mit `sys.path.insert(0, "frontend")` und `from ui import format` arbeiten. (Stand jetzt ist sie leer.)

- [ ] **Step 3: Leere Paket-Marker anlegen**

Drei leere Dateien erstellen: `frontend/ui/__init__.py`, `frontend/views/__init__.py`, `frontend/tests/__init__.py`.

- [ ] **Step 4: pytest-Verfügbarkeit bestätigen**

```bash
python -m pytest --version
```

Erwartet: `pytest 9.1.0` (bereits installiert; falls nicht: `python -m pip install pytest`).

- [ ] **Step 5: Commit**

```bash
git add frontend/ui/__init__.py frontend/views/__init__.py frontend/tests/__init__.py
git commit -m "frontend: Paketgeruest fuer ui/, views/, tests/

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: `ui/format.py` — pure Formatierungs- und Statuslogik (TDD)

**Files:**
- Test: `frontend/tests/test_format.py`
- Create: `frontend/ui/format.py`

- [ ] **Step 1: Failing Tests schreiben**

Datei `frontend/tests/test_format.py` mit exakt diesem Inhalt anlegen:

```python
"""Tests für die reine Formatierungs- und Statuslogik (frontend/ui/format.py)."""

from frontend.ui import format as fmt


class TestHashesMatch:
    def test_gleiche_hashes_case_insensitiv(self):
        assert fmt.hashes_match("ABC123", "abc123") is True

    def test_verschiedene_hashes(self):
        assert fmt.hashes_match("abc", "abd") is False

    def test_leere_werte_sind_kein_match(self):
        assert fmt.hashes_match("", "abc") is False
        assert fmt.hashes_match("abc", "") is False
        assert fmt.hashes_match("", "") is False


class TestDeriveStatus:
    def test_chain_und_uebereinstimmung_ist_verified(self):
        assert fmt.derive_status("abc", "abc", "chain") == fmt.VERIFIED

    def test_abweichung_ist_immer_mismatch(self):
        assert fmt.derive_status("abc", "abd", "chain") == fmt.MISMATCH
        assert fmt.derive_status("abc", "abd", "fallback") == fmt.MISMATCH

    def test_fallback_uebereinstimmung_ist_unverified(self):
        assert fmt.derive_status("abc", "abc", "fallback") == fmt.UNVERIFIED

    def test_fehlende_werte_sind_unverified(self):
        assert fmt.derive_status("", "abc", "chain") == fmt.UNVERIFIED
        assert fmt.derive_status("abc", "", "chain") == fmt.UNVERIFIED


class TestTruncateMiddle:
    def test_langer_hash_wird_mittig_gekuerzt(self):
        h = "a1b2c3" + "0" * 52 + "9f8e7d"
        assert fmt.truncate_middle(h) == "a1b2c3…9f8e7d"

    def test_kurzer_wert_bleibt_unveraendert(self):
        assert fmt.truncate_middle("abcdef") == "abcdef"

    def test_leerer_wert(self):
        assert fmt.truncate_middle("") == ""
        assert fmt.truncate_middle(None) == ""


class TestDiffPositions:
    def test_identische_strings_keine_diff(self):
        assert fmt.diff_positions("abc", "abc") == set()

    def test_einzelnes_abweichendes_zeichen(self):
        assert fmt.diff_positions("abc", "aXc") == {1}

    def test_laengenueberhang_zaehlt_als_diff(self):
        assert fmt.diff_positions("abc", "abcXY") == {3, 4}


class TestFormatBytes:
    def test_bytes(self):
        assert fmt.format_bytes(512) == "512 B"

    def test_kilobytes(self):
        assert fmt.format_bytes(2048) == "2.0 KB"
```

- [ ] **Step 2: Tests laufen lassen — sie MÜSSEN fehlschlagen**

```bash
python -m pytest frontend/tests/test_format.py -v
```

Erwartet: `ModuleNotFoundError: No module named 'frontend.ui.format'` (bzw. ImportError).

- [ ] **Step 3: `frontend/ui/format.py` implementieren**

```python
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
    """Dateigröße lesbar (B/KB/MB/GB)."""
    for unit in ("B", "KB", "MB", "GB"):
        if num < 1024 or unit == "GB":
            return f"{num:.0f} {unit}" if unit == "B" else f"{num:.1f} {unit}"
        num /= 1024
```

- [ ] **Step 4: Tests laufen lassen — sie müssen bestehen**

```bash
python -m pytest frontend/tests/test_format.py -v
```

Erwartet: alle Tests PASS (15 passed).

- [ ] **Step 5: Commit**

```bash
git add frontend/ui/format.py frontend/tests/test_format.py
git commit -m "frontend: ui/format.py mit Drei-Zustand-Logik und Hash-Formatierung (TDD)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: `audit_ext.py` — Anzeige-Helfer für Proof-Pfad und Diff-Kontext (TDD)

**Files:**
- Test: `frontend/tests/test_audit_ext.py`
- Create: `frontend/audit_ext.py`

Zweck: `views/dataset.py` braucht (a) den Merkle-Pfad Blatt→Root als lesbare Schritte statt rohem JSON und (b) den Zeilen-Diff mit Inhalt „alt vs. neu" statt nur „geändert/fehlt". Beides sind reine Zusatzfunktionen — `audit.py` bleibt unangetastet, die Verifikations-Entscheidung trifft weiterhin `audit.verify_row_against_root`.

- [ ] **Step 1: Failing Tests schreiben**

Datei `frontend/tests/test_audit_ext.py` mit exakt diesem Inhalt anlegen:

```python
"""Tests für die darstellungsnahen Audit-Erweiterungen (frontend/audit_ext.py).

Wichtigste Eigenschaft: compute_proof_steps muss zum bestehenden
verify_merkle_proof identisch urteilen — die Anzeige darf nie etwas anderes
behaupten als die Verifikation.
"""

import sys
from pathlib import Path

# backend/ für die Referenz-Merkle-Implementierung importierbar machen.
sys.path.append(str(Path(__file__).resolve().parents[2] / "backend"))

from merkle_tree import (
    generate_merkle_proof,
    get_merkle_root,
    sha256,
    verify_merkle_proof,
)

from frontend import audit_ext

ROWS = [
    "patient_id,age,gender",
    "P0001,32,Female",
    "P0002,45,Male",
    "P0003,58,Female",
    "P0004,29,Male",
]


class TestComputeProofSteps:
    def test_pfad_endet_im_merkle_root(self):
        root = get_merkle_root(ROWS)
        for index in range(len(ROWS)):
            path = audit_ext.compute_proof_steps(ROWS, index, root)
            assert path["computed_root"] == root
            assert path["is_valid"] is True

    def test_urteil_identisch_zu_verify_merkle_proof(self):
        root = get_merkle_root(ROWS)
        for index in range(len(ROWS)):
            proof = generate_merkle_proof(ROWS, index)
            expected = verify_merkle_proof(ROWS[index], proof, root)
            path = audit_ext.compute_proof_steps(ROWS, index, root)
            assert path["is_valid"] == expected

    def test_manipulierte_zeile_ist_ungueltig(self):
        root = get_merkle_root(ROWS)
        tampered = ROWS.copy()
        tampered[1] = "P0001,33,Female"  # age 32 -> 33 (wie tampered_dataset.csv)
        path = audit_ext.compute_proof_steps(tampered, 1, root)
        assert path["is_valid"] is False

    def test_blatt_ist_sha256_der_zeile(self):
        root = get_merkle_root(ROWS)
        path = audit_ext.compute_proof_steps(ROWS, 2, root)
        assert path["leaf"] == sha256(ROWS[2])
        assert len(path["steps"]) == len(generate_merkle_proof(ROWS, 2))


class TestEnrichDiffs:
    def test_identische_daten_keine_diffs(self):
        leaves = [sha256(r) for r in ROWS]
        assert audit_ext.enrich_diffs(ROWS, leaves, ROWS) == []

    def test_geaenderte_zeile_mit_registriertem_kontext(self):
        leaves = [sha256(r) for r in ROWS]
        tampered = ROWS.copy()
        tampered[1] = "P0001,33,Female"
        diffs = audit_ext.enrich_diffs(tampered, leaves, ROWS)
        assert len(diffs) == 1
        d = diffs[0]
        assert d["index"] == 1
        assert d["patient_id"] == "P0001"
        assert d["status"] == audit_ext.STATUS_GEAENDERT
        assert d["hochgeladen"] == "P0001,33,Female"
        assert d["registriert"] == "P0001,32,Female"  # kryptografisch bestätigt

    def test_kontext_nur_bei_hash_bestaetigung(self):
        leaves = [sha256(r) for r in ROWS]
        tampered = ROWS.copy()
        tampered[1] = "P0001,33,Female"
        falsche_originale = ROWS.copy()
        falsche_originale[1] = "P0001,99,Female"  # passt nicht zum Blatt-Hash
        diffs = audit_ext.enrich_diffs(tampered, leaves, falsche_originale)
        assert diffs[0]["registriert"] is None

    def test_fehlende_zeile(self):
        leaves = [sha256(r) for r in ROWS]
        kurz = ROWS[:-1]
        diffs = audit_ext.enrich_diffs(kurz, leaves, ROWS)
        assert len(diffs) == 1
        assert diffs[0]["status"] == audit_ext.STATUS_FEHLT
        assert diffs[0]["patient_id"] == "—"

    def test_zusaetzliche_zeile(self):
        leaves = [sha256(r) for r in ROWS]
        lang = ROWS + ["P0005,77,Male"]
        diffs = audit_ext.enrich_diffs(lang, leaves, ROWS)
        assert len(diffs) == 1
        assert diffs[0]["status"] == audit_ext.STATUS_ZUSAETZLICH

    def test_ohne_originaldaten_kein_kontext(self):
        leaves = [sha256(r) for r in ROWS]
        tampered = ROWS.copy()
        tampered[2] = "P0002,46,Male"
        diffs = audit_ext.enrich_diffs(tampered, leaves, None)
        assert diffs[0]["registriert"] is None
```

- [ ] **Step 2: Tests laufen lassen — sie MÜSSEN fehlschlagen**

```bash
python -m pytest frontend/tests/test_audit_ext.py -v
```

Erwartet: `ImportError: cannot import name 'audit_ext' from 'frontend'`.

- [ ] **Step 3: `frontend/audit_ext.py` implementieren**

```python
"""Darstellungsnahe Audit-Erweiterungen. Ändern KEINE Prüfsemantik.

audit.py bleibt unangetastet; hier stehen nur zusätzliche, reine Funktionen,
die die Views mit Kontext versorgen (Proof-Pfad als Schritte, Diff mit
Zeileninhalt). Die Hash-Logik kommt direkt aus backend/merkle_tree.py —
identisch zu der Logik, mit der registriert und verifiziert wird.
"""

import csv
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from merkle_tree import generate_merkle_proof, hash_pair, sha256  # noqa: E402

ORIGINAL_DATASET = BASE_DIR / "data" / "health_dataset_1000.csv"

STATUS_GEAENDERT = "geändert"
STATUS_FEHLT = "fehlt (Zeile entfernt)"
STATUS_ZUSAETZLICH = "zusätzlich (nicht registriert)"


def compute_proof_steps(rows: list, row_index: int, expected_root: str) -> dict:
    """Rekonstruiert den Merkle-Pfad Blatt → Root als lesbare Schritte.

    Rechnet mit exakt denselben Backend-Funktionen wie verify_merkle_proof;
    'is_valid' ist deshalb identisch zum Urteil der bestehenden Verifikation
    (exakter String-Vergleich mit dem Root, wie im Backend).
    """
    proof = generate_merkle_proof(rows, row_index)
    current = sha256(rows[row_index])
    leaf = current
    steps = []
    for ebene, item in enumerate(proof, start=1):
        if item["position"] == "left":
            current = hash_pair(item["hash"], current)
        else:
            current = hash_pair(current, item["hash"])
        steps.append({
            "ebene": ebene,
            "partner_position": item["position"],
            "partner_hash": item["hash"],
            "ergebnis": current,
        })
    return {
        "leaf": leaf,
        "steps": steps,
        "computed_root": current,
        "expected_root": expected_root,
        "is_valid": current == expected_root,
    }


def load_original_rows():
    """Lädt die lokale Originaldatei als Zeilen-Strings (oder None).

    Gleiche Serialisierung wie backend/hash_files.load_csv_rows:
    csv.reader + ','.join — damit die Blatt-Hashes vergleichbar sind.
    """
    if not ORIGINAL_DATASET.exists():
        return None
    with open(ORIGINAL_DATASET, "r", encoding="utf-8") as file:
        return [",".join(row) for row in csv.reader(file)]


def enrich_diffs(rows: list, registered_leaves: list, original_rows=None) -> list:
    """Zeilenvergleich wie audit.diff_rows_against_leaves, plus Kontext.

    Der registrierte Zeileninhalt ist aus dem Blatt-Hash nicht rekonstruierbar.
    Er wird nur angezeigt, wenn die lokale Originaldatei vorliegt UND ihr
    Zeilen-Hash exakt dem registrierten Blatt entspricht — dann ist der Inhalt
    kryptografisch bestätigt. Andernfalls bleibt das Feld ehrlich leer (None).
    """
    diffs = []
    total = max(len(rows), len(registered_leaves))
    for i in range(total):
        uploaded_leaf = sha256(rows[i]) if i < len(rows) else None
        registered_leaf = registered_leaves[i] if i < len(registered_leaves) else None
        if uploaded_leaf == registered_leaf:
            continue
        if uploaded_leaf is None:
            status = STATUS_FEHLT
        elif registered_leaf is None:
            status = STATUS_ZUSAETZLICH
        else:
            status = STATUS_GEAENDERT
        registered_row = None
        if (
            registered_leaf is not None
            and original_rows is not None
            and i < len(original_rows)
            and sha256(original_rows[i]) == registered_leaf
        ):
            registered_row = original_rows[i]
        diffs.append({
            "index": i,
            "patient_id": rows[i].split(",")[0] if i < len(rows) else "—",
            "status": status,
            "hochgeladen": rows[i] if i < len(rows) else None,
            "registriert": registered_row,
        })
    return diffs
```

- [ ] **Step 4: Tests laufen lassen — alle müssen bestehen**

```bash
python -m pytest frontend/tests -v
```

Erwartet: alle Tests PASS (Format- + Audit-Ext-Tests, 26 passed).

- [ ] **Step 5: Commit**

```bash
git add frontend/audit_ext.py frontend/tests/test_audit_ext.py
git commit -m "frontend: audit_ext.py fuer Proof-Pfad-Anzeige und Diff-Kontext (TDD)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: `ui/theme.py` — Design-Tokens und zentrales CSS

**Files:**
- Create: `frontend/ui/theme.py`

- [ ] **Step 1: `frontend/ui/theme.py` anlegen**

```python
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
```

- [ ] **Step 2: Import-Smoke-Test**

```bash
python -c "import sys; sys.path.insert(0, 'frontend'); import ui.theme; print('ok:', len(ui.theme._CSS), 'Zeichen CSS')"
```

Erwartet: `ok: <Zahl> Zeichen CSS` (Streamlit-Warnungen über fehlenden ScriptRunContext sind unkritisch).

- [ ] **Step 3: Commit**

```bash
git add frontend/ui/theme.py
git commit -m "frontend: ui/theme.py mit Design-Tokens und zentralem CSS

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 5: `ui/components.py` — wiederverwendbare Render-Bausteine

**Files:**
- Create: `frontend/ui/components.py`

Alle Funktionen rendern nur (oder liefern HTML-Strings) — keine Prüflogik. Nutzereingaben/Hashes werden vor HTML-Einbettung mit `html.escape` behandelt.

- [ ] **Step 1: `frontend/ui/components.py` anlegen**

```python
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
        f'<span class="cp-badge cp-badge--{status}">'
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
        f'<div class="cp-statusbar cp-statusbar--{cls}">'
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
        f'<div class="cp-verdict cp-verdict--{status}">'
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
```

- [ ] **Step 2: Import-Smoke-Test**

```bash
python -c "import sys; sys.path.insert(0, 'frontend'); import ui.components; print('ok')"
```

Erwartet: `ok`.

- [ ] **Step 3: Commit**

```bash
git add frontend/ui/components.py
git commit -m "frontend: ui/components.py mit Badges, Karten, Statusbalken, Proof-Pfad

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 6: `app_state.py` — gecachter Zustand

**Files:**
- Create: `frontend/app_state.py`

Semantik von `load_state()` ist **identisch** zum bisherigen `app.py:load_state` (Chain zuerst; bei jedem Fehler Fallback auf `hashes.json` mit `source == "fallback"`, Fehlertext erhalten). Neu: Caching (`st.cache_resource` für die Verbindung, `st.cache_data` für Reads) und Kontextfelder für Sidebar/Views.

- [ ] **Step 1: `frontend/app_state.py` anlegen**

```python
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
```

- [ ] **Step 2: Import-Smoke-Test**

```bash
python -c "import sys; sys.path.insert(0, 'frontend'); import app_state; print('ok')"
```

Erwartet: `ok` (Streamlit-Cache-Warnungen außerhalb der Runtime sind unkritisch).

- [ ] **Step 3: Commit**

```bash
git add frontend/app_state.py
git commit -m "frontend: app_state.py mit gecachter Chain-Verbindung und Reads

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 7: `views/overview.py` — Tab „Registry-Übersicht"

**Files:**
- Create: `frontend/views/overview.py`

- [ ] **Step 1: `frontend/views/overview.py` anlegen**

```python
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
```

- [ ] **Step 2: Import-Smoke-Test**

```bash
python -c "import sys; sys.path.insert(0, 'frontend'); import views.overview; print('ok')"
```

Erwartet: `ok`.

- [ ] **Step 3: Commit**

```bash
git add frontend/views/overview.py
git commit -m "frontend: views/overview.py (Tab Registry-Uebersicht)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 8: `views/dataset.py` — Tab „Dataset-Audit" (Ergebnis zuerst)

**Files:**
- Create: `frontend/views/dataset.py`

Layout-Reihenfolge (Spezifikation „Ergebnis oben"): Eingabe-Controls kompakt → Datei-Zusammenfassung → Sanity-Warnungen → **Verdict-Banner** → Vergleichskarte → Abweichungstabelle (Filter + Kontext alt/neu) → Einzelzeilen-Verifikation (Auswahl über patient_id) → Proof-Pfad im Expander.

Semantik-Erhalt: `audit.load_csv_rows_from_bytes`, `audit.sanity_check`, `audit.get_merkle_root`, `audit.load_registered_leaves`, `audit.verify_row_against_root` werden unverändert aufgerufen; deren Fehlermeldungen werden unverändert angezeigt. Das Einzelzeilen-Urteil kommt weiterhin AUSSCHLIESSLICH von `audit.verify_row_against_root`; `audit_ext.compute_proof_steps` liefert nur die Anzeige des Pfads (Task 3 testet, dass beide identisch urteilen).

- [ ] **Step 1: `frontend/views/dataset.py` anlegen**

```python
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
        ui.empty_state(
            "Noch keine Datei ausgewählt — CSV hochladen oder Tamper-Demo aktivieren."
        )
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
```

- [ ] **Step 2: Import-Smoke-Test**

```bash
python -c "import sys; sys.path.insert(0, 'frontend'); import views.dataset; print('ok')"
```

Erwartet: `ok`.

- [ ] **Step 3: Commit**

```bash
git add frontend/views/dataset.py
git commit -m "frontend: views/dataset.py mit Ergebnis-zuerst-Layout und Proof-Pfad

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 9: `views/model.py` — Tab „Modell- & Config-Audit"

**Files:**
- Create: `frontend/views/model.py`

Semantik-Erhalt: Hash-Berechnung via `audit.sha256_bytes` (unverändert); die Meldung zur bekannten Config-Inkonsistenz erscheint weiterhin NUR bei Mismatch, Wortlaut erhalten (Umlaute korrigiert).

- [ ] **Step 1: `frontend/views/model.py` anlegen**

```python
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
```

- [ ] **Step 2: Import-Smoke-Test**

```bash
python -c "import sys; sys.path.insert(0, 'frontend'); import views.model; print('ok')"
```

Erwartet: `ok`.

- [ ] **Step 3: Commit**

```bash
git add frontend/views/model.py
git commit -m "frontend: views/model.py (Modell- und Config-Audit)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 10: `views/chain_status.py` — Tab „On-Chain-Status"

**Files:**
- Create: `frontend/views/chain_status.py`

- [ ] **Step 1: `frontend/views/chain_status.py` anlegen**

```python
"""Tab 4: On-Chain-Status — Netzwerk, Contract, Registry-Bestand."""

import streamlit as st

import chain
from ui import components as ui


def render(state: dict) -> None:
    st.header("On-Chain-Status")
    deployment = state["deployment_local"]

    col1, col2 = st.columns(2)
    with col1:
        st.metric("RPC-Knoten erreichbar", "Ja" if state["connected"] else "Nein")
        st.metric("ABI kompiliert", "Ja" if state["abi_available"] else "Nein")
    with col2:
        st.metric("Netzwerk", deployment.get("network", "—"))
        st.metric("RPC-URL", state["rpc"])

    address = state["address"] or deployment.get("contractAddress")
    st.markdown('<div class="cp-kv">Contract-Adresse</div>', unsafe_allow_html=True)
    st.markdown(
        f"<div>{ui.hash_html(address or '(unbekannt)')}</div>", unsafe_allow_html=True
    )
    with st.expander("Adresse kopieren"):
        st.code(address or "(unbekannt)", language="text")

    explorer_url = deployment.get("explorerUrl")
    if explorer_url:
        st.link_button("Contract im Explorer öffnen", explorer_url)
    else:
        st.caption("Lokales Netzwerk — kein Block-Explorer verfügbar.")

    if not state["abi_available"]:
        st.error(
            "Contract-ABI fehlt. Einmalig kompilieren (in contracts/): "
            "npm install && npx hardhat compile."
        )
    if not state["connected"] and state["error"]:
        st.error(state["error"])

    if state["connected"]:
        try:
            with st.spinner("Lese Chain-Daten…"):
                info = chain.chain_info(state["web3"])
                records = chain.list_records(state["contract"])
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

    if state["last_reg"]:
        st.subheader("Letzte Registrierung (lokal protokolliert)")
        st.dataframe(
            [{"Feld": k, "Wert": str(v)} for k, v in state["last_reg"].items()],
            hide_index=True,
            use_container_width=True,
        )
```

- [ ] **Step 2: Import-Smoke-Test**

```bash
python -c "import sys; sys.path.insert(0, 'frontend'); import views.chain_status; print('ok')"
```

Erwartet: `ok`.

- [ ] **Step 3: Commit**

```bash
git add frontend/views/chain_status.py
git commit -m "frontend: views/chain_status.py (On-Chain-Status)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 11: `app.py` ersetzen — schlanker Kompositions-Layer

**Files:**
- Modify: `frontend/app.py` (kompletter Ersatz des Inhalts)

- [ ] **Step 1: `frontend/app.py` mit exakt diesem Inhalt ERSETZEN**

```python
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
```

- [ ] **Step 2: App starten und Erreichbarkeit prüfen**

Voraussetzung: Hardhat-Node läuft und das Modell ist registriert (falls nicht, siehe Task 13 Step 1).

```bash
python -m streamlit run frontend/app.py --server.headless true --server.port 8501 &
sleep 5
curl -s -o /dev/null -w "%{http_code}" http://localhost:8501/
```

Erwartet: `200`. Danach im Browser `http://localhost:8501` öffnen: grüner Statusbalken „Chain verbunden", Sidebar mit Prüfkontext, vier Tabs rendern ohne Exception.

- [ ] **Step 3: Alle Tests erneut laufen lassen (Regression)**

```bash
python -m pytest frontend/tests -v
```

Erwartet: alle PASS.

- [ ] **Step 4: Commit**

```bash
git add frontend/app.py
git commit -m "frontend: app.py zu schlankem Kompositions-Layer umgebaut

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 12: Umlaut-Korrektur in `audit.py` und `chain.py` (nur UI-sichtbare Strings)

**Files:**
- Modify: `frontend/audit.py` (nur String-Literale in Meldungen)
- Modify: `frontend/chain.py` (nur String-Literale in Meldungen)

Nur Rechtschreibung (ue→ü usw.) — der SEMANTISCHE Inhalt jeder Meldung bleibt identisch. Keine Änderung an Logik, Signaturen oder Hash-Berechnung. Exakte Ersetzungen:

- [ ] **Step 1: `frontend/audit.py` — folgende Ersetzungen in Meldungs-Strings**

| Alt | Neu |
|---|---|
| `"Datei ist nicht UTF-8-kodiert. Wahrscheinliche Ursache: Excel-Reexport mit anderer Kodierung (ANSI/UTF-16). Bitte als 'CSV UTF-8' speichern."` | unverändert lassen (keine Umlaut-Wörter enthalten) |
| `"Die CSV-Datei enthaelt keine Zeilen."` | `"Die CSV-Datei enthält keine Zeilen."` |
| `f"Zeilenindex {row_index} liegt ausserhalb des Bereichs 0..{len(rows) - 1}."` | `f"Zeilenindex {row_index} liegt außerhalb des Bereichs 0..{len(rows) - 1}."` |
| `f"...erhalten {len(rows)}. Moegliche Ursache: falsche/abgeschnittene Datei "` | `...erhalten {len(rows)}. Mögliche Ursache: falsche/abgeschnittene Datei ` |
| `f"oder Excel-Reexport, der Zeilen hinzufuegt oder entfernt."` | `oder Excel-Reexport, der Zeilen hinzufügt oder entfernt.` |
| `"...(erwartet: {','.join(expected_header)}). Excel-Reexporte aendern "` | `...(erwartet: {','.join(expected_header)}). Excel-Reexporte ändern ` |
| `"haeufig Spaltenreihenfolge, Quoting oder Zeilenenden - dann schlaegt "` | `häufig Spaltenreihenfolge, Quoting oder Zeilenenden — dann schlägt ` |
| `"die Pruefung fehl, obwohl die Daten unveraendert sind."` | `die Prüfung fehl, obwohl die Daten unverändert sind.` |
| `"Unterschiedliche Spaltenanzahl je Zeile erkannt - evtl. Felder mit "` | `Unterschiedliche Spaltenanzahl je Zeile erkannt — evtl. Felder mit ` |

- [ ] **Step 2: `frontend/chain.py` — folgende Ersetzungen in Meldungs-Strings**

| Alt | Neu |
|---|---|
| `f"Kein Kontakt zum RPC-Knoten unter {rpc_url}. Laeuft der Hardhat-Node? "` | `f"Kein Kontakt zum RPC-Knoten unter {rpc_url}. Läuft der Hardhat-Node? "` |

(Die übrigen Meldungen in `chain.py` enthalten keine ASCII-Umlaute.)

- [ ] **Step 3: Regression — Tests und App-Smoke**

```bash
python -m pytest frontend/tests -v
python -c "import sys; sys.path.insert(0, 'frontend'); import audit, chain; print('ok')"
```

Erwartet: alle Tests PASS, `ok`.

- [ ] **Step 4: Commit**

```bash
git add frontend/audit.py frontend/chain.py
git commit -m "frontend: korrekte Umlaute in Meldungstexten (audit.py, chain.py)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 13: Manuelle Verifikation der drei Kernszenarien + beide Themes

**Files:** keine Änderungen — reiner Verifikationslauf. Gefundene Probleme werden als Fix-Commits nachgezogen.

- [ ] **Step 1: Lokale Chain bereitstellen (falls nicht bereits laufend)**

```bash
# Terminal 1 (im Repo-Root):
cd contracts && npx hardhat node

# Terminal 2 (im Repo-Root):
cd contracts && npm run deploy:local && cd ..
python backend/hash_files.py
python backend/register_model.py
```

Erwartet: `Registered model on-chain: ... "recordId": "Health-Risk-Classifier-1.0.0"` (oder „Record already exists on-chain" — beides ok).

- [ ] **Step 2: App starten**

```bash
python -m streamlit run frontend/app.py --server.headless true --server.port 8501
```

- [ ] **Step 3: Szenario A — Chain verbunden + Originaldaten → alles `verified`**

Im Browser `http://localhost:8501`:
1. Statusbalken oben ist GRÜN („Chain verbunden … Erwartete Werte werden on-chain gelesen").
2. Tab „Dataset-Audit": `data/health_dataset_1000.csv` hochladen → Verdict-Banner grün `● Verifiziert`, Vergleichskarte `dataset_merkle_root` mit Badge „Verifiziert", keine Abweichungstabelle („keine Abweichungen").
3. Einzelzeile `1 — P0001` auswählen → grünes Verdict „Verifiziert: diese Zeile gehört zum registrierten Datensatz." Proof-Pfad-Expander zeigt Ebene 0 (Blatt) + 10 Schritte + identische Roots.
4. Tab „Modell- & Config-Audit": `artifacts/model.pkl` und `artifacts/config.json` hochladen → beide Badges „Verifiziert".
5. Kein einziges ✅/❌/⚠️-Emoji irgendwo sichtbar.

- [ ] **Step 4: Szenario B — Tamper-Demo → `mismatch`, Zeile identifiziert**

1. Tab „Dataset-Audit": Toggle „Tamper-Demo" aktivieren.
2. Verdict-Banner ROT `✕ Abweichend`; in der Vergleichskarte sind die abweichenden Zeichen beider Roots rot markiert.
3. Abweichungstabelle zeigt genau 1 Zeile: Zeilenindex 1, patient_id P0001, Status „geändert", „Hochgeladen (neu)" mit age 33, „Registriert (alt)" mit age 32.
4. Filter „P0001" eingeben → Zeile bleibt; Filter „P0002" → Tabelle leer.
5. Einzelzeilen-Verifikation: JEDE Zeile der manipulierten Datei schlägt fehl (rotes Verdict) — das ist die dokumentierte Bestands-Semantik: der Proof wird aus der hochgeladenen Datei rekonstruiert, eine manipulierte Nachbarzeile verfälscht den rekonstruierten Root. NICHT „fixen". Danach Toggle aus, Original hochladen → Einzelzeile P0002 verifiziert wieder grün.

- [ ] **Step 5: Szenario C — Chain aus → Fallback, alles `unverified`**

1. Hardhat-Node (Terminal 1) stoppen, in der App „Neu laden" klicken.
2. Statusbalken AMBER („FALLBACK aktiv … NICHT on-chain verifiziert"), Expander „Details zur Verbindungsstörung" zeigt die Fehlermeldung.
3. Tab „Registry-Übersicht": Badge „Unbestätigt", Beweise als „lokaler Fallback — unbestätigt" gekennzeichnet.
4. Original-CSV hochladen → Verdict AMBER `◌ Unbestätigt` („Übereinstimmung nur mit lokalem Fallback-Wert…") — ein Match wird NICHT als Erfolg getarnt.
5. Danach Node wieder starten und Chain-Zustand wiederherstellen (Neustart leert die Chain!): `cd contracts && npm run deploy:local && cd .. && python backend/register_model.py`, dann „Neu laden" → Statusbalken wieder grün.

- [ ] **Step 6: Beide Themes prüfen (Kontrast)**

```bash
python -m streamlit run frontend/app.py --server.headless true --theme.base light
# danach erneut mit:
python -m streamlit run frontend/app.py --server.headless true --theme.base dark
```

In beiden Themes: Badges, Statusbalken, Verdicts, Hash-Diff-Markierung lesbar; lange Hashes brechen um statt zu überlaufen (Fenster schmal ziehen). Falls eine Statusfarbe zu blass/grell wirkt: NUR den Wert in `TOKENS` in `ui/theme.py` anpassen (eine Stelle) und committen.

- [ ] **Step 7: Vollständige Testsuite + Abschluss-Commit (falls Fixes anfielen)**

```bash
python -m pytest frontend/tests -v
git status
```

Erwartet: alle Tests PASS, Arbeitsbaum sauber (bzw. Fixes einzeln committet).

---

## Abnahme-Checkliste (gegen die Spezifikation)

- [ ] `app.py` ist schlanker Kompositions-Layer; Theme/Komponenten/Views getrennt
- [ ] `st.cache_resource`/`st.cache_data` für Verbindung und Reads aktiv
- [ ] Design-Tokens an einer Stelle (`ui/theme.py` TOKENS); ein Akzentton + 3 semantische Farben
- [ ] Drei-Zustand-Semantik sichtbar: verified/mismatch/unverified; Fallback-Match NIE grün
- [ ] Keine Emoji-Statusträger; Badges = Farbe + Marker-Glyphe + Text
- [ ] Hashes: Monospace, mittige Truncation wo gekürzt, Volltext + Copy (st.code), Zeichen-Diff bei Mismatch
- [ ] Persistenter Statusbalken auf allen Tabs; Sidebar mit Modell/Version/Record-ID/Contract/Netzwerk
- [ ] Dataset-Tab: Ergebnis oben; Diff-Tabelle sortierbar + filterbar + alt/neu-Kontext
- [ ] Einzelzeilen-Auswahl über patient_id; Proof als lesbarer Pfad Blatt → Root
- [ ] Upload-Zustand sichtbar (Name, Größe, Zeitpunkt) + Reset über Uploader-✕
- [ ] Spinner bei Chain-Abfragen; ruhige Leerzustände
- [ ] A11y: Status nie nur über Farbe; beide Themes geprüft; Hashes sprengen kein Layout
- [ ] Korrekte Umlaute in allen UI-Strings; Dateien UTF-8
- [ ] `backend/` und `contracts/` unverändert (`git diff --stat dev -- backend contracts` ist leer)
- [ ] Alle pytest-Tests grün
