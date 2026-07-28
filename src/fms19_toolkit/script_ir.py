from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import sysconfig
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError


SCHEMA_FILES = {
    1: "script-ir-v1.schema.json",
    2: "script-ir-v2.schema.json",
}


class ScriptIRValidationError(ValueError):
    """Raised when a Script IR document fails structural or semantic validation."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("Script IR validation failed: " + "; ".join(errors))


def _schema_directories() -> tuple[Path, ...]:
    source_tree = Path(__file__).resolve().parents[2] / "schemas"
    installed_data = (
        Path(sysconfig.get_path("data"))
        / "share"
        / "fms19-script-toolkit"
        / "schemas"
    )
    return source_tree, installed_data


@lru_cache(maxsize=2)
def load_schema(version: int) -> dict[str, Any]:
    try:
        filename = SCHEMA_FILES[version]
    except KeyError as exc:
        raise ValueError(f"unsupported Script IR schema version: {version!r}") from exc

    for directory in _schema_directories():
        path = directory / filename
        if path.is_file():
            schema = json.loads(path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
            return schema
    searched = ", ".join(str(path / filename) for path in _schema_directories())
    raise RuntimeError(f"unable to locate {filename}; searched: {searched}")


def detect_ir_version(data: Any) -> int:
    if not isinstance(data, dict):
        raise ScriptIRValidationError(["root: must be a JSON object"])
    if data.get("schemaVersion") == 2:
        return 2
    if "schemaVersion" in data:
        raise ScriptIRValidationError(
            [f"schemaVersion: unsupported value {data.get('schemaVersion')!r}"]
        )
    if data.get("target") == "FileMaker Server 19.5" and data.get("kind") == "script_steps":
        return 1
    raise ScriptIRValidationError(
        [
            "root: cannot determine Script IR version; expected v1 target/kind "
            "or schemaVersion 2"
        ]
    )


def _json_path(parts: Any) -> str:
    path = "$"
    for part in parts:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            path += f".{part}"
    return path


def _format_schema_error(error: ValidationError) -> str:
    message = error.message
    if error.validator == "oneOf" and error.context:
        relevant = [
            child
            for child in error.context
            if child.validator in {"required", "additionalProperties", "const", "enum"}
        ]
        if relevant:
            details = "; ".join(child.message for child in relevant[:4])
            message = f"{message} ({details})"
    return f"{_json_path(error.absolute_path)}: {message}"


def _schema_errors(data: dict[str, Any], version: int) -> list[str]:
    validator = Draft202012Validator(load_schema(version))
    failures = sorted(
        validator.iter_errors(data),
        key=lambda error: (
            tuple(str(part) for part in error.absolute_path),
            error.message,
        ),
    )
    return [_format_schema_error(error) for error in failures]


def _expected_scope(name: str) -> str | None:
    if name.startswith("$$"):
        return "global"
    if name.startswith("$"):
        return "local"
    return None


def _validate_embedded_contracts(data: dict[str, Any], errors: list[str]) -> None:
    script = data["script"]
    for contract_name in ("inputContract", "resultContract"):
        schema = script[contract_name]["schema"]
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as exc:
            errors.append(
                f"$.script.{contract_name}.schema: invalid Draft 2020-12 schema: "
                f"{exc.message}"
            )


def _validate_variables(data: dict[str, Any], errors: list[str]) -> None:
    declared: dict[str, dict[str, Any]] = {}
    for index, variable in enumerate(data["variables"]):
        name = variable["name"]
        if name in declared:
            errors.append(f"$.variables[{index}].name: duplicate variable {name!r}")
        else:
            declared[name] = variable
        expected = _expected_scope(name)
        if expected is not None and variable["scope"] != expected:
            errors.append(
                f"$.variables[{index}].scope: {name!r} requires scope {expected!r}"
            )

    for index, step in enumerate(data["steps"]):
        if step["type"] != "set_variable":
            continue
        name = step["name"]
        if name not in declared:
            errors.append(
                f"$.steps[{index}].name: Set Variable target {name!r} is not declared"
            )


def _validate_object_references(data: dict[str, Any], errors: list[str]) -> None:
    references: dict[str, dict[str, Any]] = {}
    for index, reference in enumerate(data["objectReferences"]):
        key = reference["key"]
        if key in references:
            errors.append(
                f"$.objectReferences[{index}].key: duplicate object reference key {key!r}"
            )
        else:
            references[key] = reference

    context = data["context"]
    if context["mode"] != "required":
        return
    expected = {
        "layoutRef": "layout",
        "tableOccurrenceRef": "tableOccurrence",
    }
    for property_name, object_type in expected.items():
        key = context[property_name]
        reference = references.get(key)
        if reference is None:
            errors.append(
                f"$.context.{property_name}: object reference {key!r} is not declared"
            )
        elif reference["type"] != object_type:
            errors.append(
                f"$.context.{property_name}: {key!r} must reference a "
                f"{object_type}, not {reference['type']}"
            )


def _validate_unique_keys(data: dict[str, Any], errors: list[str]) -> None:
    for property_name in ("unresolvedIssues", "risks"):
        seen: set[str] = set()
        for index, item in enumerate(data[property_name]):
            key = item["key"]
            if key in seen:
                errors.append(
                    f"$.{property_name}[{index}].key: duplicate key {key!r}"
                )
            seen.add(key)


def _validate_control_flow(data: dict[str, Any], errors: list[str]) -> None:
    stack: list[dict[str, Any]] = []
    for index, step in enumerate(data["steps"]):
        step_type = step["type"]
        if step_type == "if":
            stack.append({"index": index, "elseSeen": False})
        elif step_type == "else":
            if not stack:
                errors.append(f"$.steps[{index}]: else is outside an if block")
            elif stack[-1]["elseSeen"]:
                errors.append(
                    f"$.steps[{index}]: if block at step {stack[-1]['index']} "
                    "contains more than one else"
                )
            else:
                stack[-1]["elseSeen"] = True
        elif step_type == "end_if":
            if not stack:
                errors.append(f"$.steps[{index}]: end_if has no matching if")
            else:
                stack.pop()
    for opener in stack:
        errors.append(f"$.steps[{opener['index']}]: if has no matching end_if")


def _validate_status(data: dict[str, Any], errors: list[str]) -> None:
    unresolved_references = any(
        reference["resolution"] == "unresolved"
        for reference in data["objectReferences"]
    )
    blocking_issues = any(
        issue["blocking"] for issue in data["unresolvedIssues"]
    )
    incomplete = unresolved_references or blocking_issues
    status = data["status"]
    if incomplete and status["design"] == "ready":
        errors.append(
            "$.status.design: cannot be ready while references or blocking "
            "issues remain unresolved"
        )
    if incomplete and status["evidence"] != "unverified":
        errors.append(
            "$.status.evidence: must be unverified while references or blocking "
            "issues remain unresolved"
        )
    if status["evidence"] != "unverified" and status["design"] != "ready":
        errors.append(
            "$.status.design: evidence beyond unverified requires a ready design"
        )


def _semantic_errors_v2(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data["script"]["execution"] != data["target"]["execution"]:
        errors.append(
            "$.script.execution: must match $.target.execution "
            f"({data['target']['execution']!r})"
        )
    if data["target"]["execution"] == "unspecified":
        if data.get("migration") != {"fromSchemaVersion": 1}:
            errors.append(
                "$.target.execution: unspecified is reserved for deterministic "
                "migration from Script IR v1"
            )
        if not any(
            issue["category"] == "target_execution"
            for issue in data["unresolvedIssues"]
        ):
            errors.append(
                "$.unresolvedIssues: migrated unspecified execution requires a "
                "target_execution issue"
            )
    elif "migration" in data:
        errors.append(
            "$.migration: is allowed only when v1 execution remains unspecified"
        )
    _validate_embedded_contracts(data, errors)
    _validate_variables(data, errors)
    _validate_object_references(data, errors)
    _validate_unique_keys(data, errors)
    _validate_control_flow(data, errors)
    _validate_status(data, errors)
    return errors


def validate_ir(data: Any, version: int | None = None) -> int:
    detected = detect_ir_version(data) if version is None else version
    if detected not in SCHEMA_FILES:
        raise ValueError(f"unsupported Script IR schema version: {detected!r}")
    if not isinstance(data, dict):
        raise ScriptIRValidationError(["root: must be a JSON object"])

    errors = _schema_errors(data, detected)
    if not errors and detected == 2:
        errors.extend(_semantic_errors_v2(data))
    if errors:
        raise ScriptIRValidationError(errors)
    return detected


def read_ir_file(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ScriptIRValidationError(["root: must be a JSON object"])
    return data


def validate_ir_file(path: str | Path) -> int:
    return validate_ir(read_ir_file(path))


def _migrate_step(step: dict[str, Any]) -> dict[str, Any]:
    step_type = step["type"]
    migrated: dict[str, Any] = {"type": step_type}
    if "enabled" in step:
        migrated["enabled"] = step["enabled"]

    if step_type == "comment":
        migrated["text"] = str(step.get("text", ""))
    elif step_type == "set_error_capture":
        migrated["state"] = bool(step.get("state", True))
    elif step_type == "set_variable":
        migrated["name"] = str(step.get("name", ""))
        migrated["calculation"] = str(step.get("calculation", ""))
        migrated["repetition"] = str(step.get("repetition", "1"))
    elif step_type == "if":
        migrated["calculation"] = str(step.get("calculation", ""))
    elif step_type == "exit_script":
        migrated["calculation"] = str(step.get("calculation", ""))
    return migrated


def migrate_v1_to_v2(data: dict[str, Any]) -> dict[str, Any]:
    validate_ir(data, version=1)

    variables: list[dict[str, Any]] = []
    seen_variables: set[str] = set()
    for step in data["steps"]:
        if step["type"] != "set_variable":
            continue
        name = str(step.get("name", ""))
        if name in seen_variables:
            continue
        seen_variables.add(name)
        variables.append(
            {
                "name": name,
                "scope": _expected_scope(name) or "local",
                "type": "unknown",
                "initialization": {
                    "method": "first_assignment",
                    "calculation": str(step.get("calculation", "")),
                },
                "purpose": "Unspecified in Script IR v1.",
            }
        )

    migrated: dict[str, Any] = {
        "schemaVersion": 2,
        "target": {
            "serverVersion": "19.5",
            "proVersion": "19.5",
            "execution": "unspecified",
            "platform": "windows",
        },
        "script": {
            "name": "Unspecified migrated v1 script",
            "purpose": "Unspecified in Script IR v1.",
            "sideEffects": {
                "state": "unspecified",
            },
            "execution": "unspecified",
            "inputContract": {
                "format": "json",
                "description": "Unspecified in Script IR v1.",
                "schema": {},
            },
            "resultContract": {
                "format": "json",
                "description": "Unspecified in Script IR v1.",
                "schema": {},
            },
        },
        "context": {
            "mode": "unspecified",
            "reason": "Script IR v1 did not represent FileMaker context.",
        },
        "variables": variables,
        "objectReferences": [],
        "steps": [_migrate_step(step) for step in data["steps"]],
        "unresolvedIssues": [
            {
                "key": "migration.execution",
                "category": "target_execution",
                "description": (
                    "Script IR v1 did not distinguish client, PSOS, and "
                    "server-schedule execution."
                ),
                "blocking": True,
            },
            {
                "key": "migration.scriptMetadata",
                "category": "script_metadata",
                "description": (
                    "Script name, purpose, and side effects were not represented in v1."
                ),
                "blocking": False,
            },
            {
                "key": "migration.inputContract",
                "category": "input_contract",
                "description": "The v1 input contract was not represented.",
                "blocking": False,
            },
            {
                "key": "migration.resultContract",
                "category": "result_contract",
                "description": "The v1 result contract was not represented.",
                "blocking": False,
            },
            {
                "key": "migration.context",
                "category": "context",
                "description": "The v1 FileMaker context was not represented.",
                "blocking": False,
            },
        ],
        "risks": [],
        "status": {
            "design": "draft",
            "evidence": "unverified",
        },
        "migration": {
            "fromSchemaVersion": 1,
        },
    }
    validate_ir(migrated, version=2)
    return migrated


def normalize_ir_to_v2(data: dict[str, Any]) -> dict[str, Any]:
    version = detect_ir_version(data)
    if version == 1:
        return migrate_v1_to_v2(data)
    validate_ir(data, version=2)
    return data


def ensure_renderable_v2(data: dict[str, Any]) -> None:
    validate_ir(data, version=2)
    unresolved = [
        reference["key"]
        for reference in data["objectReferences"]
        if reference["resolution"] == "unresolved"
    ]
    if unresolved:
        raise ScriptIRValidationError(
            [
                "objectReferences: XML generation requires resolved internal IDs; "
                f"unresolved keys: {unresolved}"
            ]
        )
    is_v1_migration = (
        data.get("migration") == {"fromSchemaVersion": 1}
        and data["target"]["execution"] == "unspecified"
    )
    if not is_v1_migration:
        blocking = [
            issue["key"]
            for issue in data["unresolvedIssues"]
            if issue["blocking"]
        ]
        if blocking:
            raise ScriptIRValidationError(
                [
                    "unresolvedIssues: XML generation is blocked by unresolved "
                    f"items: {blocking}"
                ]
            )


def dumps_ir(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def migrate_ir_file(input_path: str | Path, output_path: str | Path) -> None:
    data = read_ir_file(input_path)
    if detect_ir_version(data) != 1:
        raise ScriptIRValidationError(
            ["migrate-ir accepts Script IR v1 input only"]
        )
    migrated = migrate_v1_to_v2(data)
    Path(output_path).write_text(dumps_ir(migrated), encoding="utf-8", newline="\n")
