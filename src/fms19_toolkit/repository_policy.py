from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlparse

EVIDENCE_LEVELS = (
    "documented",
    "public_fixture_observed",
    "structure_tested",
    "clipboard_payload_tested",
    "fm19_5_paste_verified",
    "fm19_5_runtime_verified",
    "fmse_verified",
)
EVIDENCE_SET = set(EVIDENCE_LEVELS)
RUNTIME_EVIDENCE = {
    "fm19_5_paste_verified",
    "fm19_5_runtime_verified",
    "fmse_verified",
}
SOURCE_TYPES = {"primary", "secondary"}
SOURCE_STATUSES = {"active", "archived", "superseded", "unavailable"}
STEP_STATUSES = {"experimental", "supported", "deprecated"}
SOURCE_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

REQUIRED_PATHS = (
    "ROADMAP.md",
    "QUALITY_GATES.md",
    "docs/DEFINITION_OF_DONE.md",
    "docs/EVIDENCE_MODEL.md",
    "docs/MATURITY_MODEL.md",
    "docs/SOURCE_POLICY.md",
    "decisions/README.md",
    "decisions/0000-template.md",
    "schemas/source-registry.schema.json",
    "sources/registry.json",
    "catalog/fm19.5/verified-steps.json",
)


def _load_json(path: Path, errors: list[str]) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing required JSON file: {path}")
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in {path}: {exc}")
    return None


def _validate_evidence(
    values: Any,
    label: str,
    errors: list[str],
    *,
    allow_empty: bool = False,
) -> set[str]:
    if not isinstance(values, list):
        errors.append(f"{label}: evidence must be an array")
        return set()
    if not values and not allow_empty:
        errors.append(f"{label}: evidence must not be empty")
    if any(not isinstance(value, str) for value in values):
        errors.append(f"{label}: evidence values must be strings")
        return set()
    evidence = set(values)
    if len(evidence) != len(values):
        errors.append(f"{label}: evidence values must be unique")
    unknown = evidence - EVIDENCE_SET
    if unknown:
        errors.append(f"{label}: unknown evidence values: {sorted(unknown)}")
    return evidence


def _validate_source_registry(root: Path, errors: list[str]) -> set[str]:
    path = root / "sources/registry.json"
    data = _load_json(path, errors)
    if not isinstance(data, dict):
        return set()
    if data.get("schemaVersion") != 1:
        errors.append("sources/registry.json: schemaVersion must be 1")
    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("sources/registry.json: sources must be a non-empty array")
        return set()

    seen: set[str] = set()
    required = {
        "id",
        "title",
        "url",
        "sourceType",
        "publisher",
        "targetVersion",
        "scope",
        "retrievedAt",
        "status",
    }
    allowed = required | {"notes"}
    for index, source in enumerate(sources):
        label = f"sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{label}: source must be an object")
            continue
        missing = required - source.keys()
        extra = source.keys() - allowed
        if missing:
            errors.append(f"{label}: missing fields: {sorted(missing)}")
        if extra:
            errors.append(f"{label}: unknown fields: {sorted(extra)}")
        source_id = source.get("id")
        if not isinstance(source_id, str) or not SOURCE_ID_RE.fullmatch(source_id):
            errors.append(f"{label}: invalid source id: {source_id!r}")
        elif source_id in seen:
            errors.append(f"{label}: duplicate source id: {source_id}")
        else:
            seen.add(source_id)
        parsed = urlparse(str(source.get("url", "")))
        if parsed.scheme != "https" or not parsed.netloc:
            errors.append(f"{label}: url must be an absolute https URL")
        if source.get("sourceType") not in SOURCE_TYPES:
            errors.append(f"{label}: sourceType must be one of {sorted(SOURCE_TYPES)}")
        if source.get("status") not in SOURCE_STATUSES:
            errors.append(f"{label}: status must be one of {sorted(SOURCE_STATUSES)}")
        try:
            date.fromisoformat(str(source.get("retrievedAt", "")))
        except ValueError:
            errors.append(f"{label}: retrievedAt must be YYYY-MM-DD")
        for field in ("title", "publisher", "targetVersion", "scope"):
            if not isinstance(source.get(field), str) or not source[field].strip():
                errors.append(f"{label}: {field} must be a non-empty string")
    return seen


def _validate_source_ids(
    values: Any,
    known_sources: set[str],
    label: str,
    errors: list[str],
) -> None:
    if not isinstance(values, list) or not values:
        errors.append(f"{label}: sourceIds must be a non-empty array")
        return
    if any(not isinstance(value, str) for value in values):
        errors.append(f"{label}: sourceIds must contain strings")
        return
    if len(set(values)) != len(values):
        errors.append(f"{label}: sourceIds must be unique")
    unknown = set(values) - known_sources
    if unknown:
        errors.append(f"{label}: unknown sourceIds: {sorted(unknown)}")


def _validate_step_catalog(root: Path, known_sources: set[str], errors: list[str]) -> None:
    path = root / "catalog/fm19.5/verified-steps.json"
    data = _load_json(path, errors)
    if not isinstance(data, dict):
        return
    if data.get("schemaVersion") != 1:
        errors.append("step catalog: schemaVersion must be 1")
    if data.get("policy") != "deny-by-default":
        errors.append("step catalog: policy must be deny-by-default")

    steps = data.get("steps")
    if not isinstance(steps, list) or not steps:
        errors.append("step catalog: steps must be a non-empty array")
        return

    seen_ir: set[str] = set()
    seen_names: set[str] = set()
    seen_ids: set[int] = set()
    catalog_steps: dict[str, tuple[int, str]] = {}
    for index, step in enumerate(steps):
        label = f"steps[{index}]"
        if not isinstance(step, dict):
            errors.append(f"{label}: step must be an object")
            continue
        required = {
            "ir",
            "name",
            "id",
            "status",
            "sourceIds",
            "evidence",
            "missingEvidence",
        }
        missing = required - step.keys()
        if missing:
            errors.append(f"{label}: missing fields: {sorted(missing)}")
            continue
        ir = step.get("ir")
        name = step.get("name")
        step_id = step.get("id")
        if not isinstance(ir, str) or not ir:
            errors.append(f"{label}: ir must be a non-empty string")
        elif ir in seen_ir:
            errors.append(f"{label}: duplicate ir: {ir}")
        else:
            seen_ir.add(ir)
        if not isinstance(name, str) or not name:
            errors.append(f"{label}: name must be a non-empty string")
        elif name in seen_names:
            errors.append(f"{label}: duplicate step name: {name}")
        else:
            seen_names.add(name)
        if not isinstance(step_id, int) or isinstance(step_id, bool) or step_id < 0:
            errors.append(f"{label}: id must be a non-negative integer")
        elif step_id in seen_ids:
            errors.append(f"{label}: duplicate step id: {step_id}")
        else:
            seen_ids.add(step_id)
        if step.get("status") not in STEP_STATUSES:
            errors.append(f"{label}: invalid status: {step.get('status')!r}")
        _validate_source_ids(step.get("sourceIds"), known_sources, label, errors)
        evidence = _validate_evidence(step.get("evidence"), label, errors)
        missing_evidence = _validate_evidence(
            step.get("missingEvidence"),
            f"{label}.missingEvidence",
            errors,
            allow_empty=True,
        )
        overlap = evidence & missing_evidence
        if overlap:
            errors.append(f"{label}: evidence and missingEvidence overlap: {sorted(overlap)}")
        if evidence & RUNTIME_EVIDENCE and not step.get("verification"):
            errors.append(f"{label}: runtime evidence requires verification metadata")
        if isinstance(ir, str) and isinstance(step_id, int) and isinstance(name, str):
            catalog_steps[ir] = (step_id, name)

    forbidden = data.get("forbidden")
    if not isinstance(forbidden, list) or not forbidden:
        errors.append("step catalog: forbidden must be a non-empty array")
        forbidden_names: set[str] = set()
    else:
        forbidden_names = set()
        for index, item in enumerate(forbidden):
            label = f"forbidden[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{label}: forbidden entry must be an object")
                continue
            required = {"name", "introducedIn", "reason", "sourceIds", "evidence"}
            missing = required - item.keys()
            if missing:
                errors.append(f"{label}: missing fields: {sorted(missing)}")
                continue
            name = item.get("name")
            if not isinstance(name, str) or not name:
                errors.append(f"{label}: name must be a non-empty string")
            elif name in forbidden_names:
                errors.append(f"{label}: duplicate forbidden name: {name}")
            else:
                forbidden_names.add(name)
            _validate_source_ids(item.get("sourceIds"), known_sources, label, errors)
            _validate_evidence(item.get("evidence"), label, errors)

    try:
        from fms19_toolkit.renderer import STEP_IDS
        from fms19_toolkit.snippet import FORBIDDEN_STEP_NAMES
    except ImportError as exc:
        errors.append(f"unable to import toolkit catalogs for consistency check: {exc}")
        return

    if catalog_steps != STEP_IDS:
        errors.append(
            "renderer STEP_IDS must exactly match catalog steps; "
            f"catalog={catalog_steps!r}, renderer={STEP_IDS!r}"
        )
    if forbidden_names != FORBIDDEN_STEP_NAMES:
        errors.append(
            "snippet FORBIDDEN_STEP_NAMES must exactly match catalog forbidden names; "
            f"catalog={sorted(forbidden_names)!r}, code={sorted(FORBIDDEN_STEP_NAMES)!r}"
        )


def check_repository(root: str | Path) -> list[str]:
    root_path = Path(root).resolve()
    errors: list[str] = []
    for relative in REQUIRED_PATHS:
        if not (root_path / relative).is_file():
            errors.append(f"missing required path: {relative}")
    known_sources = _validate_source_registry(root_path, errors)
    _validate_step_catalog(root_path, known_sources, errors)
    return errors
