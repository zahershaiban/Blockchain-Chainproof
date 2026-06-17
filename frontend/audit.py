"""ChainProof Audit-Logik: Hashing, Merkle-Berechnung und Datei-Sanity-Checks.

Diese Funktionen MUESSEN byte-identisch zur Backend-Logik rechnen (backend/
merkle_tree.py + backend/hash_files.py), sonst stimmen die Roots nicht ueberein.
Deshalb werden die Merkle-Funktionen direkt aus backend/merkle_tree.py importiert
statt sie hier neu zu schreiben.
"""

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

# Projektpfade.
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
ORIGINAL_DATASET = BASE_DIR / "data" / "health_dataset_1000.csv"
MERKLE_PATH = ARTIFACTS_DIR / "dataset_merkle.json"

# backend/ in den Importpfad legen, damit die ORIGINAL-Merkle-Logik genutzt wird.
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

# Exakt dieselbe Implementierung wie im Backend (gleiche Hash-/Serialisierung).
from merkle_tree import (  # noqa: E402
    sha256,
    get_merkle_root,
    generate_merkle_proof,
    verify_merkle_proof,
)


class AuditError(Exception):
    """Fehler bei der Datei-Pruefung mit handlungsleitender Meldung."""


def sha256_bytes(data: bytes) -> str:
    """SHA-256 ueber die rohen Dateibytes (wie backend/hash_files.sha256_file)."""
    if not data:
        raise AuditError("Die Datei ist leer.")
    return hashlib.sha256(data).hexdigest()


def load_csv_rows_from_bytes(data: bytes) -> list[str]:
    """Dekodiert CSV-Bytes und serialisiert jede Zeile als ','-getrennten String.

    Identisch zum Backend: csv.reader(...) + ','.join(row). Kopfzeile ist Blatt 0.
    """
    if not data:
        raise AuditError("Die hochgeladene Datei ist leer.")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AuditError(
            "Datei ist nicht UTF-8-kodiert. Wahrscheinliche Ursache: Excel-Reexport "
            "mit anderer Kodierung (ANSI/UTF-16). Bitte als 'CSV UTF-8' speichern."
        ) from exc
    rows = [",".join(row) for row in csv.reader(io.StringIO(text))]
    if not rows:
        raise AuditError("Die CSV-Datei enthaelt keine Zeilen.")
    return rows


def dataset_root_from_bytes(data: bytes) -> str:
    """Berechnet den Merkle-Root einer kompletten CSV-Datei aus ihren Bytes."""
    return get_merkle_root(load_csv_rows_from_bytes(data))


def verify_row_against_root(rows: list[str], row_index: int, root: str):
    """Verifiziert eine Einzelzeile per Merkle-Proof gegen den (on-chain-)Root.

    Nutzt die vorhandene Backend-Logik: Proof aus den Zeilen erzeugen und gegen
    den vertrauenswuerdigen Root pruefen. Stimmt eine beliebige Zeile der Datei
    nicht, weicht der rekonstruierte Root ab und die Pruefung schlaegt fehl.
    Gibt (row, proof, is_valid) zurueck.
    """
    if row_index < 0 or row_index >= len(rows):
        raise AuditError(
            f"Zeilenindex {row_index} liegt ausserhalb des Bereichs 0..{len(rows) - 1}."
        )
    row = rows[row_index]
    proof = generate_merkle_proof(rows, row_index)
    is_valid = verify_merkle_proof(row, proof, root)
    return row, proof, is_valid


def load_registered_leaves(expected_root: str | None = None):
    """Laedt registrierte Blatt-Hashes aus artifacts/dataset_merkle.json.

    Nur vertrauenswuerdig, wenn der gespeicherte Root mit dem on-chain-Root
    uebereinstimmt. Gibt (leaves, root) zurueck oder None, wenn nicht verfuegbar
    bzw. inkonsistent.
    """
    if not MERKLE_PATH.exists():
        return None
    try:
        data = json.loads(MERKLE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    leaves = data.get("leaves")
    root = data.get("merkle_root")
    if not leaves or not root:
        return None
    if expected_root and root.lower() != expected_root.lower():
        return None
    return leaves, root


def diff_rows_against_leaves(rows: list[str], registered_leaves: list[str]) -> list[dict]:
    """Vergleicht hochgeladene Zeilen mit den registrierten Blatt-Hashes.

    Gibt fuer jede abweichende Zeile {index, patient_id, uploaded, registered}
    zurueck (patient_id = erste Spalte = echter Inhalt, nicht nur der Index).
    """
    diffs = []
    total = max(len(rows), len(registered_leaves))
    for i in range(total):
        uploaded_leaf = sha256(rows[i]) if i < len(rows) else None
        registered_leaf = registered_leaves[i] if i < len(registered_leaves) else None
        if uploaded_leaf != registered_leaf:
            patient_id = rows[i].split(",")[0] if i < len(rows) else "(Zeile fehlt)"
            diffs.append({
                "index": i,
                "patient_id": patient_id,
                "uploaded": uploaded_leaf,
                "registered": registered_leaf,
            })
    return diffs


def _expected_header_and_count():
    """Liest Referenz-Header und erwartete Zeilenzahl aus lokalen Originaldaten.

    Reine Format-Heuristik fuer bessere Fehlererklaerungen (KEIN Vertrauensanker).
    """
    header = None
    count = None
    if ORIGINAL_DATASET.exists():
        with open(ORIGINAL_DATASET, "r", encoding="utf-8") as file:
            reference = list(csv.reader(file))
        if reference:
            header = reference[0]
            count = len(reference)
    elif MERKLE_PATH.exists():
        try:
            data = json.loads(MERKLE_PATH.read_text(encoding="utf-8"))
            count = data.get("leaf_count")
        except (json.JSONDecodeError, OSError):
            pass
    return header, count


def sanity_check(rows: list[str]):
    """Plausibilitaetspruefung der hochgeladenen Datei. Gibt (ok, messages)."""
    messages = []
    expected_header, expected_count = _expected_header_and_count()

    if expected_count is not None and len(rows) != expected_count:
        messages.append(
            f"Zeilenzahl weicht ab: erwartet {expected_count} (inkl. Kopfzeile), "
            f"erhalten {len(rows)}. Moegliche Ursache: falsche/abgeschnittene Datei "
            f"oder Excel-Reexport, der Zeilen hinzufuegt oder entfernt."
        )

    if expected_header is not None and rows:
        uploaded_header = rows[0].split(",")
        if uploaded_header != expected_header:
            messages.append(
                "Kopfzeile/Spalten weichen vom registrierten Datensatz ab "
                f"(erwartet: {','.join(expected_header)}). Excel-Reexporte aendern "
                "haeufig Spaltenreihenfolge, Quoting oder Zeilenenden - dann schlaegt "
                "die Pruefung fehl, obwohl die Daten unveraendert sind."
            )

    if rows:
        widths = {len(row.split(",")) for row in rows}
        if len(widths) > 1:
            messages.append(
                "Unterschiedliche Spaltenanzahl je Zeile erkannt - evtl. Felder mit "
                "Kommas/Quoting, die beim Reexport anders kodiert wurden."
            )

    return (len(messages) == 0), messages
