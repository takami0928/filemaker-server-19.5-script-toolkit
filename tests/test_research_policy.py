from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from fms19_toolkit.research_policy import (
    _validate_candidate_documents,
    _validate_outer_manifest_files,
    validate_issue_7_research,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
ISSUE_ROOT = REPO_ROOT / "research/issue-7"
CANDIDATES = ISSUE_ROOT / "candidates"


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class Issue7ResearchPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents = {
            "source_registry": _load_json(
                CANDIDATES / "source-registry-candidates.json"
            ),
            "catalog": _load_json(
                CANDIDATES / "script-step-catalog-candidates.json"
            ),
            "unresolved": _load_json(CANDIDATES / "unresolved-questions.json"),
            "coverage": _load_json(CANDIDATES / "coverage-audit.json"),
            "outer_manifest": _load_json(ISSUE_ROOT / "manifest.json"),
            "candidate_manifest": _load_json(CANDIDATES / "manifest.json"),
        }

    def _candidate_errors(self, mutate) -> list[str]:
        documents = deepcopy(self.documents)
        mutate(documents)
        errors: list[str] = []
        _validate_candidate_documents(
            documents["source_registry"],
            documents["catalog"],
            documents["unresolved"],
            documents["coverage"],
            documents["outer_manifest"],
            documents["candidate_manifest"],
            errors,
        )
        return errors

    def test_current_research_candidates_pass_policy(self):
        self.assertEqual(validate_issue_7_research(REPO_ROOT), [])

    def test_duplicate_source_id_is_rejected(self):
        def mutate(documents):
            sources = documents["source_registry"]["sources"]
            sources[1]["id"] = sources[0]["id"]

        errors = self._candidate_errors(mutate)
        self.assertTrue(any("duplicate source ID" in error for error in errors))

    def test_unknown_source_reference_is_rejected(self):
        def mutate(documents):
            documents["catalog"]["steps"][0]["sourceIds"].append(
                "source-does-not-exist"
            )

        errors = self._candidate_errors(mutate)
        self.assertTrue(any("unknown source reference" in error for error in errors))

    def test_duplicate_step_name_is_rejected(self):
        def mutate(documents):
            steps = documents["catalog"]["steps"]
            steps[1]["name"] = steps[0]["name"]

        errors = self._candidate_errors(mutate)
        self.assertTrue(any("duplicate step name" in error for error in errors))

    def test_manifest_hash_mismatch_is_rejected(self):
        manifest = deepcopy(self.documents["outer_manifest"])
        manifest["files"][0]["sha256"] = "0" * 64
        errors: list[str] = []
        _validate_outer_manifest_files(ISSUE_ROOT, manifest, errors)
        self.assertTrue(any("SHA-256 mismatch" in error for error in errors))

    def test_manifest_count_mismatch_is_rejected(self):
        def mutate(documents):
            documents["outer_manifest"]["validation"]["sources"] = 109

        errors = self._candidate_errors(mutate)
        self.assertTrue(any("manifest count mismatch" in error for error in errors))

    def test_research_candidate_classification_cannot_be_promoted(self):
        manifest = deepcopy(self.documents["outer_manifest"])
        manifest["classification"] = "verified"
        errors: list[str] = []
        _validate_outer_manifest_files(ISSUE_ROOT, manifest, errors)
        self.assertTrue(
            any("classification must be research-candidate" in error for error in errors)
        )

    def test_partial_without_option_level_rule_is_rejected(self):
        def mutate(documents):
            step = next(
                item
                for item in documents["catalog"]["steps"]
                if item["name"] == "New Window"
            )
            step["options"] = []
            step["dialogBehavior"] = ""
            step["contextRequirements"] = []
            step["risks"] = []
            step["versionTransitions"] = []

        errors = self._candidate_errors(mutate)
        self.assertTrue(
            any("partial compatibility requires" in error for error in errors)
        )

    def test_unknown_execution_is_not_treated_as_available(self):
        def mutate(documents):
            documents["catalog"]["steps"][0]["execution"]["psos"] = "available"

        errors = self._candidate_errors(mutate)
        self.assertTrue(
            any("unknown must not be treated as available" in error for error in errors)
        )

    def test_unknown_policy_cannot_promote_support(self):
        def mutate(documents):
            documents["catalog"]["policy"]["unknown"] = (
                "Unknown values are available by default."
            )

        errors = self._candidate_errors(mutate)
        self.assertTrue(
            any("unknown compatibility must never" in error for error in errors)
        )

    def test_later_server_support_is_not_backported_to_19_5(self):
        def mutate(documents):
            step = next(
                item
                for item in documents["catalog"]["steps"]
                if item["name"] == "Set Error Logging"
            )
            step["execution"]["psos"] = True

        errors = self._candidate_errors(mutate)
        self.assertTrue(any("later server support" in error for error in errors))

    def test_numeric_fmxmlsnippet_id_is_rejected(self):
        def mutate(documents):
            documents["catalog"]["steps"][0]["fmxmlsnippet"]["stepId"] = 130

        errors = self._candidate_errors(mutate)
        self.assertTrue(
            any("numeric clipboard fmxmlsnippet ID" in error for error in errors)
        )

    def test_public_fixture_cannot_claim_19_5_device_provenance(self):
        def mutate(documents):
            source = next(
                item
                for item in documents["source_registry"]["sources"]
                if item["id"] == "agentic-fm-public-implementation"
            )
            source["sourceType"] = "primary"
            source["targetVersion"] = "FileMaker Pro 19.5 verified fixture"
            source["notes"] = "Sufficient for paste verification."

        errors = self._candidate_errors(mutate)
        self.assertTrue(
            any("public fixture must remain secondary" in error for error in errors)
        )

    def test_research_candidate_cannot_claim_device_evidence(self):
        def mutate(documents):
            documents["catalog"]["steps"][0]["evidence"].append(
                "fm19_5_paste_verified"
            )

        errors = self._candidate_errors(mutate)
        self.assertTrue(
            any("research candidate claims device evidence" in error for error in errors)
        )

    def test_unknown_unresolved_reference_is_rejected(self):
        def mutate(documents):
            documents["coverage"]["unresolvedQuestionIds"][0] = (
                "uq-does-not-exist"
            )

        errors = self._candidate_errors(mutate)
        self.assertTrue(
            any("references unknown unresolved ID" in error for error in errors)
        )

    def test_duplicate_unresolved_id_is_rejected(self):
        def mutate(documents):
            questions = documents["unresolved"]["questions"]
            questions[1]["id"] = questions[0]["id"]

        errors = self._candidate_errors(mutate)
        self.assertTrue(
            any("duplicate unresolved ID" in error for error in errors)
        )


if __name__ == "__main__":
    unittest.main()
