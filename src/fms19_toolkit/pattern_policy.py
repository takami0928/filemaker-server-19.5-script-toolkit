from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from .compatibility import (
    CONTEXTS,
    SUPPORT_VALUES,
    derive_renderer_metadata,
)


EXPECTED_PATTERN_IDS = (
    "create-record",
    "find-one-by-primary-key",
    "json-parameter-validation",
    "perform-script-on-server",
    "update-record",
)
PATTERN_CONTEXTS = {
    "client",
    "psos",
    "server_schedule",
}
TARGET = {
    "fileMakerPro": "19.5",
    "fileMakerServer": "19.5",
}
PATTERN_FIELDS = {
    "schemaVersion",
    "id",
    "title",
    "target",
    "purpose",
    "composesPatterns",
    "supportedContexts",
    "preconditions",
    "inputContract",
    "outputContract",
    "placeholders",
    "steps",
    "functions",
    "happyPath",
    "errorBranches",
    "concurrencyNotes",
    "securityNotes",
    "examples",
    "sourceIds",
    "verificationStatus",
}
STEP_FIELDS = {
    "name",
    "purpose",
    "requiredContexts",
    "compatibility",
    "rendererStatus",
    "partialConditions",
}
PLACEHOLDER_FIELDS = {
    "name",
    "kind",
    "required",
    "resolutionSource",
    "unresolvedBehavior",
}
FUNCTION_FIELDS = {
    "name",
    "purpose",
    "sourceIds",
}
ERROR_BRANCH_FIELDS = {
    "code",
    "trigger",
    "fileMakerCodes",
    "action",
}
EXAMPLE_FIELDS = {
    "inputJson",
    "successJson",
    "failureJson",
}
OBJECT_PLACEHOLDER_KINDS = {
    "field",
    "fieldMap",
    "layout",
    "script",
    "tableOccurrence",
}
FORBIDDEN_EVIDENCE_VALUES = {
    "paste_verified",
    "runtime_verified",
    "fmse_verified",
    "fm19_5_paste_verified",
    "fm19_5_runtime_verified",
}
FORBIDDEN_ID_KEYS = {
    "clipboardid",
    "filemakerinternalid",
    "fmxmlsnippetid",
    "internalid",
    "numericstepid",
}
PLACEHOLDER_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
PLACEHOLDER_TOKEN_RE = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")
VERSION_RE = re.compile(r"^\s*(\d+)(?:\.(\d+))?(?:\.(\d+))?")
NUMERIC_FMXML_ID_RE = re.compile(
    r"fmxmlsnippet.{0,80}\b(?:id|step\s+id)\b.{0,20}\b\d+\b",
    re.IGNORECASE | re.DOTALL,
)
QUALIFIED_OBJECT_RE = re.compile(
    r"(?<!\{\{)\b[A-Za-z][A-Za-z0-9_ ]*::[A-Za-z][A-Za-z0-9_ ]*\b"
)
LITERAL_LAYOUT_RE = re.compile(
    r"\bGo to Layout\s*\[\s*(?!\{\{|<)([^\]\r\n;]+)",
    re.IGNORECASE,
)
LITERAL_SERVER_SCRIPT_RE = re.compile(
    r"\bPerform Script on Server\s*\[\s*(?:Specified:\s*)?"
    r"(?!\{\{|<)([^\]\r\n;]+)",
    re.IGNORECASE,
)


def _load_json(path: Path, errors: list[str]) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing practical-pattern JSON file: {path}")
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"invalid practical-pattern JSON in {path}: {exc}")
    return None


def _duplicates(values: list[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        normalized = value.strip().casefold()
        if normalized in seen:
            duplicates.add(value)
        seen.add(normalized)
    return duplicates


def _leading_version(value: Any) -> tuple[int, int, int] | None:
    if not isinstance(value, str):
        return None
    match = VERSION_RE.match(value)
    if match is None:
        return None
    return tuple(int(part or 0) for part in match.groups())


def _after_19_5(value: Any) -> bool:
    version = _leading_version(value)
    return version is not None and version[:2] > (19, 5)


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _collect_placeholder_tokens(value: Any) -> set[str]:
    tokens: set[str] = set()
    if isinstance(value, dict):
        for child in value.values():
            tokens.update(_collect_placeholder_tokens(child))
    elif isinstance(value, list):
        for child in value:
            tokens.update(_collect_placeholder_tokens(child))
    elif isinstance(value, str):
        tokens.update(PLACEHOLDER_TOKEN_RE.findall(value))
    return tokens


def _validate_string_array(
    value: Any,
    label: str,
    errors: list[str],
    *,
    allow_empty: bool = False,
) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{label}: must be an array")
        return []
    if not value and not allow_empty:
        errors.append(f"{label}: must not be empty")
    if any(not _nonempty_string(item) for item in value):
        errors.append(f"{label}: must contain non-empty strings")
        return []
    items = [str(item) for item in value]
    duplicates = _duplicates(items)
    if duplicates:
        errors.append(f"{label}: duplicate value(s): {sorted(duplicates)}")
    return items


def _validate_forbidden_claims(
    pattern: dict[str, Any],
    label: str,
    errors: list[str],
) -> None:
    def inspect(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                normalized_key = re.sub(r"[^a-z0-9]", "", key.casefold())
                if normalized_key in FORBIDDEN_ID_KEYS:
                    errors.append(
                        f"{label}{path}.{key}: FileMaker internal or "
                        "fmxmlsnippet numeric IDs are forbidden"
                    )
                if (
                    "verified" in normalized_key
                    and normalized_key
                    not in {"verificationstatus", "rendererstatus"}
                    and child not in (False, None, "", [])
                ):
                    errors.append(
                        f"{label}{path}.{key}: FileMaker device verification "
                        "must not be self-declared"
                    )
                inspect(child, f"{path}.{key}")
            return
        if isinstance(value, list):
            for index, child in enumerate(value):
                inspect(child, f"{path}[{index}]")
            return
        if isinstance(value, str):
            if value.casefold() in FORBIDDEN_EVIDENCE_VALUES:
                errors.append(
                    f"{label}{path}: FileMaker device evidence value "
                    f"{value!r} is forbidden"
                )
            if NUMERIC_FMXML_ID_RE.search(value):
                errors.append(
                    f"{label}{path}: numeric fmxmlsnippet ID claim is forbidden"
                )
            if QUALIFIED_OBJECT_RE.search(value):
                errors.append(
                    f"{label}{path}: hard-coded FileMaker field reference "
                    "must be a placeholder"
                )
            if LITERAL_LAYOUT_RE.search(value):
                errors.append(
                    f"{label}{path}: hard-coded layout name must be a placeholder"
                )
            if LITERAL_SERVER_SCRIPT_RE.search(value):
                errors.append(
                    f"{label}{path}: hard-coded server script name must be a "
                    "placeholder"
                )

    inspect(pattern, "")


def _validate_later_feature_mentions(
    pattern: dict[str, Any],
    research_catalog: dict[str, Any],
    label: str,
    errors: list[str],
) -> None:
    exclusions = research_catalog.get("laterVersionExclusions")
    if not isinstance(exclusions, list):
        errors.append("research later-version exclusions must be an array")
        return
    forbidden_names = {
        item["name"]
        for item in exclusions
        if isinstance(item, dict)
        and item.get("availableIn19_5") is False
        and _nonempty_string(item.get("name"))
    }

    def inspect(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                inspect(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                inspect(child, f"{path}[{index}]")
        elif isinstance(value, str):
            normalized = value.casefold()
            mentioned = sorted(
                name
                for name in forbidden_names
                if name.casefold() in normalized
            )
            if mentioned:
                errors.append(
                    f"{label}{path}: later-version feature mention(s) are "
                    f"forbidden: {mentioned}"
                )

    inspect(pattern, "")


def _validate_sources(
    values: Any,
    known_sources: set[str],
    label: str,
    errors: list[str],
) -> set[str]:
    source_ids = _validate_string_array(values, label, errors)
    unknown = set(source_ids) - known_sources
    if unknown:
        errors.append(f"{label}: unregistered source ID(s): {sorted(unknown)}")
    return set(source_ids)


def _validate_examples(
    pattern: dict[str, Any],
    result_schema: dict[str, Any],
    label: str,
    errors: list[str],
) -> None:
    examples = pattern.get("examples")
    if not isinstance(examples, dict) or set(examples) != EXAMPLE_FIELDS:
        errors.append(f"{label}.examples: unexpected or missing fields")
        return

    parsed: dict[str, Any] = {}
    for name in EXAMPLE_FIELDS:
        raw = examples.get(name)
        if not isinstance(raw, str):
            errors.append(f"{label}.examples.{name}: must be a JSON string")
            continue
        try:
            parsed[name] = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(
                f"{label}.examples.{name}: invalid JSON example: {exc}"
            )

    input_contract = pattern.get("inputContract")
    input_schema = (
        input_contract.get("schema")
        if isinstance(input_contract, dict)
        else None
    )
    if isinstance(input_schema, dict) and "inputJson" in parsed:
        try:
            validator = Draft202012Validator(input_schema)
        except SchemaError as exc:
            errors.append(f"{label}.inputContract.schema: invalid schema: {exc}")
        else:
            for error in validator.iter_errors(parsed["inputJson"]):
                errors.append(
                    f"{label}.examples.inputJson: does not satisfy input "
                    f"contract: {error.message}"
                )

    try:
        result_validator = Draft202012Validator(result_schema)
    except SchemaError as exc:
        errors.append(f"common result schema: invalid schema: {exc}")
        return
    for name, expected_ok in (
        ("successJson", True),
        ("failureJson", False),
    ):
        if name not in parsed:
            continue
        value = parsed[name]
        for error in result_validator.iter_errors(value):
            errors.append(
                f"{label}.examples.{name}: does not satisfy common result "
                f"contract: {error.message}"
            )
        if isinstance(value, dict):
            if value.get("ok") is not expected_ok:
                errors.append(
                    f"{label}.examples.{name}: ok must be {expected_ok}"
                )
            meta = value.get("meta")
            if (
                not isinstance(meta, dict)
                or meta.get("pattern") != pattern.get("id")
            ):
                errors.append(
                    f"{label}.examples.{name}: meta.pattern must match pattern ID"
                )


def _validate_placeholders(
    pattern: dict[str, Any],
    label: str,
    errors: list[str],
) -> None:
    placeholders = pattern.get("placeholders")
    if not isinstance(placeholders, list) or not placeholders:
        errors.append(f"{label}.placeholders: must be a non-empty array")
        return
    names: list[str] = []
    for index, placeholder in enumerate(placeholders):
        item_label = f"{label}.placeholders[{index}]"
        if not isinstance(placeholder, dict):
            errors.append(f"{item_label}: must be an object")
            continue
        if set(placeholder) != PLACEHOLDER_FIELDS:
            errors.append(f"{item_label}: unexpected or missing fields")
        name = placeholder.get("name")
        if not isinstance(name, str) or not PLACEHOLDER_NAME_RE.fullmatch(name):
            errors.append(f"{item_label}: invalid placeholder name {name!r}")
        else:
            names.append(name)
        if not _nonempty_string(placeholder.get("kind")):
            errors.append(f"{item_label}: kind must be a non-empty string")
        if not isinstance(placeholder.get("required"), bool):
            errors.append(f"{item_label}: required must be boolean")
        if not _nonempty_string(placeholder.get("resolutionSource")):
            errors.append(
                f"{item_label}: resolutionSource must be a non-empty string"
            )
        behavior = placeholder.get("unresolvedBehavior")
        if placeholder.get("required") is True and behavior != "block_generation":
            errors.append(
                f"{item_label}: required placeholder must use block_generation"
            )
        if placeholder.get("required") is False and behavior not in {
            "block_generation",
            "omit_optional_feature",
        }:
            errors.append(
                f"{item_label}: optional placeholder has invalid unresolvedBehavior"
            )
        if (
            placeholder.get("kind") in OBJECT_PLACEHOLDER_KINDS
            and behavior not in {"block_generation", "omit_optional_feature"}
        ):
            errors.append(
                f"{item_label}: FileMaker object reference must fail closed"
            )
    duplicates = _duplicates(names)
    if duplicates:
        errors.append(
            f"{label}.placeholders: duplicate placeholder(s): "
            f"{sorted(duplicates)}"
        )
    declared = set(names)
    used = _collect_placeholder_tokens(pattern)
    undeclared = sorted(used - declared)
    if undeclared:
        errors.append(
            f"{label}.placeholders: undeclared placeholder token(s): "
            f"{undeclared}"
        )
    unused = sorted(declared - used)
    if unused:
        errors.append(
            f"{label}.placeholders: unused declared placeholder(s): "
            f"{unused}"
        )


def _validate_steps(
    pattern: dict[str, Any],
    compatibility_catalog: dict[str, Any],
    verified_catalog: dict[str, Any],
    pattern_sources: set[str],
    label: str,
    errors: list[str],
) -> None:
    catalog_steps = compatibility_catalog.get("steps")
    if not isinstance(catalog_steps, list):
        errors.append("compatibility catalog steps must be an array")
        return
    by_name = {
        step.get("name"): step
        for step in catalog_steps
        if isinstance(step, dict) and isinstance(step.get("name"), str)
    }
    steps = pattern.get("steps")
    if not isinstance(steps, list) or not steps:
        errors.append(f"{label}.steps: must be a non-empty array")
        return
    names: list[str] = []
    for index, step in enumerate(steps):
        item_label = f"{label}.steps[{index}]"
        if not isinstance(step, dict):
            errors.append(f"{item_label}: must be an object")
            continue
        if set(step) != STEP_FIELDS:
            errors.append(f"{item_label}: unexpected or missing fields")
        name = step.get("name")
        if not _nonempty_string(name):
            errors.append(f"{item_label}: name must be a non-empty string")
            continue
        names.append(name)
        catalog_step = by_name.get(name)
        if catalog_step is None:
            errors.append(f"{item_label}: unregistered script step {name!r}")
            continue
        if catalog_step.get("availableIn19_5") is not True:
            errors.append(f"{item_label}: step is not available in FileMaker 19.5")
        if _after_19_5(catalog_step.get("introducedIn")):
            errors.append(f"{item_label}: later-version step is forbidden")
        if not _nonempty_string(step.get("purpose")):
            errors.append(f"{item_label}: purpose must be a non-empty string")
        required_contexts = _validate_string_array(
            step.get("requiredContexts"),
            f"{item_label}.requiredContexts",
            errors,
        )
        invalid_contexts = set(required_contexts) - set(CONTEXTS)
        if invalid_contexts:
            errors.append(
                f"{item_label}: invalid context(s): {sorted(invalid_contexts)}"
            )
        compatibility = step.get("compatibility")
        if not isinstance(compatibility, dict):
            errors.append(f"{item_label}.compatibility: must be an object")
            compatibility = {}
        elif set(compatibility) != set(required_contexts):
            errors.append(
                f"{item_label}.compatibility: keys must equal requiredContexts"
            )
        conditions = step.get("partialConditions")
        if not isinstance(conditions, dict):
            errors.append(f"{item_label}.partialConditions: must be an object")
            conditions = {}
        for context in required_contexts:
            claimed = compatibility.get(context)
            actual = (
                catalog_step.get("execution", {}).get(context)
                if isinstance(catalog_step.get("execution"), dict)
                else None
            )
            if claimed not in SUPPORT_VALUES:
                errors.append(
                    f"{item_label}: invalid compatibility value for {context}"
                )
            if claimed != actual:
                errors.append(
                    f"{item_label}: {context} compatibility must match catalog "
                    f"{actual!r}"
                )
            if actual == "unavailable":
                errors.append(
                    f"{item_label}: unavailable context {context!r} cannot be used"
                )
            if actual == "unknown":
                errors.append(
                    f"{item_label}: unknown context {context!r} cannot be treated "
                    "as supported"
                )
            if actual == "partial" and not _nonempty_string(
                conditions.get(context)
            ):
                errors.append(
                    f"{item_label}: partial context {context!r} requires a "
                    "condition"
                )
        unknown_condition_contexts = set(conditions) - set(required_contexts)
        if unknown_condition_contexts:
            errors.append(
                f"{item_label}: partialConditions contains unused context(s): "
                f"{sorted(unknown_condition_contexts)}"
            )
        derived = derive_renderer_metadata(name, verified_catalog)
        if step.get("rendererStatus") != derived["rendererStatus"]:
            errors.append(
                f"{item_label}: renderer status must be derived as "
                f"{derived['rendererStatus']!r}"
            )
        if (
            step.get("rendererStatus") == "verified"
            and "fm19_5_paste_verified"
            not in set(derived["rendererEvidence"])
        ):
            errors.append(
                f"{item_label}: renderer verified self-declaration is forbidden"
            )
        catalog_source_ids = catalog_step.get("sourceIds")
        if isinstance(catalog_source_ids, list):
            missing_sources = set(catalog_source_ids) - pattern_sources
            if missing_sources:
                errors.append(
                    f"{item_label}: pattern sourceIds omit catalog source(s): "
                    f"{sorted(missing_sources)}"
                )
    duplicates = _duplicates(names)
    if duplicates:
        errors.append(
            f"{label}.steps: duplicate step name(s): {sorted(duplicates)}"
        )


def _validate_functions_and_errors(
    pattern: dict[str, Any],
    research_catalog: dict[str, Any],
    known_implementation_sources: set[str],
    pattern_sources: set[str],
    label: str,
    errors: list[str],
) -> None:
    research_functions = research_catalog.get("functions")
    if not isinstance(research_functions, list):
        errors.append("research function candidates must be an array")
        return
    functions_by_name = {
        item.get("name"): item
        for item in research_functions
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    exclusions = research_catalog.get("laterVersionExclusions")
    later_functions = {
        item.get("name")
        for item in exclusions
        if isinstance(item, dict)
        and item.get("featureType") == "function"
        and item.get("availableIn19_5") is False
    } if isinstance(exclusions, list) else set()

    functions = pattern.get("functions")
    if not isinstance(functions, list) or not functions:
        errors.append(f"{label}.functions: must be a non-empty array")
        functions = []
    names: list[str] = []
    for index, function in enumerate(functions):
        item_label = f"{label}.functions[{index}]"
        if not isinstance(function, dict):
            errors.append(f"{item_label}: must be an object")
            continue
        if set(function) != FUNCTION_FIELDS:
            errors.append(f"{item_label}: unexpected or missing fields")
        name = function.get("name")
        if not _nonempty_string(name):
            errors.append(f"{item_label}: name must be a non-empty string")
            continue
        names.append(name)
        if name in later_functions:
            errors.append(f"{item_label}: later-version function is forbidden")
            continue
        candidate = functions_by_name.get(name)
        if candidate is None:
            errors.append(
                f"{item_label}: function is not in the FileMaker 19.5 "
                f"research candidate: {name!r}"
            )
            continue
        if candidate.get("availableIn19_5") is not True or _after_19_5(
            candidate.get("introducedIn")
        ):
            errors.append(f"{item_label}: function is not available in 19.5")
        if not _nonempty_string(function.get("purpose")):
            errors.append(f"{item_label}: purpose must be a non-empty string")
        function_sources = _validate_sources(
            function.get("sourceIds"),
            known_implementation_sources,
            f"{item_label}.sourceIds",
            errors,
        )
        candidate_sources = set(candidate.get("sourceIds", []))
        if not function_sources.issubset(candidate_sources):
            errors.append(
                f"{item_label}: sourceIds must come from the research candidate"
            )
        missing_candidate_sources = candidate_sources - pattern_sources
        if missing_candidate_sources:
            errors.append(
                f"{item_label}: pattern sourceIds omit function source(s): "
                f"{sorted(missing_candidate_sources)}"
            )
    duplicates = _duplicates(names)
    if duplicates:
        errors.append(
            f"{label}.functions: duplicate function name(s): {sorted(duplicates)}"
        )

    research_errors = research_catalog.get("errors")
    known_error_codes = {
        item.get("code")
        for item in research_errors
        if isinstance(item, dict)
        and item.get("availableIn19_5") is True
        and isinstance(item.get("code"), int)
    } if isinstance(research_errors, list) else set()
    branches = pattern.get("errorBranches")
    if not isinstance(branches, list) or not branches:
        errors.append(f"{label}.errorBranches: must be a non-empty array")
        return
    codes: list[str] = []
    used_numeric_codes: set[int] = set()
    for index, branch in enumerate(branches):
        item_label = f"{label}.errorBranches[{index}]"
        if not isinstance(branch, dict):
            errors.append(f"{item_label}: must be an object")
            continue
        if set(branch) != ERROR_BRANCH_FIELDS:
            errors.append(f"{item_label}: unexpected or missing fields")
        for field in ("code", "trigger", "action"):
            if not _nonempty_string(branch.get(field)):
                errors.append(f"{item_label}.{field}: must be a non-empty string")
        if isinstance(branch.get("code"), str):
            codes.append(branch["code"])
        filemaker_codes = branch.get("fileMakerCodes")
        if not isinstance(filemaker_codes, list) or any(
            not isinstance(code, int) or isinstance(code, bool)
            for code in filemaker_codes
        ):
            errors.append(f"{item_label}.fileMakerCodes: must contain integers")
            continue
        used_numeric_codes.update(filemaker_codes)
        unknown_codes = set(filemaker_codes) - known_error_codes
        if unknown_codes:
            errors.append(
                f"{item_label}: FileMaker error code(s) lack a 19.5 research "
                f"candidate: {sorted(unknown_codes)}"
            )
    duplicate_codes = _duplicates(codes)
    if duplicate_codes:
        errors.append(
            f"{label}.errorBranches: duplicate code(s): {sorted(duplicate_codes)}"
        )
    if used_numeric_codes and "claris-current-error-codes" not in pattern_sources:
        errors.append(
            f"{label}: numeric FileMaker errors require the registered "
            "candidate error-code source"
        )


def _validate_pattern(
    pattern: Any,
    expected_id: str,
    compatibility_catalog: dict[str, Any],
    verified_catalog: dict[str, Any],
    research_catalog: dict[str, Any],
    result_schema: dict[str, Any],
    known_compatibility_sources: set[str],
    known_implementation_sources: set[str],
    errors: list[str],
) -> None:
    label = f"pattern {expected_id!r}"
    if not isinstance(pattern, dict):
        errors.append(f"{label}: root must be an object")
        return
    if set(pattern) != PATTERN_FIELDS:
        errors.append(f"{label}: unexpected or missing root fields")
    if pattern.get("schemaVersion") != 1:
        errors.append(f"{label}: schemaVersion must be 1")
    if pattern.get("id") != expected_id or expected_id not in EXPECTED_PATTERN_IDS:
        errors.append(f"{label}: invalid pattern ID {pattern.get('id')!r}")
    if not _nonempty_string(pattern.get("title")):
        errors.append(f"{label}: title must be a non-empty string")
    if not _nonempty_string(pattern.get("purpose")):
        errors.append(f"{label}: purpose must be a non-empty string")
    if pattern.get("target") != TARGET:
        errors.append(f"{label}: target must be FileMaker Pro/Server 19.5")
    if pattern.get("verificationStatus") != "design_only":
        errors.append(f"{label}: verificationStatus must remain design_only")

    composed = _validate_string_array(
        pattern.get("composesPatterns"),
        f"{label}.composesPatterns",
        errors,
        allow_empty=True,
    )
    unknown_composed = set(composed) - set(EXPECTED_PATTERN_IDS)
    if unknown_composed:
        errors.append(
            f"{label}: unknown composed pattern(s): {sorted(unknown_composed)}"
        )
    if expected_id in composed:
        errors.append(f"{label}: pattern cannot compose itself")

    contexts = _validate_string_array(
        pattern.get("supportedContexts"),
        f"{label}.supportedContexts",
        errors,
    )
    invalid_contexts = set(contexts) - PATTERN_CONTEXTS
    if invalid_contexts:
        errors.append(
            f"{label}: invalid supported context(s): {sorted(invalid_contexts)}"
        )
    for field in (
        "preconditions",
        "happyPath",
        "concurrencyNotes",
        "securityNotes",
    ):
        _validate_string_array(pattern.get(field), f"{label}.{field}", errors)

    input_contract = pattern.get("inputContract")
    if (
        not isinstance(input_contract, dict)
        or set(input_contract) != {"format", "schema"}
        or input_contract.get("format") != "json"
        or not isinstance(input_contract.get("schema"), dict)
    ):
        errors.append(
            f"{label}.inputContract: must contain JSON format and schema"
        )
    output_contract = pattern.get("outputContract")
    if not isinstance(output_contract, dict) or set(output_contract) != {
        "schemaRef",
        "successCodes",
        "errorCodes",
    }:
        errors.append(f"{label}.outputContract: unexpected or missing fields")
    else:
        if (
            output_contract.get("schemaRef")
            != "patterns/fm19.5/common-result.schema.json"
        ):
            errors.append(
                f"{label}.outputContract: must reference common result schema"
            )
        success_codes = _validate_string_array(
            output_contract.get("successCodes"),
            f"{label}.outputContract.successCodes",
            errors,
        )
        error_codes = _validate_string_array(
            output_contract.get("errorCodes"),
            f"{label}.outputContract.errorCodes",
            errors,
        )
        overlap = set(success_codes) & set(error_codes)
        if overlap:
            errors.append(
                f"{label}.outputContract: success/error code overlap: "
                f"{sorted(overlap)}"
            )

    pattern_sources = _validate_sources(
        pattern.get("sourceIds"),
        known_compatibility_sources | known_implementation_sources,
        f"{label}.sourceIds",
        errors,
    )
    _validate_placeholders(pattern, label, errors)
    _validate_steps(
        pattern,
        compatibility_catalog,
        verified_catalog,
        pattern_sources,
        label,
        errors,
    )
    _validate_functions_and_errors(
        pattern,
        research_catalog,
        known_implementation_sources,
        pattern_sources,
        label,
        errors,
    )
    _validate_examples(pattern, result_schema, label, errors)
    _validate_forbidden_claims(pattern, label, errors)
    _validate_later_feature_mentions(
        pattern,
        research_catalog,
        label,
        errors,
    )


def _validate_pattern_documents(
    index: Any,
    patterns_by_path: dict[str, Any],
    result_schema: Any,
    compatibility_catalog: Any,
    compatibility_sources: Any,
    verified_catalog: Any,
    research_catalog: Any,
    implementation_sources: Any,
    errors: list[str],
) -> None:
    if not isinstance(index, dict):
        errors.append("patterns index: root must be an object")
        return
    if set(index) != {
        "schemaVersion",
        "target",
        "verificationStatus",
        "patterns",
    }:
        errors.append("patterns index: unexpected or missing root fields")
    if index.get("schemaVersion") != 1:
        errors.append("patterns index: schemaVersion must be 1")
    if index.get("target") != TARGET:
        errors.append("patterns index: target must be FileMaker Pro/Server 19.5")
    if index.get("verificationStatus") != "design_only":
        errors.append("patterns index: verificationStatus must remain design_only")
    if not isinstance(result_schema, dict):
        errors.append("common result schema: root must be an object")
        return
    try:
        Draft202012Validator.check_schema(result_schema)
    except SchemaError as exc:
        errors.append(f"common result schema: invalid schema: {exc}")

    entries = index.get("patterns")
    if not isinstance(entries, list):
        errors.append("patterns index: patterns must be an array")
        return
    ids: list[str] = []
    paths: list[str] = []
    for position, entry in enumerate(entries):
        label = f"patterns index[{position}]"
        if not isinstance(entry, dict) or set(entry) != {"id", "path"}:
            errors.append(f"{label}: must contain only id and path")
            continue
        pattern_id = entry.get("id")
        path = entry.get("path")
        if not _nonempty_string(pattern_id):
            errors.append(f"{label}: id must be a non-empty string")
        else:
            ids.append(pattern_id)
        if not _nonempty_string(path):
            errors.append(f"{label}: path must be a non-empty string")
        else:
            paths.append(path)
            expected_path = f"{pattern_id}/pattern.json"
            if path != expected_path:
                errors.append(
                    f"{label}: path must be {expected_path!r}, got {path!r}"
                )
            if path not in patterns_by_path:
                errors.append(f"{label}: index reference does not exist: {path}")
    duplicate_ids = _duplicates(ids)
    if duplicate_ids:
        errors.append(
            f"patterns index: duplicate pattern ID(s): {sorted(duplicate_ids)}"
        )
    duplicate_paths = _duplicates(paths)
    if duplicate_paths:
        errors.append(
            f"patterns index: duplicate path(s): {sorted(duplicate_paths)}"
        )
    if set(ids) != set(EXPECTED_PATTERN_IDS) or len(ids) != len(
        EXPECTED_PATTERN_IDS
    ):
        errors.append(
            "patterns index: must contain exactly the five approved pattern IDs"
        )
    if ids != sorted(ids):
        errors.append("patterns index: entries must be sorted by pattern ID")
    extra_paths = set(patterns_by_path) - set(paths)
    if extra_paths:
        errors.append(
            f"patterns index: unindexed pattern file(s): {sorted(extra_paths)}"
        )

    def source_ids(document: Any) -> set[str]:
        if not isinstance(document, dict):
            return set()
        entries_value = document.get("sources")
        if not isinstance(entries_value, list):
            return set()
        return {
            item["id"]
            for item in entries_value
            if isinstance(item, dict) and _nonempty_string(item.get("id"))
        }

    known_compatibility_sources = source_ids(compatibility_sources)
    known_implementation_sources = source_ids(implementation_sources)
    required_documents = (
        compatibility_catalog,
        verified_catalog,
        research_catalog,
    )
    if not all(isinstance(document, dict) for document in required_documents):
        errors.append("pattern policy: required catalog document is invalid")
        return
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        path = entry.get("path")
        pattern_id = entry.get("id")
        if not isinstance(path, str) or not isinstance(pattern_id, str):
            continue
        pattern = patterns_by_path.get(path)
        if pattern is None:
            continue
        _validate_pattern(
            pattern,
            pattern_id,
            compatibility_catalog,
            verified_catalog,
            research_catalog,
            result_schema,
            known_compatibility_sources,
            known_implementation_sources,
            errors,
        )


def validate_practical_patterns(root: str | Path) -> list[str]:
    root_path = Path(root).resolve()
    pattern_root = root_path / "patterns/fm19.5"
    errors: list[str] = []
    index = _load_json(pattern_root / "index.json", errors)
    result_schema = _load_json(
        pattern_root / "common-result.schema.json",
        errors,
    )
    compatibility_catalog = _load_json(
        root_path / "catalog/fm19.5/compatibility/script-steps.json",
        errors,
    )
    compatibility_sources = _load_json(
        root_path / "catalog/fm19.5/compatibility/sources.json",
        errors,
    )
    verified_catalog = _load_json(
        root_path / "catalog/fm19.5/verified-steps.json",
        errors,
    )
    research_catalog = _load_json(
        root_path
        / "research/issue-7/candidates/script-step-catalog-candidates.json",
        errors,
    )
    implementation_sources = _load_json(
        root_path / "sources/registry.json",
        errors,
    )

    patterns_by_path: dict[str, Any] = {}
    for path in sorted(pattern_root.glob("*/pattern.json")):
        relative = path.relative_to(pattern_root).as_posix()
        data = _load_json(path, errors)
        if data is not None:
            patterns_by_path[relative] = data
    for pattern_id in EXPECTED_PATTERN_IDS:
        readme_path = pattern_root / pattern_id / "README.md"
        try:
            readme = readme_path.read_text(encoding="utf-8")
        except (FileNotFoundError, UnicodeDecodeError) as exc:
            errors.append(f"invalid practical-pattern README {readme_path}: {exc}")
            continue
        for section in range(1, 16):
            if f"## {section}." not in readme:
                errors.append(
                    f"{readme_path}: missing required human section {section}"
                )
        if NUMERIC_FMXML_ID_RE.search(readme):
            errors.append(f"{readme_path}: numeric fmxmlsnippet ID is forbidden")

    documents = (
        index,
        result_schema,
        compatibility_catalog,
        compatibility_sources,
        verified_catalog,
        research_catalog,
        implementation_sources,
    )
    if all(document is not None for document in documents):
        _validate_pattern_documents(
            index,
            patterns_by_path,
            result_schema,
            compatibility_catalog,
            compatibility_sources,
            verified_catalog,
            research_catalog,
            implementation_sources,
            errors,
        )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the five FileMaker 19.5 practical patterns."
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="repository root (default: current directory)",
    )
    args = parser.parse_args(argv)
    errors = validate_practical_patterns(args.root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Practical FileMaker 19.5 pattern checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
