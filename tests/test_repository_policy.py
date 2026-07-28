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

    def test_runtime_evidence_requires_verification_metadata(self):
        catalog = json.loads(
            (REPO_ROOT / "catalog/fm19.5/verified-steps.json").read_text(encoding="utf-8")
        )
        catalog["steps"][0]["evidence"].append("fm19_5_paste_verified")
        catalog["steps"][0]["missingEvidence"].remove("fm19_5_paste_verified")

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            catalog_path = root / "catalog/fm19.5/verified-steps.json"
            catalog_path.parent.mkdir(parents=True)
            catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
            errors: list[str] = []
            known_sources = {
                source["id"]
                for source in json.loads(
                    (REPO_ROOT / "sources/registry.json").read_text(encoding="utf-8")
                )["sources"]
            }
            _validate_step_catalog(root, known_sources, errors)

        self.assertTrue(any("runtime evidence requires verification metadata" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
