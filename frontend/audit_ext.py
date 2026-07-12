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
