from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from fms19_toolkit.repository_policy import (
    COPILOT_REQUIRED_PATHS,
    COPILOT_SOURCE_REQUIRED_FILES,
    _collect_copilot_source_ids,
    _validate_copilot_package,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


class CopilotPackagePolicyTests(unittest.TestCase):
    README_PATH = Path("docs/copilot/README.md")
    OUTPUT_CONTRACT_PATH = Path("docs/copilot/09-output-contract.md")
    EXAMPLE_PATH = Path("docs/copilot/examples/synthetic-complete-design.md")
    VALID_STEP_LINE = "1. `Set Variable` [ `$value` ; Value: `1` ]"
    VALID_LEDGER_ROW = "| Set Variable | client | available | — |"

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

    def _replace_example(self, root: Path, old: str, new: str) -> None:
        path = root / self.EXAMPLE_PATH
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text)
        path.write_text(text.replace(old, new), encoding="utf-8")

    def _write_collision_registries(
        self, root: Path, compatibility_url: str, implementation_url: str
    ) -> None:
        compatibility_path = (
            root / "catalog/fm19.5/compatibility/sources.json"
        )
        implementation_path = root / "sources/registry.json"
        compatibility_path.parent.mkdir(parents=True, exist_ok=True)
        implementation_path.parent.mkdir(parents=True, exist_ok=True)
        compatibility_path.write_text(
            json.dumps(
                {
                    "sources": [
                        {"id": "shared-source", "url": compatibility_url}
                    ]
                }
            ),
            encoding="utf-8",
        )
        implementation_path.write_text(
            json.dumps(
                {
                    "sources": [
                        {"id": "shared-source", "url": implementation_url}
                    ]
                }
            ),
            encoding="utf-8",
        )

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

    def test_package_version_missing(self):
        def mutate(root, _):
            path = root / self.README_PATH
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "Knowledge package version: 0.1.0\n", ""
                ),
                encoding="utf-8",
            )

        errors = self._fixture_errors(mutate)
        self.assertIn(
            "docs/copilot/README.md: package version must be 0.1.0", errors
        )

    def test_target_19_5_missing(self):
        def mutate(root, _):
            path = root / self.README_PATH
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "Target: FileMaker Pro 19.5 / FileMaker Server 19.5\n", ""
                ),
                encoding="utf-8",
            )

        errors = self._fixture_errors(mutate)
        self.assertIn(
            "docs/copilot/README.md: target must be "
            "FileMaker Pro 19.5 / FileMaker Server 19.5",
            errors,
        )

    def test_each_completion_dimension_missing(self):
        dimensions = (
            "Design status",
            "XML output",
            "Automated checks",
            "Paste verification",
            "Client runtime verification",
            "FMSE verification",
        )
        for dimension in dimensions:
            with self.subTest(dimension=dimension):
                def mutate(root, _, missing=dimension):
                    path = root / self.OUTPUT_CONTRACT_PATH
                    path.write_text(
                        path.read_text(encoding="utf-8").replace(
                            f"{missing}:\n", ""
                        ),
                        encoding="utf-8",
                    )

                errors = self._fixture_errors(mutate)
                self.assertIn(
                    "docs/copilot/09-output-contract.md: missing completion "
                    f"dimension: {dimension}",
                    errors,
                )

    def test_required_file_missing(self):
        def mutate(root, _):
            (root / "docs/copilot/10-human-review-and-testing.md").unlink()

        errors = self._fixture_errors(mutate)
        self.assertIn(
            "missing required Copilot package file: "
            "docs/copilot/10-human-review-and-testing.md",
            errors,
        )

    def test_broken_relative_link(self):
        def mutate(root, _):
            path = root / "docs/copilot/README.md"
            path.write_text(
                path.read_text(encoding="utf-8") + "\n[Missing](missing.md)\n",
                encoding="utf-8",
            )

        errors = self._fixture_errors(mutate)
        self.assertIn(
            f"{self.README_PATH}: broken relative link: missing.md", errors
        )

    def test_relative_link_cannot_escape_repository(self):
        def mutate(root, _):
            path = root / self.README_PATH
            path.write_text(
                path.read_text(encoding="utf-8")
                + "\n[Escape](../../../outside.md)\n",
                encoding="utf-8",
            )

        errors = self._fixture_errors(mutate)
        self.assertIn(
            f"{self.README_PATH}: relative link escapes repository: "
            "../../../outside.md",
            errors,
        )

    def test_invalid_utf_8_markdown_rejected(self):
        def mutate(root, _):
            (root / "docs/copilot/00-purpose-and-scope.md").write_bytes(
                b"\xff\xfe"
            )

        errors = self._fixture_errors(mutate)
        self.assertTrue(
            any(
                "docs\\copilot\\00-purpose-and-scope.md: "
                "Copilot Markdown must be valid UTF-8:" in error
                or "docs/copilot/00-purpose-and-scope.md: "
                "Copilot Markdown must be valid UTF-8:" in error
                for error in errors
            ),
            errors,
        )

    def test_source_id_missing(self):
        def mutate(root, _):
            (root / COPILOT_SOURCE_REQUIRED_FILES[0]).write_text(
                "# Missing source section\n", encoding="utf-8"
            )

        errors = self._fixture_errors(mutate)
        self.assertIn(
            f"{COPILOT_SOURCE_REQUIRED_FILES[0]}: missing ## Source IDs section",
            errors,
        )

    def test_multiple_source_id_lines_rejected(self):
        def mutate(root, _):
            path = root / COPILOT_SOURCE_REQUIRED_FILES[0]
            path.write_text(
                path.read_text(encoding="utf-8")
                + "\nSource IDs: `known-source`\n",
                encoding="utf-8",
            )

        errors = self._fixture_errors(mutate)
        self.assertIn(
            f"{COPILOT_SOURCE_REQUIRED_FILES[0]}: "
            "requires exactly one Source IDs: line",
            errors,
        )

    def test_empty_source_id_payload_rejected(self):
        def mutate(root, _):
            path = root / COPILOT_SOURCE_REQUIRED_FILES[0]
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "Source IDs: `known-source`", "Source IDs:"
                ),
                encoding="utf-8",
            )

        errors = self._fixture_errors(mutate)
        self.assertIn(
            f"{COPILOT_SOURCE_REQUIRED_FILES[0]}: "
            "Source IDs must not be empty",
            errors,
        )

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
        self.assertIn(
            f"{COPILOT_SOURCE_REQUIRED_FILES[0]}: "
            "unknown Source IDs: ['unknown-source']",
            errors,
        )

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
        self.assertIn(
            f"{COPILOT_SOURCE_REQUIRED_FILES[0]}: "
            "duplicate Source IDs are not allowed",
            errors,
        )

    def test_source_id_collision_with_different_urls_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_collision_registries(
                root,
                "https://example.test/compatibility",
                "https://example.test/implementation",
            )
            errors: list[str] = []
            _collect_copilot_source_ids(root, {"shared-source"}, errors)

        self.assertIn(
            "Copilot source ID collision: shared-source maps to "
            "'https://example.test/compatibility' and "
            "'https://example.test/implementation'",
            errors,
        )

    def test_source_id_collision_with_same_url_allowed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            shared_url = "https://example.test/shared"
            self._write_collision_registries(root, shared_url, shared_url)
            errors: list[str] = []
            source_ids = _collect_copilot_source_ids(
                root, {"shared-source"}, errors
            )

        self.assertEqual(errors, [])
        self.assertEqual(source_ids, {"shared-source"})

    def test_compatibility_ledger_section_missing(self):
        def mutate(root, _):
            self._replace_example(
                root, "## Compatibility ledger", "## Compatibility matrix"
            )

        errors = self._fixture_errors(mutate)
        self.assertIn(
            "docs/copilot/examples/synthetic-complete-design.md: "
            "missing ## Compatibility ledger",
            errors,
        )

    def test_compatibility_ledger_canonical_header_missing(self):
        def mutate(root, _):
            self._replace_example(
                root,
                "| Step | Context | Catalog support | Resolved condition |",
                "| Script step | Context | Catalog support | Resolved condition |",
            )

        errors = self._fixture_errors(mutate)
        self.assertIn(
            "Copilot Compatibility ledger: missing canonical table header",
            errors,
        )

    def test_compatibility_ledger_malformed_row_rejected(self):
        malformed_row = "| Set Variable | client |"

        def mutate(root, _):
            self._replace_example(
                root,
                "| --- | --- | --- | --- |",
                f"| --- | --- | --- | --- |\n{malformed_row}",
            )

        errors = self._fixture_errors(mutate)
        self.assertIn(
            f"Copilot Compatibility ledger: malformed row: {malformed_row}",
            errors,
        )

    def test_compatibility_ledger_duplicate_pair_rejected(self):
        def mutate(root, _):
            self._replace_example(
                root,
                self.VALID_LEDGER_ROW,
                f"{self.VALID_LEDGER_ROW}\n{self.VALID_LEDGER_ROW}",
            )

        errors = self._fixture_errors(mutate)
        self.assertIn(
            "Copilot Compatibility ledger: duplicate step/context: "
            "Set Variable / client",
            errors,
        )

    def test_compatibility_ledger_requires_a_row(self):
        def mutate(root, _):
            self._replace_example(root, f"{self.VALID_LEDGER_ROW}\n", "")

        errors = self._fixture_errors(mutate)
        self.assertIn(
            "Copilot Compatibility ledger: must contain at least one row",
            errors,
        )

    def test_compatibility_ledger_unknown_step_branch(self):
        def mutate(root, _):
            self._replace_example(
                root,
                self.VALID_LEDGER_ROW,
                "| Invented Step | client | available | — |",
            )

        errors = self._fixture_errors(mutate)
        self.assertIn(
            "Copilot Compatibility ledger: unknown step: Invented Step", errors
        )

    def test_compatibility_ledger_unknown_context_branch(self):
        def mutate(root, _):
            self._replace_example(
                root,
                self.VALID_LEDGER_ROW,
                "| Set Variable | desktop | available | — |",
            )

        errors = self._fixture_errors(mutate)
        self.assertIn(
            "Copilot Compatibility ledger: unknown context: desktop", errors
        )

    def test_compatibility_ledger_support_mismatch_branch(self):
        def mutate(root, _):
            self._replace_example(
                root,
                self.VALID_LEDGER_ROW,
                "| Set Variable | client | partial | resolved |",
            )

        errors = self._fixture_errors(mutate)
        self.assertIn(
            "Copilot Compatibility ledger: catalog support mismatch for "
            "Set Variable / client: expected available, got partial",
            errors,
        )

    def test_compatibility_ledger_unavailable_support_branch(self):
        def mutate(root, _):
            self._replace_example(
                root,
                self.VALID_LEDGER_ROW,
                "| Unavailable Example | client | unavailable | — |",
            )

        errors = self._fixture_errors(mutate)
        self.assertIn(
            "Copilot Compatibility ledger: "
            "Unavailable Example / client has rejected support unavailable",
            errors,
        )

    def test_compatibility_ledger_unknown_support_branch(self):
        def mutate(root, _):
            self._replace_example(
                root,
                self.VALID_LEDGER_ROW,
                "| Unknown Example | client | unknown | — |",
            )

        errors = self._fixture_errors(mutate)
        self.assertIn(
            "Copilot Compatibility ledger: "
            "Unknown Example / client has rejected support unknown",
            errors,
        )

    def test_compatibility_ledger_partial_condition_branch(self):
        def mutate(root, _):
            self._replace_example(
                root,
                self.VALID_LEDGER_ROW,
                "| Set Error Capture | psos | partial | — |",
            )

        errors = self._fixture_errors(mutate)
        self.assertIn(
            "Copilot Compatibility ledger: partial support requires a "
            "resolved condition for Set Error Capture / psos",
            errors,
        )

    def test_script_steps_section_missing(self):
        def mutate(root, _):
            self._replace_example(
                root,
                "## FileMaker-format script steps",
                "## FileMaker script implementation",
            )

        errors = self._fixture_errors(mutate)
        self.assertIn(
            "docs/copilot/examples/synthetic-complete-design.md: "
            "missing ## FileMaker-format script steps",
            errors,
        )

    def test_script_step_list_requires_a_step(self):
        def mutate(root, _):
            self._replace_example(root, f"{self.VALID_STEP_LINE}\n", "")

        errors = self._fixture_errors(mutate)
        self.assertIn("Copilot script steps: no FileMaker steps found", errors)

    def test_script_step_requires_preceding_context_heading(self):
        def mutate(root, _):
            self._replace_example(
                root,
                "## FileMaker-format script steps\n\n",
                "## FileMaker-format script steps\n\n"
                f"{self.VALID_STEP_LINE}\n\n",
            )

        errors = self._fixture_errors(mutate)
        self.assertIn(
            "Copilot script steps: step has no context heading: Set Variable",
            errors,
        )

    def test_script_step_context_heading_must_be_canonical(self):
        def mutate(root, _):
            self._replace_example(
                root, "### SYN_Test — `client`", "### SYN_Test — `desktop`"
            )

        errors = self._fixture_errors(mutate)
        self.assertIn(
            "Copilot script steps: unknown context heading: desktop", errors
        )

    def test_script_step_must_exist_in_catalog(self):
        def mutate(root, _):
            self._replace_example(
                root,
                self.VALID_STEP_LINE,
                "1. `Invented Step` [ `$value` ; Value: `1` ]",
            )

        errors = self._fixture_errors(mutate)
        self.assertIn("Copilot script steps: unknown step: Invented Step", errors)

    def test_script_step_ledger_mapping_branch(self):
        def mutate(root, _):
            self._replace_example(
                root,
                self.VALID_STEP_LINE,
                f"{self.VALID_STEP_LINE}\n2. `If` [ `$value = 1` ]",
            )

        errors = self._fixture_errors(mutate)
        self.assertIn(
            "Copilot script steps: missing from Compatibility ledger: "
            "[('If', 'client')]",
            errors,
        )


if __name__ == "__main__":
    unittest.main()
