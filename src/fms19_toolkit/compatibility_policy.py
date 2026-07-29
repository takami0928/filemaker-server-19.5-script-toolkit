from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from .compatibility import (
    CONTEXTS,
    RENDERER_STATUSES,
    SUPPORT_VALUES,
    TARGET,
    CompatibilityCatalogError,
    build_normalized_catalog,
    build_normalized_sources,
    derive_renderer_metadata,
)


STEP_FIELDS = {
    "name",
    "category",
    "availableIn19_5",
    "introducedIn",
    "serverSupportIntroducedIn",
    "execution",
    "summary",
    "options",
    "contextRequirements",
    "contextEffects",
    "dialogBehavior",
    "risks",
    "commonErrors",
    "sourceIds",
    "confidence",
    "researchStatus",
    "researchEvidence",
    "compatibilityBasis",
    "versionTransitions",
}
SOURCE_FIELDS = {
    "id",
    "title",
    "url",
    "sourceType",
    "publisher",
    "targetVersion",
    "scope",
    "retrievedAt",
    "status",
    "relevantSections",
    "notes",
}
VERSION_RE = re.compile(r"^\s*(\d+)(?:\.(\d+))?(?:\.(\d+))?")
ANY_VERSION_RE = re.compile(r"(?<!\d)(\d+)\.(\d+)(?:\.(\d+))?")


def _load_json(path: Path, errors: list[str]) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing compatibility JSON file: {path}")
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"invalid compatibility JSON in {path}: {exc}")
    return None


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


def _describes_later_or_current_source(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    if "current" in value.casefold():
        return True
    return any(
        (int(match.group(1)), int(match.group(2))) > (19, 5)
        for match in ANY_VERSION_RE.finditer(value)
    )


def _duplicates(values: list[str]) -> set[str]:
    seen: set[str] = set()
    duplicate: set[str] = set()
    for value in values:
        normalized = value.strip().casefold()
        if normalized in seen:
            duplicate.add(value)
        seen.add(normalized)
    return duplicate


def _has_partial_conditions(step: dict[str, Any]) -> bool:
    if any(
        isinstance(step.get(field), list) and bool(step[field])
        for field in (
            "options",
            "contextRequirements",
            "contextEffects",
            "risks",
            "versionTransitions",
        )
    ):
        return True
    dialog = step.get("dialogBehavior")
    return isinstance(dialog, str) and bool(dialog.strip())


def _validate_source_registry(
    sources_data: Any,
    research_sources: Any,
    errors: list[str],
) -> set[str]:
    label = "compatibility sources"
    if not isinstance(sources_data, dict):
        errors.append(f"{label}: root must be an object")
        return set()
    expected_root_fields = {
        "schemaVersion",
        "target",
        "classification",
        "derivedFrom",
        "scope",
        "sources",
    }
    if set(sources_data) != expected_root_fields:
        errors.append(f"{label}: unexpected or missing root fields")
    if sources_data.get("schemaVersion") != 1:
        errors.append(f"{label}: schemaVersion must be 1")
    if sources_data.get("target") != TARGET:
        errors.append(f"{label}: target must be FileMaker Pro/Server 19.5")
    if sources_data.get("classification") != "compatibility-source-registry":
        errors.append(
            f"{label}: classification must be compatibility-source-registry"
        )

    sources = sources_data.get("sources")
    if not isinstance(sources, list):
        errors.append(f"{label}: sources must be an array")
        return set()
    declared_count = (
        sources_data.get("scope", {}).get("sourceCount")
        if isinstance(sources_data.get("scope"), dict)
        else None
    )
    if declared_count != len(sources):
        errors.append(
            f"{label}: sourceCount mismatch; "
            f"declared={declared_count!r}, actual={len(sources)}"
        )

    source_ids: list[str] = []
    for index, source in enumerate(sources):
        item_label = f"{label}[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{item_label}: source must be an object")
            continue
        if set(source) != SOURCE_FIELDS:
            errors.append(f"{item_label}: unexpected or missing source fields")
        source_id = source.get("id")
        if not isinstance(source_id, str) or not source_id.strip():
            errors.append(f"{item_label}: source ID must be a non-empty string")
        else:
            source_ids.append(source_id)
        if source.get("sourceType") not in {"primary", "secondary"}:
            errors.append(f"{item_label}: invalid sourceType")

    duplicate_ids = _duplicates(source_ids)
    if duplicate_ids:
        errors.append(
            f"{label}: duplicate source ID(s): {sorted(duplicate_ids)}"
        )

    if isinstance(research_sources, dict):
        research_entries = research_sources.get("sources")
        if not isinstance(research_entries, list):
            errors.append(
                f"{label}: research-candidate sources must be an array"
            )
            research_entries = []
        research_by_id = {
            source.get("id"): source
            for source in research_entries
            if isinstance(source, dict)
            and isinstance(source.get("id"), str)
        }
        for source in sources:
            if not isinstance(source, dict):
                continue
            source_id = source.get("id")
            research_source = research_by_id.get(source_id)
            if research_source is None:
                errors.append(
                    f"{label}: source {source_id!r} has no research-candidate mapping"
                )
                continue
            if source.get("sourceType") != research_source.get("sourceType"):
                errors.append(
                    f"{label}: source {source_id!r} changes research sourceType "
                    "and may promote secondary evidence"
                )
            if source != research_source:
                errors.append(
                    f"{label}: source {source_id!r} lost or changed "
                    "research-candidate information"
                )
    return set(source_ids)


def _validate_step_catalog(
    catalog: Any,
    known_sources: set[str],
    research_catalog: Any,
    errors: list[str],
) -> list[dict[str, Any]]:
    label = "compatibility catalog"
    if not isinstance(catalog, dict):
        errors.append(f"{label}: root must be an object")
        return []
    expected_root_fields = {
        "schemaVersion",
        "target",
        "classification",
        "derivedFrom",
        "scope",
        "policy",
        "contexts",
        "supportValues",
        "steps",
    }
    if set(catalog) != expected_root_fields:
        errors.append(f"{label}: unexpected or missing root fields")
    if catalog.get("schemaVersion") != 1:
        errors.append(f"{label}: schemaVersion must be 1")
    if catalog.get("target") != TARGET:
        errors.append(f"{label}: target must be FileMaker Pro/Server 19.5")
    if catalog.get("classification") != "compatibility-reference":
        errors.append(
            f"{label}: compatibility data must not be classified as "
            "research-candidate or verified renderer data"
        )
    if catalog.get("contexts") != list(CONTEXTS):
        errors.append(f"{label}: contexts must use the canonical ordered set")
    if catalog.get("supportValues") != list(SUPPORT_VALUES):
        errors.append(f"{label}: supportValues must use the closed enumeration")
    expected_policy = {
        "unknown": "fail-closed",
        "partial": "requires documented conditions or constraints",
        "laterServerSupport": "must not be backported to 19.5",
        "rendererStatus": "derived from catalog/fm19.5/verified-steps.json",
    }
    if catalog.get("policy") != expected_policy:
        errors.append(
            f"{label}: unknown, partial, later-version, and renderer policies "
            "must remain fail-closed"
        )

    steps = catalog.get("steps")
    if not isinstance(steps, list):
        errors.append(f"{label}: steps must be an array")
        return []
    declared_count = (
        catalog.get("scope", {}).get("stepCount")
        if isinstance(catalog.get("scope"), dict)
        else None
    )
    if declared_count != len(steps):
        errors.append(
            f"{label}: stepCount mismatch; "
            f"declared={declared_count!r}, actual={len(steps)}"
        )

    names: list[str] = []
    for index, step in enumerate(steps):
        item_label = f"{label}.steps[{index}]"
        if not isinstance(step, dict):
            errors.append(f"{item_label}: step must be an object")
            continue
        if set(step) != STEP_FIELDS:
            errors.append(
                f"{item_label}: unexpected or missing fields; renderer status "
                "must not be stored in the compatibility catalog"
            )
        name = step.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"{item_label}: name must be a non-empty string")
        else:
            names.append(name)
        if not isinstance(step.get("category"), str) or not step["category"].strip():
            errors.append(f"{item_label}: category must be a non-empty string")
        if not isinstance(step.get("availableIn19_5"), bool):
            errors.append(f"{item_label}: availableIn19_5 must be a boolean")
        if not isinstance(step.get("introducedIn"), str):
            errors.append(f"{item_label}: introducedIn must be a string")
        server_introduced = step.get("serverSupportIntroducedIn")
        if server_introduced is not None and not isinstance(
            server_introduced,
            str,
        ):
            errors.append(
                f"{item_label}: serverSupportIntroducedIn must be string or null"
            )
        execution = step.get("execution")
        if not isinstance(execution, dict):
            errors.append(f"{item_label}: execution must be an object")
        else:
            if set(execution) != set(CONTEXTS):
                errors.append(
                    f"{item_label}: execution must contain every canonical context"
                )
            invalid = [
                value
                for value in execution.values()
                if value not in SUPPORT_VALUES
            ]
            if invalid:
                errors.append(
                    f"{item_label}: invalid compatibility value(s): "
                    f"{sorted(invalid, key=repr)}"
                )
            if (
                "partial" in execution.values()
                and not _has_partial_conditions(step)
            ):
                errors.append(
                    f"{item_label}: partial compatibility requires documented "
                    "conditions or constraints"
                )
            if _after_19_5(server_introduced):
                for context in ("psos", "server_schedule"):
                    if execution.get(context) != "unavailable":
                        errors.append(
                            f"{item_label}: Server support introduced after 19.5 "
                            f"must not be backported to {context}"
                        )
        if (
            _after_19_5(step.get("introducedIn"))
            and step.get("availableIn19_5") is True
        ):
            errors.append(
                f"{item_label}: step introduced after 19.5 cannot be available"
            )

        source_ids = step.get("sourceIds")
        if not isinstance(source_ids, list) or not source_ids:
            errors.append(
                f"{item_label}: sourceIds must be a non-empty array"
            )
        elif any(
            not isinstance(source_id, str) or not source_id.strip()
            for source_id in source_ids
        ):
            errors.append(f"{item_label}: source IDs must be non-empty strings")
        else:
            unknown = set(source_ids) - known_sources
            if unknown:
                errors.append(
                    f"{item_label}: unknown source ID(s): {sorted(unknown)}"
                )
        research_evidence = step.get("researchEvidence")
        if (
            not isinstance(research_evidence, list)
            or step.get("researchStatus") not in research_evidence
        ):
            errors.append(
                f"{item_label}: researchStatus must be backed by researchEvidence"
            )
        if any(field in step for field in ("rendererStatus", "fmxmlsnippet", "id")):
            errors.append(
                f"{item_label}: compatibility data must not contain renderer "
                "or clipboard implementation fields"
            )

    duplicate_names = _duplicates(names)
    if duplicate_names:
        errors.append(
            f"{label}: duplicate step name(s): {sorted(duplicate_names)}"
        )

    if isinstance(research_catalog, dict):
        try:
            expected = build_normalized_catalog(research_catalog)
        except (CompatibilityCatalogError, KeyError, TypeError) as exc:
            errors.append(f"{label}: unable to normalize research data: {exc}")
        else:
            expected_names = {
                step["name"].casefold()
                for step in expected["steps"]
            }
            actual_names = {
                step.get("name", "").casefold()
                for step in steps
                if isinstance(step, dict)
                and isinstance(step.get("name"), str)
            }
            if actual_names != expected_names:
                errors.append(
                    f"{label}: normalized scope must include every research "
                    "candidate step exactly once"
                )
            expected_by_name = {
                step["name"].casefold(): step
                for step in expected["steps"]
            }
            for step in steps:
                if not isinstance(step, dict) or not isinstance(
                    step.get("name"),
                    str,
                ):
                    continue
                expected_step = expected_by_name.get(step["name"].casefold())
                if expected_step is not None and step != expected_step:
                    errors.append(
                        f"{label}: {step['name']!r} differs from the deterministic "
                        "research normalization"
                    )
    return [step for step in steps if isinstance(step, dict)]


def _validate_renderer_derivation(
    steps: list[dict[str, Any]],
    verified_catalog: Any,
    errors: list[str],
) -> None:
    label = "renderer status derivation"
    if not isinstance(verified_catalog, dict):
        errors.append(f"{label}: verified catalog root must be an object")
        return
    verified_steps = verified_catalog.get("steps")
    if not isinstance(verified_steps, list):
        errors.append(f"{label}: verified catalog steps must be an array")
        return
    for index, entry in enumerate(verified_steps):
        if not isinstance(entry, dict):
            continue
        evidence = entry.get("evidence")
        evidence_set = (
            {
                value
                for value in evidence
                if isinstance(value, str)
            }
            if isinstance(evidence, list)
            else set()
        )
        if (
            entry.get("status") == "supported"
            and "fm19_5_paste_verified" not in evidence_set
        ):
            errors.append(
                f"{label}: verified promotion for {entry.get('name')!r} "
                "requires fm19_5_paste_verified evidence"
            )

    for step in steps:
        try:
            derived = derive_renderer_metadata(step["name"], verified_catalog)
        except CompatibilityCatalogError as exc:
            errors.append(f"{label}: {exc}")
            return
        if derived["rendererStatus"] not in RENDERER_STATUSES:
            errors.append(
                f"{label}: invalid derived status for {step.get('name')!r}"
            )
        if (
            derived["rendererStatus"] == "verified"
            and "fm19_5_paste_verified"
            not in set(derived["rendererEvidence"])
        ):
            errors.append(
                f"{label}: {step.get('name')!r} is verified without "
                "FileMaker Pro 19.5 fixture evidence"
            )


def _validate_later_source_usage(
    steps: list[dict[str, Any]],
    sources_data: Any,
    errors: list[str],
) -> None:
    if not isinstance(sources_data, dict):
        return
    source_entries = sources_data.get("sources")
    if not isinstance(source_entries, list):
        return
    later_source_ids = {
        source.get("id")
        for source in source_entries
        if isinstance(source, dict)
        and isinstance(source.get("id"), str)
        and _describes_later_or_current_source(source.get("targetVersion"))
    }
    for step in steps:
        direct_ids = step.get("sourceIds")
        if not isinstance(direct_ids, list):
            continue
        used_later_ids = {
            source_id
            for source_id in direct_ids
            if isinstance(source_id, str)
        } & later_source_ids
        if not used_later_ids:
            continue
        transition_ids: set[str] = set()
        transitions = step.get("versionTransitions")
        if isinstance(transitions, list):
            for transition in transitions:
                if (
                    isinstance(transition, dict)
                    and _after_19_5(transition.get("fromVersion"))
                    and isinstance(transition.get("sourceIds"), list)
                ):
                    transition_ids.update(
                        source_id
                        for source_id in transition["sourceIds"]
                        if isinstance(source_id, str)
                    )
        unconditional = used_later_ids - transition_ids
        if unconditional:
            errors.append(
                "compatibility catalog: "
                f"{step.get('name')!r} uses later/current source(s) "
                f"{sorted(unconditional)} without an explicit post-19.5 "
                "version transition"
            )


def _validate_compatibility_documents(
    catalog: Any,
    sources_data: Any,
    research_catalog: Any,
    research_sources: Any,
    verified_catalog: Any,
    errors: list[str],
) -> None:
    known_sources = _validate_source_registry(
        sources_data,
        research_sources,
        errors,
    )
    steps = _validate_step_catalog(
        catalog,
        known_sources,
        research_catalog,
        errors,
    )
    _validate_later_source_usage(steps, sources_data, errors)
    if isinstance(research_catalog, dict) and isinstance(research_sources, dict):
        try:
            expected_sources = build_normalized_sources(
                research_catalog,
                research_sources,
            )
        except (CompatibilityCatalogError, KeyError, TypeError) as exc:
            errors.append(
                f"compatibility sources: unable to normalize research data: {exc}"
            )
        else:
            if sources_data != expected_sources:
                errors.append(
                    "compatibility sources: committed registry differs from "
                    "the deterministic referenced-source normalization"
                )
    _validate_renderer_derivation(steps, verified_catalog, errors)


def validate_compatibility_catalog(root: str | Path) -> list[str]:
    root_path = Path(root).resolve()
    errors: list[str] = []
    catalog = _load_json(
        root_path / "catalog/fm19.5/compatibility/script-steps.json",
        errors,
    )
    sources_data = _load_json(
        root_path / "catalog/fm19.5/compatibility/sources.json",
        errors,
    )
    research_catalog = _load_json(
        root_path
        / "research/issue-7/candidates/script-step-catalog-candidates.json",
        errors,
    )
    research_sources = _load_json(
        root_path
        / "research/issue-7/candidates/source-registry-candidates.json",
        errors,
    )
    verified_catalog = _load_json(
        root_path / "catalog/fm19.5/verified-steps.json",
        errors,
    )
    if all(
        document is not None
        for document in (
            catalog,
            sources_data,
            research_catalog,
            research_sources,
            verified_catalog,
        )
    ):
        _validate_compatibility_documents(
            catalog,
            sources_data,
            research_catalog,
            research_sources,
            verified_catalog,
            errors,
        )
    return errors
