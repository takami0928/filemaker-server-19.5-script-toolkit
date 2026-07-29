from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
import unittest

from fms19_toolkit.cli import main as cli_main
from fms19_toolkit.compatibility import (
    compatibility_steps,
    filter_steps,
)
from fms19_toolkit.compatibility_policy import (
    _validate_compatibility_documents,
    validate_compatibility_catalog,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
COMPATIBILITY_ROOT = REPO_ROOT / "catalog/fm19.5/compatibility"
RESEARCH_ROOT = REPO_ROOT / "research/issue-7/candidates"


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _run_cli(arguments: list[str]) -> tuple[int, str, str]:
    stdout = StringIO()
    stderr = StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        try:
            result = cli_main(arguments)
        except SystemExit as exc:
            result = int(exc.code)
    return result, stdout.getvalue(), stderr.getvalue()


class CompatibilityCatalogPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents = {
            "catalog": _load_json(COMPATIBILITY_ROOT / "script-steps.json"),
            "sources": _load_json(COMPATIBILITY_ROOT / "sources.json"),
            "research_catalog": _load_json(
                RESEARCH_ROOT / "script-step-catalog-candidates.json"
            ),
            "research_sources": _load_json(
                RESEARCH_ROOT / "source-registry-candidates.json"
            ),
            "verified": _load_json(
                REPO_ROOT / "catalog/fm19.5/verified-steps.json"
            ),
        }

    def _errors(self, mutate) -> list[str]:
        documents = deepcopy(self.documents)
        mutate(documents)
        errors: list[str] = []
        _validate_compatibility_documents(
            documents["catalog"],
            documents["sources"],
            documents["research_catalog"],
            documents["research_sources"],
            documents["verified"],
            errors,
        )
        return errors

    def test_valid_normalized_catalog(self):
        self.assertEqual(validate_compatibility_catalog(REPO_ROOT), [])
        self.assertEqual(len(self.documents["catalog"]["steps"]), 59)
        self.assertEqual(len(self.documents["sources"]["sources"]), 64)

    def test_duplicate_step_name_is_rejected(self):
        def mutate(documents):
            steps = documents["catalog"]["steps"]
            steps[1]["name"] = steps[0]["name"]

        errors = self._errors(mutate)
        self.assertTrue(any("duplicate step name" in error for error in errors))

    def test_unregistered_source_id_is_rejected(self):
        def mutate(documents):
            documents["catalog"]["steps"][0]["sourceIds"].append(
                "source-does-not-exist"
            )

        errors = self._errors(mutate)
        self.assertTrue(any("unknown source ID" in error for error in errors))

    def test_invalid_compatibility_value_is_rejected(self):
        def mutate(documents):
            documents["catalog"]["steps"][0]["execution"]["psos"] = "yes"

        errors = self._errors(mutate)
        self.assertTrue(
            any("invalid compatibility value" in error for error in errors)
        )

    def test_partial_without_conditions_is_rejected(self):
        def mutate(documents):
            step = next(
                item
                for item in documents["catalog"]["steps"]
                if item["name"] == "New Window"
            )
            step["options"] = []
            step["contextRequirements"] = []
            step["contextEffects"] = []
            step["dialogBehavior"] = ""
            step["risks"] = []
            step["versionTransitions"] = []

        errors = self._errors(mutate)
        self.assertTrue(
            any("partial compatibility requires" in error for error in errors)
        )

    def test_unknown_support_is_not_available(self):
        step = deepcopy(compatibility_steps()[0])
        step["execution"]["psos"] = "unknown"
        self.assertEqual(
            filter_steps([step], context="psos", support="available"),
            [],
        )
        self.assertEqual(
            filter_steps([step], context="psos", support="unknown"),
            [step],
        )

    def test_later_server_support_backport_is_rejected(self):
        def mutate(documents):
            step = next(
                item
                for item in documents["catalog"]["steps"]
                if item["name"] == "Set Error Logging"
            )
            step["execution"]["psos"] = "available"

        errors = self._errors(mutate)
        self.assertTrue(
            any("must not be backported" in error for error in errors)
        )

    def test_later_source_cannot_be_used_as_unconditional_19_5_evidence(self):
        def mutate(documents):
            step = next(
                item
                for item in documents["catalog"]["steps"]
                if item["name"] == "Set Error Logging"
            )
            step["versionTransitions"] = []

        errors = self._errors(mutate)
        self.assertTrue(
            any("uses later/current source" in error for error in errors)
        )

    def test_renderer_verified_promotion_requires_paste_evidence(self):
        def mutate(documents):
            entry = next(
                item
                for item in documents["verified"]["steps"]
                if item["name"] == "Set Variable"
            )
            entry["status"] = "supported"

        errors = self._errors(mutate)
        self.assertTrue(
            any("requires fm19_5_paste_verified" in error for error in errors)
        )

    def test_secondary_source_cannot_be_promoted_to_primary(self):
        def mutate(documents):
            normalized_source = documents["sources"]["sources"][0]
            research_source = next(
                item
                for item in documents["research_sources"]["sources"]
                if item["id"] == normalized_source["id"]
            )
            research_source["sourceType"] = "secondary"

        errors = self._errors(mutate)
        self.assertTrue(
            any("may promote secondary evidence" in error for error in errors)
        )

    def test_research_source_information_cannot_disappear(self):
        def mutate(documents):
            documents["sources"]["sources"][0]["title"] = ""

        errors = self._errors(mutate)
        self.assertTrue(
            any("lost or changed" in error for error in errors)
        )

    def test_every_research_step_must_be_normalized(self):
        def mutate(documents):
            documents["catalog"]["steps"].pop()
            documents["catalog"]["scope"]["stepCount"] -= 1

        errors = self._errors(mutate)
        self.assertTrue(
            any("every research candidate step" in error for error in errors)
        )

    def test_every_execution_context_is_required(self):
        def mutate(documents):
            del documents["catalog"]["steps"][0]["execution"]["data_api"]

        errors = self._errors(mutate)
        self.assertTrue(
            any("every canonical context" in error for error in errors)
        )


class CompatCommandTests(unittest.TestCase):
    def test_exact_match(self):
        code, stdout, stderr = _run_cli(
            ["compat", "Perform Script on Server"]
        )
        self.assertEqual(code, 0)
        self.assertIn("Perform Script on Server", stdout)
        self.assertEqual(stderr, "")

    def test_case_insensitive_trimmed_match(self):
        code, stdout, stderr = _run_cli(
            ["compat", "  perform script on server  "]
        )
        self.assertEqual(code, 0)
        self.assertTrue(stdout.startswith("Perform Script on Server"))
        self.assertEqual(stderr, "")

    def test_unique_partial_match_is_only_a_candidate(self):
        code, stdout, stderr = _run_cli(["compat", "Error Logging"])
        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("Candidates:", stderr)
        self.assertIn("Set Error Logging", stderr)

    def test_multiple_partial_matches_are_not_auto_selected(self):
        code, stdout, stderr = _run_cli(["compat", "Data File"])
        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("Candidates:", stderr)
        self.assertLessEqual(
            len([line for line in stderr.splitlines() if line.startswith("  - ")]),
            5,
        )

    def test_unknown_step_returns_nonzero(self):
        code, stdout, stderr = _run_cli(
            ["compat", "Definitely Not a FileMaker Step"]
        )
        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("no exact script-step match", stderr)

    def test_context_is_emphasized(self):
        code, stdout, stderr = _run_cli(
            [
                "compat",
                "Perform Script on Server",
                "--context",
                "psos",
            ]
        )
        self.assertEqual(code, 0)
        self.assertIn("Selected context:\n  psos: available", stdout)
        self.assertEqual(stderr, "")

    def test_context_alias_uses_canonical_name(self):
        code, stdout, stderr = _run_cli(
            ["compat", "Insert File", "--context", "schedule"]
        )
        self.assertEqual(code, 0)
        self.assertIn("server_schedule: unavailable", stdout)
        self.assertNotIn("  schedule:", stdout)
        self.assertEqual(stderr, "")

    def test_unavailable_context_is_a_successful_lookup(self):
        code, stdout, stderr = _run_cli(
            ["compat", "Insert File", "--context", "server_schedule"]
        )
        self.assertEqual(code, 0)
        self.assertIn("server_schedule: unavailable", stdout)
        self.assertEqual(stderr, "")

    def test_json_output(self):
        code, stdout, stderr = _run_cli(
            ["compat", "Pause/Resume Script", "--json"]
        )
        self.assertEqual(code, 0)
        data = json.loads(stdout)
        self.assertEqual(data["name"], "Pause/Resume Script")
        self.assertEqual(data["execution"]["psos"], "available")
        self.assertEqual(data["rendererStatus"], "not_verified")
        self.assertEqual(stderr, "")

    def test_json_output_is_deterministic(self):
        first = _run_cli(["compat", "Pause/Resume Script", "--json"])
        second = _run_cli(["compat", "Pause/Resume Script", "--json"])
        self.assertEqual(first, second)


class ListStepsCommandTests(unittest.TestCase):
    def test_all_steps(self):
        code, stdout, stderr = _run_cli(["list-steps"])
        self.assertEqual(code, 0)
        self.assertEqual(len(stdout.splitlines()), 60)
        self.assertIn("PSOS\tSERVER_SCHEDULE\tRENDERER", stdout.splitlines()[0])
        self.assertEqual(stderr, "")

    def test_context_display(self):
        code, stdout, stderr = _run_cli(
            ["list-steps", "--context", "psos"]
        )
        self.assertEqual(code, 0)
        self.assertIn("\tPSOS\tRENDERER", stdout.splitlines()[0])
        self.assertNotIn("SERVER_SCHEDULE", stdout.splitlines()[0])
        self.assertEqual(stderr, "")

    def test_support_filter(self):
        code, stdout, stderr = _run_cli(
            [
                "list-steps",
                "--context",
                "psos",
                "--support",
                "available",
                "--json",
            ]
        )
        self.assertEqual(code, 0)
        data = json.loads(stdout)
        self.assertTrue(data)
        self.assertTrue(
            all(step["execution"]["psos"] == "available" for step in data)
        )
        self.assertEqual(stderr, "")

    def test_category_filter(self):
        code, stdout, stderr = _run_cli(
            ["list-steps", "--category", "control", "--json"]
        )
        self.assertEqual(code, 0)
        data = json.loads(stdout)
        self.assertEqual(len(data), 16)
        self.assertTrue(all(step["category"] == "control" for step in data))
        self.assertEqual(stderr, "")

    def test_renderer_status_filter(self):
        code, stdout, stderr = _run_cli(
            [
                "list-steps",
                "--renderer-status",
                "experimental",
                "--json",
            ]
        )
        self.assertEqual(code, 0)
        data = json.loads(stdout)
        self.assertEqual(len(data), 6)
        self.assertTrue(
            all(step["rendererStatus"] == "experimental" for step in data)
        )
        self.assertEqual(stderr, "")

    def test_compound_filters(self):
        code, stdout, stderr = _run_cli(
            [
                "list-steps",
                "--context",
                "server_schedule",
                "--support",
                "unavailable",
                "--category",
                "external-io",
                "--renderer-status",
                "not_verified",
                "--json",
            ]
        )
        self.assertEqual(code, 0)
        data = json.loads(stdout)
        self.assertTrue(data)
        self.assertTrue(
            all(
                step["execution"]["server_schedule"] == "unavailable"
                and step["category"] == "external-io"
                and step["rendererStatus"] == "not_verified"
                for step in data
            )
        )
        self.assertEqual(stderr, "")

    def test_json_output(self):
        code, stdout, stderr = _run_cli(["list-steps", "--json"])
        self.assertEqual(code, 0)
        data = json.loads(stdout)
        self.assertEqual(len(data), 59)
        self.assertEqual(stderr, "")

    def test_order_is_deterministic(self):
        first = _run_cli(["list-steps", "--json"])
        second = _run_cli(["list-steps", "--json"])
        self.assertEqual(first, second)
        data = json.loads(first[1])
        actual = [(step["category"], step["name"]) for step in data]
        expected = sorted(
            actual,
            key=lambda item: (item[0].casefold(), item[1].casefold()),
        )
        self.assertEqual(actual, expected)

    def test_support_without_context_is_rejected(self):
        code, stdout, stderr = _run_cli(
            ["list-steps", "--support", "available"]
        )
        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("--support requires --context", stderr)

    def test_invalid_context_is_rejected(self):
        code, stdout, stderr = _run_cli(
            ["list-steps", "--context", "invalid-context"]
        )
        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("unknown context", stderr)


if __name__ == "__main__":
    unittest.main()
