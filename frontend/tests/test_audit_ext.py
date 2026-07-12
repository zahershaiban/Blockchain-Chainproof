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
