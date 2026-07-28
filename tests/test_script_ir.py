from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from fms19_toolkit.renderer import render_ir, render_ir_file, render_step
from fms19_toolkit.script_ir import (
    ScriptIRValidationError,
    dumps_ir,
    migrate_ir_file,
    migrate_v1_to_v2,
    validate_ir,
)
from fms19_toolkit.snippet import validate_snippet_text


REPO_ROOT = Path(__file__).resolve().parents[1]
V1_PATH = REPO_ROOT / "examples/server-script-ir.json"
V2_PATH = REPO_ROOT / "examples/server-script-ir-v2.json"


def load_v1() -> dict:
    return json.loads(V1_PATH.read_text(encoding="utf-8"))


def load_v2() -> dict:
    return json.loads(V2_PATH.read_text(encoding="utf-8"))


def handwritten_migration_v2() -> dict:
    data = load_v2()
    data["target"]["execution"] = "unspecified"
    data["script"]["execution"] = "unspecified"
    data["script"]["sideEffects"] = {"state": "unspecified"}
    data["context"] = {
        "mode": "unspecified",
        "reason": "A synthetic handwritten v2 document omitted context.",
    }
    data["unresolvedIssues"] = [
        {
            "key": "handwritten.execution",
            "category": "target_execution",
            "description": "Execution is intentionally unresolved for this test.",
            "blocking": True,
        },
        {
            "key": "handwritten.sideEffects",
            "category": "script_metadata",
            "description": "Side effects are intentionally unresolved for this test.",
            "blocking": True,
        },
        {
            "key": "handwritten.context",
            "category": "context",
            "description": "Context is intentionally unresolved for this test.",
            "blocking": True,
        },
    ]
    data["status"] = {
        "design": "draft",
        "evidence": "unverified",
    }
    data["migration"] = {"fromSchemaVersion": 1}
    return data


class ScriptIRV2Tests(unittest.TestCase):
    def assert_invalid(self, data: dict) -> ScriptIRValidationError:
        with self.assertRaises(ScriptIRValidationError) as raised:
            validate_ir(data)
        return raised.exception

    def test_valid_v2_ir(self):
        self.assertEqual(validate_ir(load_v2()), 2)

    def test_unknown_property_is_rejected(self):
        data = load_v2()
        data["steps"][0]["state"] = True
        self.assert_invalid(data)

    def test_invalid_target_versions_are_rejected(self):
        for property_name, value in (
            ("serverVersion", "20.1"),
            ("proVersion", "19.6"),
        ):
            with self.subTest(property_name=property_name):
                data = load_v2()
                data["target"][property_name] = value
                self.assert_invalid(data)

    def test_invalid_execution_is_rejected(self):
        data = load_v2()
        data["target"]["execution"] = "batch"
        data["script"]["execution"] = "batch"
        self.assert_invalid(data)

    def test_unspecified_execution_is_reserved_for_v1_migration(self):
        data = load_v2()
        data["target"]["execution"] = "unspecified"
        data["script"]["execution"] = "unspecified"
        data["unresolvedIssues"] = [
            {
                "key": "execution.pending",
                "category": "target_execution",
                "description": "Execution remains to be selected.",
                "blocking": True,
            }
        ]
        self.assert_invalid(data)

    def test_migration_marker_cannot_bypass_native_v2_rules(self):
        data = load_v2()
        data["migration"] = {"fromSchemaVersion": 1}
        self.assert_invalid(data)

    def test_handwritten_migration_marker_does_not_authorize_render(self):
        data = handwritten_migration_v2()
        self.assertEqual(validate_ir(data), 2)
        with self.assertRaises(ScriptIRValidationError):
            render_ir(data)

    def test_other_serialized_values_cannot_activate_legacy_render(self):
        base = handwritten_migration_v2()
        variants = []

        renamed = deepcopy(base)
        renamed["script"]["name"] = "SRV | Handwritten Synthetic Marker"
        variants.append(("script name", renamed))

        changed_step = deepcopy(base)
        changed_step["steps"][0]["text"] = "Synthetic marker test changed."
        variants.append(("step content", changed_step))

        changed_issues = deepcopy(base)
        for index, issue in enumerate(changed_issues["unresolvedIssues"]):
            issue["key"] = f"changed.issue{index}"
            issue["description"] = f"Synthetic changed issue {index}."
        variants.append(("issue metadata", changed_issues))

        for label, data in variants:
            with self.subTest(label=label):
                self.assertEqual(validate_ir(data), 2)
                with self.assertRaises(ScriptIRValidationError):
                    render_ir(data)

    def test_native_v2_unspecified_context_is_rejected(self):
        data = load_v2()
        data["context"] = {
            "mode": "unspecified",
            "reason": "Synthetic context was not selected.",
        }
        self.assert_invalid(data)

    def test_native_v2_unspecified_side_effects_are_rejected(self):
        data = load_v2()
        data["script"]["sideEffects"] = {"state": "unspecified"}
        self.assert_invalid(data)

    def test_native_v2_unspecified_variable_initialization_is_rejected(self):
        data = load_v2()
        data["variables"][0]["initialization"] = {"method": "unspecified"}
        self.assert_invalid(data)

    def test_native_v2_unknown_variable_type_is_rejected(self):
        data = load_v2()
        data["variables"][0]["type"] = "unknown"
        self.assert_invalid(data)

    def test_migration_v2_preserves_unspecified_states_as_draft(self):
        data = migrate_v1_to_v2(load_v1())
        data["variables"][0]["initialization"] = {"method": "unspecified"}
        self.assertEqual(validate_ir(data), 2)
        self.assertEqual(data["context"]["mode"], "unspecified")
        self.assertEqual(data["script"]["sideEffects"]["state"], "unspecified")
        self.assertEqual(data["variables"][0]["type"], "unknown")
        self.assertEqual(data["status"], {"design": "draft", "evidence": "unverified"})

    def test_migration_only_state_requires_corresponding_blocking_issue(self):
        data = migrate_v1_to_v2(load_v1())
        for issue in data["unresolvedIssues"]:
            if issue["category"] == "context":
                issue["blocking"] = False
        self.assert_invalid(data)

    def test_migration_with_unspecified_design_cannot_be_ready(self):
        for status in (
            {"design": "ready", "evidence": "unverified"},
            {"design": "ready", "evidence": "design_ready"},
        ):
            with self.subTest(status=status):
                data = migrate_v1_to_v2(load_v1())
                data["status"] = status
                self.assert_invalid(data)

    def test_unsubstantiated_evidence_states_are_rejected(self):
        for evidence in (
            "xml_generated",
            "paste_verified",
            "runtime_verified",
            "fmse_verified",
        ):
            with self.subTest(evidence=evidence):
                data = load_v2()
                data["status"]["evidence"] = evidence
                self.assert_invalid(data)

    def test_step_specific_required_property_is_enforced(self):
        data = load_v2()
        del data["steps"][1]["state"]
        self.assert_invalid(data)

    def test_property_from_another_step_is_rejected(self):
        data = load_v2()
        data["steps"][5]["calculation"] = "1"
        self.assert_invalid(data)

    def test_unknown_step_type_is_rejected(self):
        data = load_v2()
        data["steps"][0] = {"type": "delete_everything"}
        self.assert_invalid(data)

    def test_duplicate_variables_are_rejected(self):
        data = load_v2()
        data["variables"].append(deepcopy(data["variables"][0]))
        self.assert_invalid(data)

    def test_variable_prefix_and_scope_must_match(self):
        for name, scope in (("$local", "global"), ("$$global", "local")):
            with self.subTest(name=name, scope=scope):
                data = load_v2()
                data["variables"][0]["name"] = name
                data["variables"][0]["scope"] = scope
                data["steps"][2]["name"] = name
                self.assert_invalid(data)

    def test_duplicate_object_reference_keys_are_rejected(self):
        data = load_v2()
        reference = {
            "key": "layout.synthetic",
            "type": "layout",
            "name": "Synthetic Processing Layout",
            "internalId": 1001,
            "resolution": "resolved",
        }
        data["objectReferences"] = [reference, deepcopy(reference)]
        self.assert_invalid(data)

    def test_resolved_reference_requires_internal_id(self):
        data = load_v2()
        data["objectReferences"] = [
            {
                "key": "layout.synthetic",
                "type": "layout",
                "name": "Synthetic Processing Layout",
                "resolution": "resolved",
            }
        ]
        self.assert_invalid(data)

    def test_unresolved_reference_forbids_internal_id(self):
        data = load_v2()
        data["objectReferences"] = [
            {
                "key": "layout.synthetic",
                "type": "layout",
                "name": "Synthetic Processing Layout",
                "internalId": 1001,
                "resolution": "unresolved",
            }
        ]
        self.assert_invalid(data)

    def test_v1_to_v2_migration_is_deterministic(self):
        source = load_v1()
        first = dumps_ir(migrate_v1_to_v2(source))
        second = dumps_ir(migrate_v1_to_v2(source))
        self.assertEqual(first, second)
        self.assertEqual(validate_ir(json.loads(first)), 2)

        with tempfile.TemporaryDirectory() as temp_dir:
            first_path = Path(temp_dir) / "first.json"
            second_path = Path(temp_dir) / "second.json"
            migrate_ir_file(V1_PATH, first_path)
            migrate_ir_file(V1_PATH, second_path)
            self.assertEqual(first_path.read_bytes(), second_path.read_bytes())

    def test_saved_migration_v2_validates_but_cannot_render(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            migrated_path = Path(temp_dir) / "migrated.json"
            output_path = Path(temp_dir) / "should-not-exist.xml"
            migrate_ir_file(V1_PATH, migrated_path)
            migrated = json.loads(migrated_path.read_text(encoding="utf-8"))

            self.assertEqual(validate_ir(migrated), 2)
            with self.assertRaises(ScriptIRValidationError):
                render_ir_file(migrated_path, output_path)
            self.assertFalse(output_path.exists())

    def test_v1_render_compatibility(self):
        source = load_v1()
        expected_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<fmxmlsnippet type="FMObjectList">',
        ]
        for step in source["steps"]:
            expected_lines.extend(render_step(step))
        expected_lines.append("</fmxmlsnippet>")
        expected = "\n".join(expected_lines) + "\n"
        self.assertEqual(render_ir(source), expected)
        self.assertFalse(validate_snippet_text(expected))

    def test_v2_renders_all_existing_seven_step_types(self):
        data = load_v2()
        self.assertEqual(
            {step["type"] for step in data["steps"]},
            {
                "comment",
                "set_error_capture",
                "set_variable",
                "if",
                "else",
                "end_if",
                "exit_script",
            },
        )
        xml = render_ir(data)
        self.assertFalse(validate_snippet_text(xml))
        root = ET.fromstring(xml)
        self.assertEqual(len(root.findall("Step")), len(data["steps"]))

    def test_migration_never_fabricates_filemaker_object_ids(self):
        migrated = migrate_v1_to_v2(load_v1())
        self.assertEqual(migrated["objectReferences"], [])

        def visit(value):
            if isinstance(value, dict):
                self.assertNotIn("internalId", value)
                for child in value.values():
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)

        visit(migrated)

    def test_japanese_newlines_and_special_characters_round_trip(self):
        data = load_v2()
        expected = data["steps"][0]["text"]
        self.assertIn("\n", expected)
        self.assertIn("合成JSON要求", expected)
        self.assertIn("< > &", expected)
        root = ET.fromstring(render_ir(data))
        self.assertEqual(root.findall("Step")[0].findtext("Text"), expected)

    def test_identical_input_produces_identical_v2_and_xml(self):
        source = load_v1()
        self.assertEqual(
            migrate_v1_to_v2(source),
            migrate_v1_to_v2(deepcopy(source)),
        )
        v2 = load_v2()
        self.assertEqual(render_ir(v2), render_ir(deepcopy(v2)))

    def test_unresolved_reference_validates_but_blocks_render(self):
        data = load_v2()
        data["objectReferences"] = [
            {
                "key": "field.syntheticStatus",
                "type": "field",
                "name": "SyntheticRecord::Status",
                "resolution": "unresolved",
            }
        ]
        data["status"] = {
            "design": "blocked",
            "evidence": "unverified",
        }
        self.assertEqual(validate_ir(data), 2)
        with self.assertRaises(ScriptIRValidationError):
            render_ir(data)

    def test_resolved_object_reference_allows_render(self):
        data = load_v2()
        data["objectReferences"] = [
            {
                "key": "valueList.syntheticStatus",
                "type": "valueList",
                "name": "Synthetic Status",
                "internalId": 1001,
                "resolution": "resolved",
            }
        ]
        self.assertFalse(validate_snippet_text(render_ir(data)))

    def test_blocking_native_v2_issue_blocks_render(self):
        data = load_v2()
        data["unresolvedIssues"] = [
            {
                "key": "contract.pending",
                "category": "business_rule",
                "description": "A synthetic decision remains unresolved.",
                "blocking": True,
            }
        ]
        data["status"] = {
            "design": "blocked",
            "evidence": "unverified",
        }
        self.assertEqual(validate_ir(data), 2)
        with self.assertRaises(ScriptIRValidationError):
            render_ir(data)

    def test_context_can_be_explicitly_absent(self):
        data = load_v2()
        self.assertEqual(data["context"]["mode"], "none")
        self.assertEqual(validate_ir(data), 2)

    def test_required_context_reference_types_are_checked(self):
        data = load_v2()
        data["objectReferences"] = [
            {
                "key": "layout.synthetic",
                "type": "field",
                "name": "SyntheticRecord::Status",
                "internalId": 1001,
                "resolution": "resolved",
            },
            {
                "key": "to.synthetic",
                "type": "tableOccurrence",
                "name": "SyntheticRecord",
                "internalId": 1002,
                "resolution": "resolved",
            },
        ]
        data["context"] = {
            "mode": "required",
            "layoutRef": "layout.synthetic",
            "tableOccurrenceRef": "to.synthetic",
            "recordIdentification": {
                "method": "script_parameter",
                "description": "Use a synthetic primary key from the JSON parameter.",
            },
            "foundSet": {
                "handling": "rebuild",
                "description": "Rebuild the found set in the independent FMSE session.",
            },
        }
        self.assert_invalid(data)

    def test_set_variable_target_must_be_declared(self):
        data = load_v2()
        data["variables"] = [
            variable for variable in data["variables"] if variable["name"] != "$out"
        ]
        self.assert_invalid(data)

    def test_embedded_contract_must_be_a_valid_json_schema(self):
        data = load_v2()
        data["script"]["inputContract"]["schema"] = {"type": "not-a-json-type"}
        self.assert_invalid(data)

    def test_script_and_target_execution_must_match(self):
        data = load_v2()
        data["script"]["execution"] = "client"
        self.assert_invalid(data)

    def test_unbalanced_if_is_rejected_before_rendering(self):
        data = load_v2()
        data["steps"] = data["steps"][:-2] + [data["steps"][-1]]
        self.assert_invalid(data)


if __name__ == "__main__":
    unittest.main()
