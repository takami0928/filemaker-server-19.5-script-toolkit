from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from fms19_toolkit.repository_policy import (
    COPILOT_REQUIRED_PATHS,
    COPILOT_SOURCE_REQUIRED_FILES,
    _validate_copilot_package,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


class CopilotPackagePolicyTests(unittest.TestCase):
    def _minimal_compatibility_data(self) -> dict:
        return {
            "steps": [
                {
                    "name": "Set Variable",
                    "execution": {"client": "available", "psos": "available"},
                },
                {
                    "name": "Set Error Capture",
                    "execution": {"client": "available", "psos": "partial"},
                },
                {
                    "name": "If",
                    "execution": {"client": "available", "psos": "available"},
                },
                {
                    "name": "Unavailable Example",
                    "execution": {"client": "unavailable", "psos": "unavailable"},
                },
                {
                    "name": "Unknown Example",
                    "execution": {"client": "unknown", "psos": "unknown"},
                },
            ]
        }

    def _write_minimal_package(self, root: Path) -> None:
        for relative in COPILOT_REQUIRED_PATHS:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# Synthetic fixture\n", encoding="utf-8")

        (root / "docs/copilot/README.md").write_text(
            "# Package\n\n"
            "Knowledge package version: 0.1.0\n"
            "Target: FileMaker Pro 19.5 / FileMaker Server 19.5\n\n"
            "[Scope](00-purpose-and-scope.md)\n",
            encoding="utf-8",
        )
        for relative in COPILOT_SOURCE_REQUIRED_FILES:
            (root / relative).write_text(
                "# Source-backed document\n\n"
                "## Source IDs\n\n"
                "Source IDs: `known-source`\n",
                encoding="utf-8",
            )
        (root / "docs/copilot/09-output-contract.md").write_text(
            "# Output\n\n"
            "Design status:\n"
            "XML output:\n"
            "Automated checks:\n"
            "Paste verification:\n"
            "Client runtime verification:\n"
            "FMSE verification:\n",
            encoding="utf-8",
        )
        (root / "docs/copilot/examples/synthetic-complete-design.md").write_text(
            "# Example\n\n"
            "## FileMaker-format script steps\n\n"
            "### SYN_Test — `client`\n\n"
            "1. `Set Variable` [ `$value` ; Value: `1` ]\n\n"
            "## Compatibility ledger\n\n"
            "| Step | Context | Catalog support | Resolved condition |\n"
            "| --- | --- | --- | --- |\n"
            "| Set Variable | client | available | — |\n",
            encoding="utf-8",
        )

    def _fixture_errors(self, mutate=None) -> list[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_minimal_package(root)
            compatibility_data = self._minimal_compatibility_data()
            if mutate is not None:
                mutate(root, compatibility_data)
            errors: list[str] = []
            _validate_copilot_package(
                root, {"known-source"}, compatibility_data, errors
            )
            return errors

    def test_current_package_passes(self):
        implementation_sources = {
            source["id"]
            for source in json.loads(
                (REPO_ROOT / "sources/registry.json").read_text(encoding="utf-8")
            )["sources"]
        }
        compatibility_sources = {
            source["id"]
            for source in json.loads(
                (
                    REPO_ROOT
                    / "catalog/fm19.5/compatibility/sources.json"
                ).read_text(encoding="utf-8")
            )["sources"]
        }
        compatibility_data = json.loads(
            (
                REPO_ROOT / "catalog/fm19.5/compatibility/script-steps.json"
            ).read_text(encoding="utf-8")
        )
        errors: list[str] = []
        _validate_copilot_package(
            REPO_ROOT,
            implementation_sources | compatibility_sources,
            compatibility_data,
            errors,
        )
        self.assertEqual(errors, [])

    def test_required_file_missing(self):
        def mutate(root, _):
            (root / "docs/copilot/10-human-review-and-testing.md").unlink()

        errors = self._fixture_errors(mutate)
        self.assertTrue(
            any("missing required Copilot package file" in error for error in errors)
        )

    def test_broken_relative_link(self):
        def mutate(root, _):
            path = root / "docs/copilot/README.md"
            path.write_text(
                path.read_text(encoding="utf-8") + "\n[Missing](missing.md)\n",
                encoding="utf-8",
            )

        errors = self._fixture_errors(mutate)
        self.assertTrue(any("broken relative link" in error for error in errors))

    def test_source_id_missing(self):
        def mutate(root, _):
            (root / COPILOT_SOURCE_REQUIRED_FILES[0]).write_text(
                "# Missing source section\n", encoding="utf-8"
            )

        errors = self._fixture_errors(mutate)
        self.assertTrue(any("missing ## Source IDs" in error for error in errors))

    def test_unknown_source_id(self):
        def mutate(root, _):
            path = root / COPILOT_SOURCE_REQUIRED_FILES[0]
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "`known-source`", "`unknown-source`"
                ),
                encoding="utf-8",
            )

        errors = self._fixture_errors(mutate)
        self.assertTrue(any("unknown Source IDs" in error for error in errors))

    def test_duplicate_source_id(self):
        def mutate(root, _):
            path = root / COPILOT_SOURCE_REQUIRED_FILES[0]
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "`known-source`", "`known-source`, `known-source`"
                ),
                encoding="utf-8",
            )

        errors = self._fixture_errors(mutate)
        self.assertTrue(any("duplicate Source IDs" in error for error in errors))

    def test_unknown_step(self):
        def mutate(root, _):
            path = root / "docs/copilot/examples/synthetic-complete-design.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "Set Variable", "Invented Step"
                ),
                encoding="utf-8",
            )

        errors = self._fixture_errors(mutate)
        self.assertTrue(any("unknown step" in error for error in errors))

    def test_unknown_context(self):
        def mutate(root, _):
            path = root / "docs/copilot/examples/synthetic-complete-design.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace("client", "desktop"),
                encoding="utf-8",
            )

        errors = self._fixture_errors(mutate)
        self.assertTrue(any("unknown context" in error for error in errors))

    def test_catalog_support_mismatch(self):
        def mutate(root, _):
            path = root / "docs/copilot/examples/synthetic-complete-design.md"
            text = path.read_text(encoding="utf-8").replace(
                "| Set Variable | client | available | — |",
                "| Set Variable | client | partial | resolved |",
            )
            path.write_text(text, encoding="utf-8")

        errors = self._fixture_errors(mutate)
        self.assertTrue(
            any("catalog support mismatch" in error for error in errors)
        )

    def test_unavailable_step_rejected(self):
        def mutate(root, _):
            path = root / "docs/copilot/examples/synthetic-complete-design.md"
            text = path.read_text(encoding="utf-8")
            text = text.replace("Set Variable", "Unavailable Example")
            text = text.replace("| client | available |", "| client | unavailable |")
            path.write_text(text, encoding="utf-8")

        errors = self._fixture_errors(mutate)
        self.assertTrue(
            any("rejected support unavailable" in error for error in errors)
        )

    def test_unknown_support_rejected(self):
        def mutate(root, _):
            path = root / "docs/copilot/examples/synthetic-complete-design.md"
            text = path.read_text(encoding="utf-8")
            text = text.replace("Set Variable", "Unknown Example")
            text = text.replace("| client | available |", "| client | unknown |")
            path.write_text(text, encoding="utf-8")

        errors = self._fixture_errors(mutate)
        self.assertTrue(any("rejected support unknown" in error for error in errors))

    def test_partial_without_resolved_condition_rejected(self):
        def mutate(root, _):
            path = root / "docs/copilot/examples/synthetic-complete-design.md"
            text = path.read_text(encoding="utf-8")
            text = text.replace("Set Variable", "Set Error Capture")
            text = text.replace("`client`", "`psos`")
            text = text.replace(
                "| client | available | — |", "| psos | partial | — |"
            )
            path.write_text(text, encoding="utf-8")

        errors = self._fixture_errors(mutate)
        self.assertTrue(
            any("partial support requires" in error for error in errors)
        )

    def test_script_step_missing_from_compatibility_ledger(self):
        def mutate(root, _):
            path = root / "docs/copilot/examples/synthetic-complete-design.md"
            text = path.read_text(encoding="utf-8").replace(
                "1. `Set Variable` [ `$value` ; Value: `1` ]",
                "1. `Set Variable` [ `$value` ; Value: `1` ]\n"
                "2. `If` [ `$value = 1` ]",
            )
            path.write_text(text, encoding="utf-8")

        errors = self._fixture_errors(mutate)
        self.assertTrue(
            any("missing from Compatibility ledger" in error for error in errors)
        )


if __name__ == "__main__":
    unittest.main()
