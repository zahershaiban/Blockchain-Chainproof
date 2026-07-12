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

    def test_unbekannte_quelle_ist_nie_verified(self):
        assert fmt.derive_status("abc", "abc", None) == fmt.UNVERIFIED
        assert fmt.derive_status("abc", "abc", "") == fmt.UNVERIFIED


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

    def test_null_bytes(self):
        assert fmt.format_bytes(0) == "0 B"

    def test_grenzwert_1023_bleibt_bytes(self):
        assert fmt.format_bytes(1023) == "1023 B"

    def test_grenzwert_1024_wird_kb(self):
        assert fmt.format_bytes(1024) == "1.0 KB"

    def test_gigabyte_obergrenze(self):
        assert fmt.format_bytes(1024**3) == "1.0 GB"
        assert fmt.format_bytes(1024**4) == "1024.0 GB"


class TestFormatTimestamp:
    def test_unix_sekunden_utc(self):
        assert fmt.format_timestamp(0) == "1970-01-01 00:00:00 UTC"

    def test_ungueltiger_wert_wird_string(self):
        assert fmt.format_timestamp("kein-timestamp") == "kein-timestamp"
        assert fmt.format_timestamp(None) == "None"
