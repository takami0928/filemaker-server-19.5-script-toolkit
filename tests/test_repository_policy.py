from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from fms19_toolkit.repository_policy import (
    _validate_evidence,
    _validate_source_ids,
    _validate_step_catalog,
    check_repository,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


class RepositoryPolicyTests(unittest.TestCase):
    def _catalog_errors(self, mutate) -> list[str]:
        catalog = json.loads(
            (REPO_ROOT / "catalog/fm19.5/verified-steps.json").read_text(encoding="utf-8")
        )
        mutate(catalog)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            catalog_path = root / "catalog/fm19.5/verified-steps.json"
            catalog_path.parent.mkdir(parents=True)
            catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
            known_sources = {
                source["id"]
                for source in json.loads(
                    (REPO_ROOT / "sources/registry.json").read_text(encoding="utf-8")
                )["sources"]
            }
            errors: list[str] = []
            _validate_step_catalog(root, known_sources, errors)
            return errors

    def test_current_repository_passes_policy(self):
        self.assertEqual(check_repository(REPO_ROOT), [])

    def test_unknown_evidence_is_rejected(self):
        errors: list[str] = []
        _validate_evidence(["documented", "invented"], "item", errors)
        self.assertTrue(any("unknown evidence" in error for error in errors))

    def test_unknown_source_is_rejected(self):
        errors: list[str] = []
        _validate_source_ids(["missing-source"], {"known-source"}, "item", errors)
        self.assertTrue(any("unknown sourceIds" in error for error in errors))

    def test_evidence_progression_rejects_gap(self):
        def mutate(catalog):
            step = catalog["steps"][0]
            step["evidence"].remove("structure_tested")
            step["missingEvidence"].insert(0, "structure_tested")

        errors = self._catalog_errors(mutate)
        self.assertTrue(any("clipboard_payload_tested requires" in error for error in errors))

    def test_runtime_evidence_requires_verification_metadata(self):
        def mutate(catalog):
            step = catalog["steps"][0]
            step["evidence"].append("fm19_5_paste_verified")
            step["missingEvidence"].remove("fm19_5_paste_verified")

        errors = self._catalog_errors(mutate)
        self.assertTrue(any("runtime evidence requires verification object" in error for error in errors))

    def test_verification_metadata_is_validated(self):
        def mutate(catalog):
            step = catalog["steps"][0]
            step["evidence"].append("fm19_5_paste_verified")
            step["missingEvidence"].remove("fm19_5_paste_verified")
            step["verification"] = {
                "fm19_5_paste_verified": [
                    {
                        "fileMakerProVersion": "19.5.4",
                        "windowsVersion": "11",
                        "fixtureSha256": "not-a-sha256",
                        "testedAt": "2026-07-28",
                        "tester": "synthetic-test",
                    }
                ]
            }

        errors = self._catalog_errors(mutate)
        self.assertTrue(any("fixtureSha256 must be lowercase SHA-256" in error for error in errors))

    def test_supported_status_requires_paste_evidence(self):
        def mutate(catalog):
            catalog["steps"][0]["status"] = "supported"

        errors = self._catalog_errors(mutate)
        self.assertTrue(any("supported status requires fm19_5_paste_verified" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
