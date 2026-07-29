from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from fms19_toolkit.compatibility import derive_renderer_metadata
from fms19_toolkit.pattern_policy import (
    EXPECTED_PATTERN_IDS,
    _validate_pattern_documents,
    validate_practical_patterns,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PATTERN_ROOT = REPO_ROOT / "patterns/fm19.5"


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class PracticalPatternPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        index = _load_json(PATTERN_ROOT / "index.json")
        cls.documents = {
            "index": index,
            "patterns": {
                entry["path"]: _load_json(PATTERN_ROOT / entry["path"])
                for entry in index["patterns"]
            },
            "result_schema": _load_json(
                PATTERN_ROOT / "common-result.schema.json"
            ),
            "compatibility_catalog": _load_json(
                REPO_ROOT
                / "catalog/fm19.5/compatibility/script-steps.json"
            ),
            "compatibility_sources": _load_json(
                REPO_ROOT / "catalog/fm19.5/compatibility/sources.json"
            ),
            "verified_catalog": _load_json(
                REPO_ROOT / "catalog/fm19.5/verified-steps.json"
            ),
            "research_catalog": _load_json(
                REPO_ROOT
                / "research/issue-7/candidates/"
                "script-step-catalog-candidates.json"
            ),
            "implementation_sources": _load_json(
                REPO_ROOT / "sources/registry.json"
            ),
        }

    @staticmethod
    def _pattern(documents, pattern_id):
        return documents["patterns"][f"{pattern_id}/pattern.json"]

    def _errors(self, mutate) -> list[str]:
        documents = deepcopy(self.documents)
        mutate(documents)
        errors: list[str] = []
        _validate_pattern_documents(
            documents["index"],
            documents["patterns"],
            documents["result_schema"],
            documents["compatibility_catalog"],
            documents["compatibility_sources"],
            documents["verified_catalog"],
            documents["research_catalog"],
            documents["implementation_sources"],
            errors,
        )
        return errors

    def test_five_patterns_load_and_pass_policy(self):
        self.assertEqual(validate_practical_patterns(REPO_ROOT), [])
        self.assertEqual(
            set(EXPECTED_PATTERN_IDS),
            {
                pattern["id"]
                for pattern in self.documents["patterns"].values()
            },
        )

    def test_index_matches_real_pattern_files(self):
        indexed = {
            entry["path"] for entry in self.documents["index"]["patterns"]
        }
        discovered = {
            path.relative_to(PATTERN_ROOT).as_posix()
            for path in PATTERN_ROOT.glob("*/pattern.json")
        }
        self.assertEqual(indexed, discovered)

    def test_all_patterns_target_filemaker_19_5(self):
        expected = {
            "fileMakerPro": "19.5",
            "fileMakerServer": "19.5",
        }
        self.assertTrue(
            all(
                pattern["target"] == expected
                for pattern in self.documents["patterns"].values()
            )
        )

    def test_all_patterns_remain_design_only(self):
        self.assertEqual(
            self.documents["index"]["verificationStatus"],
            "design_only",
        )
        self.assertTrue(
            all(
                pattern["verificationStatus"] == "design_only"
                for pattern in self.documents["patterns"].values()
            )
        )

    def test_all_step_references_exist_in_compatibility_catalog(self):
        known = {
            step["name"]
            for step in self.documents["compatibility_catalog"]["steps"]
        }
        self.assertTrue(
            all(
                step["name"] in known
                for pattern in self.documents["patterns"].values()
                for step in pattern["steps"]
            )
        )

    def test_context_compatibility_matches_catalog(self):
        catalog = {
            step["name"]: step
            for step in self.documents["compatibility_catalog"]["steps"]
        }
        for pattern in self.documents["patterns"].values():
            for step in pattern["steps"]:
                for context in step["requiredContexts"]:
                    self.assertEqual(
                        step["compatibility"][context],
                        catalog[step["name"]]["execution"][context],
                    )

    def test_renderer_status_is_derived_from_existing_catalog(self):
        verified = self.documents["verified_catalog"]
        for pattern in self.documents["patterns"].values():
            for step in pattern["steps"]:
                self.assertEqual(
                    step["rendererStatus"],
                    derive_renderer_metadata(
                        step["name"],
                        verified,
                    )["rendererStatus"],
                )

    def test_every_source_id_is_registered(self):
        registered = {
            source["id"]
            for source in self.documents["compatibility_sources"]["sources"]
        } | {
            source["id"]
            for source in self.documents["implementation_sources"]["sources"]
        }
        for pattern in self.documents["patterns"].values():
            self.assertTrue(set(pattern["sourceIds"]).issubset(registered))

    def test_required_placeholders_fail_closed(self):
        for pattern in self.documents["patterns"].values():
            for placeholder in pattern["placeholders"]:
                if placeholder["required"]:
                    self.assertEqual(
                        placeholder["unresolvedBehavior"],
                        "block_generation",
                    )

    def test_json_examples_are_parseable(self):
        for pattern in self.documents["patterns"].values():
            for value in pattern["examples"].values():
                self.assertIsNotNone(json.loads(value))

    def test_unregistered_step_is_rejected(self):
        def mutate(documents):
            pattern = self._pattern(
                documents,
                "json-parameter-validation",
            )
            pattern["steps"][0]["name"] = "Imagined Company Step"

        errors = self._errors(mutate)
        self.assertTrue(
            any("unregistered script step" in error for error in errors)
        )

    def test_unavailable_context_is_rejected(self):
        def mutate(documents):
            pattern = self._pattern(
                documents,
                "find-one-by-primary-key",
            )
            pattern_step = next(
                step for step in pattern["steps"] if step["name"] == "Set Field"
            )
            pattern_step["compatibility"]["psos"] = "unavailable"
            catalog_step = next(
                step
                for step in documents["compatibility_catalog"]["steps"]
                if step["name"] == "Set Field"
            )
            catalog_step["execution"]["psos"] = "unavailable"

        errors = self._errors(mutate)
        self.assertTrue(
            any("unavailable context" in error for error in errors)
        )

    def test_unknown_context_is_not_treated_as_supported(self):
        def mutate(documents):
            pattern = self._pattern(
                documents,
                "find-one-by-primary-key",
            )
            pattern_step = next(
                step for step in pattern["steps"] if step["name"] == "Set Field"
            )
            pattern_step["compatibility"]["psos"] = "unknown"
            catalog_step = next(
                step
                for step in documents["compatibility_catalog"]["steps"]
                if step["name"] == "Set Field"
            )
            catalog_step["execution"]["psos"] = "unknown"

        errors = self._errors(mutate)
        self.assertTrue(
            any("unknown context" in error for error in errors)
        )

    def test_partial_context_without_condition_is_rejected(self):
        def mutate(documents):
            pattern = self._pattern(
                documents,
                "find-one-by-primary-key",
            )
            step = next(
                item
                for item in pattern["steps"]
                if item["name"] == "Go to Layout"
            )
            del step["partialConditions"]["psos"]

        errors = self._errors(mutate)
        self.assertTrue(
            any("partial context" in error for error in errors)
        )

    def test_unregistered_source_id_is_rejected(self):
        def mutate(documents):
            pattern = self._pattern(documents, "create-record")
            pattern["sourceIds"].append("unregistered-pattern-source")

        errors = self._errors(mutate)
        self.assertTrue(
            any("unregistered source ID" in error for error in errors)
        )

    def test_required_placeholder_cannot_continue_with_guess(self):
        def mutate(documents):
            pattern = self._pattern(documents, "create-record")
            pattern["placeholders"][0][
                "unresolvedBehavior"
            ] = "continue_with_guess"

        errors = self._errors(mutate)
        self.assertTrue(
            any(
                "required placeholder must use block_generation" in error
                for error in errors
            )
        )

    def test_numeric_fmxmlsnippet_id_is_rejected(self):
        def mutate(documents):
            pattern = self._pattern(documents, "create-record")
            pattern["fmxmlsnippetId"] = 123

        errors = self._errors(mutate)
        self.assertTrue(
            any("fmxmlsnippet numeric IDs are forbidden" in error for error in errors)
        )

    def test_filemaker_internal_id_is_rejected(self):
        def mutate(documents):
            pattern = self._pattern(documents, "create-record")
            pattern["placeholders"][0]["internalId"] = 456

        errors = self._errors(mutate)
        self.assertTrue(
            any("FileMaker internal" in error for error in errors)
        )

    def test_verification_status_promotion_is_rejected(self):
        def mutate(documents):
            pattern = self._pattern(documents, "create-record")
            pattern["verificationStatus"] = "fmse_verified"

        errors = self._errors(mutate)
        self.assertTrue(
            any(
                "verificationStatus must remain design_only" in error
                for error in errors
            )
        )
        self.assertTrue(
            any("device evidence value" in error for error in errors)
        )

    def test_later_version_function_is_rejected(self):
        def mutate(documents):
            pattern = self._pattern(
                documents,
                "json-parameter-validation",
            )
            pattern["functions"].append(
                {
                    "name": "Get ( LastErrorLocation )",
                    "purpose": "Forbidden later-version function.",
                    "sourceIds": [
                        "claris-fm19-function-get-lasterror"
                    ],
                }
            )

        errors = self._errors(mutate)
        self.assertTrue(
            any("later-version function is forbidden" in error for error in errors)
        )

    def test_later_version_script_feature_mention_is_rejected(self):
        def mutate(documents):
            pattern = self._pattern(documents, "create-record")
            pattern["happyPath"].append(
                "Use Open Transaction before creating the record."
            )

        errors = self._errors(mutate)
        self.assertTrue(
            any("later-version feature mention" in error for error in errors)
        )

    def test_duplicate_pattern_id_is_rejected(self):
        def mutate(documents):
            entries = documents["index"]["patterns"]
            entries[1]["id"] = entries[0]["id"]

        errors = self._errors(mutate)
        self.assertTrue(
            any("duplicate pattern ID" in error for error in errors)
        )

    def test_index_reference_break_is_rejected(self):
        def mutate(documents):
            documents["index"]["patterns"][0][
                "path"
            ] = "create-record/missing.json"

        errors = self._errors(mutate)
        self.assertTrue(
            any("index reference does not exist" in error for error in errors)
        )

    def test_malformed_json_example_is_rejected(self):
        def mutate(documents):
            pattern = self._pattern(documents, "create-record")
            pattern["examples"]["failureJson"] = "{not-json"

        errors = self._errors(mutate)
        self.assertTrue(
            any("invalid JSON example" in error for error in errors)
        )

    def test_wrong_target_version_is_rejected(self):
        def mutate(documents):
            pattern = self._pattern(documents, "create-record")
            pattern["target"]["fileMakerServer"] = "20.1"

        errors = self._errors(mutate)
        self.assertTrue(
            any("target must be FileMaker Pro/Server 19.5" in error for error in errors)
        )

    def test_renderer_verified_self_declaration_is_rejected(self):
        def mutate(documents):
            pattern = self._pattern(documents, "create-record")
            step = next(
                item
                for item in pattern["steps"]
                if item["name"] == "New Record/Request"
            )
            step["rendererStatus"] = "verified"

        errors = self._errors(mutate)
        self.assertTrue(
            any("renderer status must be derived" in error for error in errors)
        )

    def test_missing_pattern_is_rejected(self):
        def mutate(documents):
            documents["index"]["patterns"].pop()

        errors = self._errors(mutate)
        self.assertTrue(
            any("exactly the five approved pattern IDs" in error for error in errors)
        )

    def test_hard_coded_layout_name_is_rejected(self):
        def mutate(documents):
            pattern = self._pattern(documents, "create-record")
            pattern["happyPath"].append("Go to Layout [ HardCodedLayout ]")

        errors = self._errors(mutate)
        self.assertTrue(
            any("hard-coded layout name" in error for error in errors)
        )

    def test_invalid_input_example_is_rejected(self):
        def mutate(documents):
            pattern = self._pattern(
                documents,
                "find-one-by-primary-key",
            )
            pattern["examples"]["inputJson"] = json.dumps(
                {
                    "schemaVersion": 1,
                    "requestId": "req-synthetic",
                }
            )

        errors = self._errors(mutate)
        self.assertTrue(
            any("does not satisfy input contract" in error for error in errors)
        )


if __name__ == "__main__":
    unittest.main()
