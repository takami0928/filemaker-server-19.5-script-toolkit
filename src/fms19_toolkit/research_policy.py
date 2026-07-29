from __future__ import annotations

import argparse
from collections.abc import Iterable
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any


ISSUE_7_TARGET = "FileMaker Server 19.5 / FileMaker Pro 19.5"
ISSUE_7_CLASSIFICATION = "research-candidate"
TARGET_VERSION = (19, 5)

OUTER_FILE_PATHS = (
    "candidates/deep-research-report.md",
    "candidates/source-registry-candidates.json",
    "candidates/script-step-catalog-candidates.json",
    "candidates/unresolved-questions.json",
    "candidates/coverage-audit.json",
    "candidates/revision-notes.md",
    "candidates/manifest.json",
)
INNER_FILE_PATHS = (
    "deep-research-report.md",
    "source-registry-candidates.json",
    "script-step-catalog-candidates.json",
    "unresolved-questions.json",
    "coverage-audit.json",
    "revision-notes.md",
)
JSON_FILE_PATHS = {
    "candidates/source-registry-candidates.json",
    "candidates/script-step-catalog-candidates.json",
    "candidates/unresolved-questions.json",
    "candidates/coverage-audit.json",
    "candidates/manifest.json",
}
LEGACY_DUPLICATE_PATHS = (
    "coverage-audit.json",
    "unresolved-questions.json",
    "revision-notes.md",
)
EXPECTED_COUNTS = {
    "sources": 110,
    "steps": 59,
    "requestedHighPrioritySteps": "51/51",
    "additionalAuditedSteps": 8,
    "functions": 24,
    "errors": 117,
    "exclusionsAndTransitions": 15,
    "unresolvedQuestions": 20,
    "coverageDomains": 18,
}
EXPECTED_ZERO_COUNTS = {
    "duplicateSourceIds": 0,
    "duplicateStepNames": 0,
    "unknownSourceReferences": 0,
    "numericFmxmlsnippetIdsAsserted": 0,
}
DEVICE_EVIDENCE = {
    "fm19_5_paste_verified",
    "fm19_5_runtime_verified",
    "fmse_verified",
}
VERSION_RE = re.compile(r"^\s*(\d+)(?:\.(\d+))?(?:\.(\d+))?")


def _read_utf8(path: Path, label: str, errors: list[str]) -> bytes | None:
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        errors.append(f"{label}: required file is missing")
        return None
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        errors.append(f"{label}: file is not valid UTF-8: {exc}")
        return None
    return raw


def _parse_json(raw: bytes | None, label: str, errors: list[str]) -> Any | None:
    if raw is None:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"{label}: invalid JSON: {exc}")
        return None


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _validate_manifest_entries(
    base: Path,
    entries: Any,
    expected_paths: tuple[str, ...],
    label: str,
    errors: list[str],
) -> dict[str, bytes]:
    if not isinstance(entries, list):
        errors.append(f"{label}: files must be an array")
        return {}

    expected = set(expected_paths)
    seen: set[str] = set()
    loaded: dict[str, bytes] = {}
    for index, entry in enumerate(entries):
        entry_label = f"{label}.files[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{entry_label}: entry must be an object")
            continue
        if set(entry) != {"path", "bytes", "sha256"}:
            errors.append(
                f"{entry_label}: fields must be path, bytes, and sha256"
            )
        relative = entry.get("path")
        if not isinstance(relative, str):
            errors.append(f"{entry_label}: path must be a string")
            continue
        pure_path = PurePosixPath(relative)
        if (
            pure_path.is_absolute()
            or ".." in pure_path.parts
            or "\\" in relative
        ):
            errors.append(f"{entry_label}: path must be a safe POSIX relative path")
            continue
        if relative in seen:
            errors.append(f"{entry_label}: duplicate manifest path: {relative}")
            continue
        seen.add(relative)
        if relative not in expected:
            errors.append(f"{entry_label}: unexpected manifest path: {relative}")
            continue

        path = base.joinpath(*pure_path.parts)
        raw = _read_utf8(path, entry_label, errors)
        if raw is None:
            continue
        loaded[relative] = raw
        declared_bytes = entry.get("bytes")
        if (
            not isinstance(declared_bytes, int)
            or isinstance(declared_bytes, bool)
            or declared_bytes != len(raw)
        ):
            errors.append(
                f"{entry_label}: manifest bytes mismatch for {relative}; "
                f"declared={declared_bytes!r}, actual={len(raw)}"
            )
        declared_hash = entry.get("sha256")
        actual_hash = _sha256(raw)
        if declared_hash != actual_hash:
            errors.append(
                f"{entry_label}: manifest SHA-256 mismatch for {relative}; "
                f"declared={declared_hash!r}, actual={actual_hash}"
            )

    missing = expected - seen
    if missing:
        errors.append(f"{label}: missing manifest paths: {sorted(missing)}")
    return loaded


def _validate_outer_manifest_files(
    issue_root: Path,
    manifest: Any,
    errors: list[str],
) -> dict[str, Any]:
    if not isinstance(manifest, dict):
        errors.append("research/issue-7/manifest.json: root must be an object")
        return {}
    label = "research/issue-7/manifest.json"
    if manifest.get("schemaVersion") != 3:
        errors.append(f"{label}: schemaVersion must be 3")
    if manifest.get("issue") != 7:
        errors.append(f"{label}: issue must be 7")
    if manifest.get("target") != ISSUE_7_TARGET:
        errors.append(f"{label}: target must remain {ISSUE_7_TARGET!r}")
    if manifest.get("classification") != ISSUE_7_CLASSIFICATION:
        errors.append(f"{label}: classification must be research-candidate")
    if manifest.get("canonicalRoot") != "candidates":
        errors.append(f"{label}: canonicalRoot must be candidates")

    raw_files = _validate_manifest_entries(
        issue_root,
        manifest.get("files"),
        OUTER_FILE_PATHS,
        label,
        errors,
    )
    parsed: dict[str, Any] = {}
    for relative in JSON_FILE_PATHS:
        if relative in raw_files:
            parsed[relative] = _parse_json(
                raw_files[relative],
                f"{label}:{relative}",
                errors,
            )
    return parsed


def _validate_candidate_manifest(
    candidates_root: Path,
    manifest: Any,
    errors: list[str],
) -> None:
    label = "research/issue-7/candidates/manifest.json"
    if not isinstance(manifest, dict):
        errors.append(f"{label}: root must be an object")
        return
    if manifest.get("schemaVersion") != 1:
        errors.append(f"{label}: schemaVersion must be 1")
    if manifest.get("issue") != 7:
        errors.append(f"{label}: issue must be 7")
    if manifest.get("target") != ISSUE_7_TARGET:
        errors.append(f"{label}: target must remain {ISSUE_7_TARGET!r}")
    if manifest.get("classification") != ISSUE_7_CLASSIFICATION:
        errors.append(f"{label}: classification must be research-candidate")
    _validate_manifest_entries(
        candidates_root,
        manifest.get("files"),
        INNER_FILE_PATHS,
        label,
        errors,
    )


def _duplicates(values: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def _string_ids(
    items: Any,
    field: str,
    label: str,
    errors: list[str],
) -> list[str]:
    if not isinstance(items, list):
        errors.append(f"{label}: expected an array")
        return []
    values: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"{label}[{index}]: entry must be an object")
            continue
        value = item.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{label}[{index}].{field}: must be a non-empty string")
            continue
        values.append(value)
    return values


def _collect_source_ids(
    value: Any,
    label: str,
    errors: list[str],
) -> list[str]:
    references: list[str] = []

    def walk(item: Any, path: str) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                child_path = f"{path}.{key}"
                if key == "sourceIds":
                    if not isinstance(child, list):
                        errors.append(f"{child_path}: sourceIds must be an array")
                    elif any(not isinstance(source_id, str) for source_id in child):
                        errors.append(f"{child_path}: sourceIds must contain strings")
                    else:
                        references.extend(child)
                else:
                    walk(child, child_path)
        elif isinstance(item, list):
            for index, child in enumerate(item):
                walk(child, f"{path}[{index}]")

    walk(value, label)
    return references


def _leading_version(value: Any) -> tuple[int, int, int] | None:
    if not isinstance(value, str):
        return None
    match = VERSION_RE.match(value)
    if match is None:
        return None
    parts = tuple(int(part or 0) for part in match.groups())
    return parts


def _after_target(version: tuple[int, int, int] | None) -> bool:
    return version is not None and version[:2] > TARGET_VERSION


def _nonempty_strings(value: Any) -> bool:
    return isinstance(value, list) and any(
        isinstance(item, str) and item.strip() for item in value
    )


def _has_partial_rule(step: dict[str, Any]) -> bool:
    options = step.get("options")
    if isinstance(options, list):
        for option in options:
            if not isinstance(option, dict):
                continue
            name = option.get("option")
            detail = option.get("effect") or option.get("executionNotes")
            if (
                isinstance(name, str)
                and name.strip()
                and isinstance(detail, str)
                and detail.strip()
            ):
                return True
    dialog = step.get("dialogBehavior")
    if isinstance(dialog, str) and dialog.strip():
        return True
    if _nonempty_strings(step.get("contextRequirements")):
        return True
    if _nonempty_strings(step.get("risks")):
        return True
    transitions = step.get("versionTransitions")
    return isinstance(transitions, list) and any(
        isinstance(item, dict)
        and isinstance(item.get("change"), str)
        and item["change"].strip()
        for item in transitions
    )


def _numeric_fmxmlsnippet_ids(
    steps: list[Any],
    errors: list[str],
) -> int:
    count = 0
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        snippet = step.get("fmxmlsnippet")
        label = f"research step[{index}].fmxmlsnippet"
        if not isinstance(snippet, dict):
            errors.append(f"{label}: must be an object")
            continue
        step_id = snippet.get("stepId")
        numeric = (
            isinstance(step_id, int)
            and not isinstance(step_id, bool)
        ) or (
            isinstance(step_id, str)
            and step_id.strip().isdigit()
        )
        if numeric:
            count += 1
            errors.append(
                f"{label}: numeric clipboard fmxmlsnippet ID is asserted without "
                "FileMaker Pro 19.5 fixture provenance"
            )
        if snippet.get("evidenceStatus") != "unverified":
            errors.append(
                f"{label}: evidenceStatus must remain unverified until a "
                "FileMaker Pro 19.5 fixture exists"
            )
    return count


def _validate_candidate_evidence(value: Any, label: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_label = f"{label}.{key}"
            if key == "evidence" and isinstance(child, list):
                promoted = DEVICE_EVIDENCE.intersection(
                    item for item in child if isinstance(item, str)
                )
                if promoted:
                    errors.append(
                        f"{child_label}: research candidate claims device evidence "
                        f"{sorted(promoted)}"
                    )
            _validate_candidate_evidence(child, child_label, errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_candidate_evidence(child, f"{label}[{index}]", errors)


def _validate_compatibility(
    sources: list[Any],
    catalog: dict[str, Any],
    errors: list[str],
) -> int:
    policy = catalog.get("policy")
    if not isinstance(policy, dict):
        errors.append("research catalog: policy must be an object")
        policy = {}
    if policy.get("compatibility") != "deny-by-default":
        errors.append(
            "research catalog: compatibility policy must be deny-by-default"
        )
    unknown_rule = policy.get("unknown")
    if (
        not isinstance(unknown_rule, str)
        or "never infer support" not in unknown_rule.lower()
    ):
        errors.append(
            "research catalog: unknown compatibility must never be treated as available"
        )
    partial_rule = policy.get("partial")
    if (
        not isinstance(partial_rule, str)
        or "option-level" not in partial_rule.lower()
    ):
        errors.append(
            "research catalog: partial compatibility policy must require "
            "option-level rules"
        )
    later_rule = policy.get("laterVersion")
    if (
        not isinstance(later_rule, str)
        or "excluded" not in later_rule.lower()
    ):
        errors.append(
            "research catalog: later-version compatibility must remain excluded"
        )
    snippet_rule = policy.get("fmxmlsnippet")
    if (
        not isinstance(snippet_rule, str)
        or "no numeric id" not in snippet_rule.lower()
        or "19.5 fixture provenance" not in snippet_rule.lower()
    ):
        errors.append(
            "research catalog: DDR XML IDs must not be treated as clipboard "
            "fmxmlsnippet IDs without 19.5 fixture provenance"
        )

    steps_value = catalog.get("steps")
    steps = steps_value if isinstance(steps_value, list) else []
    if not isinstance(steps_value, list):
        errors.append("research catalog: steps must be an array")
    for index, step in enumerate(steps):
        label = f"research step[{index}]"
        if not isinstance(step, dict):
            errors.append(f"{label}: must be an object")
            continue
        if "introducedIn" not in step or "serverSupportIntroducedIn" not in step:
            errors.append(
                f"{label}: introducedIn and serverSupportIntroducedIn must both "
                "be represented independently"
            )
        available = step.get("availableIn19_5")
        if not isinstance(available, bool):
            errors.append(f"{label}: availableIn19_5 must be a boolean")
        introduced = _leading_version(step.get("introducedIn"))
        if _after_target(introduced) and available is True:
            errors.append(
                f"{label}: feature introduced after 19.5 is backported as available"
            )

        execution = step.get("execution")
        if not isinstance(execution, dict):
            errors.append(f"{label}: execution must be an object")
            continue
        for mode, support in execution.items():
            valid_support = (
                isinstance(support, bool)
                or support is None
                or (
                    isinstance(support, str)
                    and support in {"partial", "unknown"}
                )
            )
            if not valid_support:
                errors.append(
                    f"{label}.execution.{mode}: unknown must not be treated as "
                    f"available; got {support!r}"
                )
        if any(value == "partial" for value in execution.values()) and not _has_partial_rule(step):
            errors.append(
                f"{label}: partial compatibility requires an option-level "
                "description or explicit compatibility rule"
            )

        server_support = _leading_version(step.get("serverSupportIntroducedIn"))
        if _after_target(server_support):
            for mode in ("psos", "serverSchedule"):
                if execution.get(mode) is not False:
                    errors.append(
                        f"{label}.execution.{mode}: later server support "
                        "introduced after 19.5 must not be backported; "
                        "serverSupportIntroducedIn must be evaluated independently "
                        "from introducedIn"
                    )

    exclusions_value = catalog.get("laterVersionExclusions")
    exclusions = exclusions_value if isinstance(exclusions_value, list) else []
    if not isinstance(exclusions_value, list):
        errors.append("research catalog: laterVersionExclusions must be an array")
    for index, exclusion in enumerate(exclusions):
        label = f"laterVersionExclusions[{index}]"
        if not isinstance(exclusion, dict):
            errors.append(f"{label}: must be an object")
            continue
        if exclusion.get("availableIn19_5") is not False:
            errors.append(
                f"{label}: later-version feature must not be backported to 19.5"
            )
        originated = _leading_version(exclusion.get("originatedIn"))
        if originated is not None and not _after_target(originated):
            errors.append(
                f"{label}: originatedIn must identify a release after 19.5"
            )

    public_fixture = next(
        (
            source
            for source in sources
            if isinstance(source, dict)
            and source.get("id") == "agentic-fm-public-implementation"
        ),
        None,
    )
    if not isinstance(public_fixture, dict):
        errors.append(
            "research sources: public fixture candidate boundary record is missing"
        )
    else:
        boundary_text = " ".join(
            str(public_fixture.get(field, ""))
            for field in ("targetVersion", "scope", "notes")
        ).lower()
        if (
            public_fixture.get("sourceType") != "secondary"
            or "not independently proven" not in boundary_text
            or "never sufficient" not in boundary_text
        ):
            errors.append(
                "research sources: public fixture must remain secondary and must "
                "not be treated as FileMaker Pro 19.5 device evidence"
            )

    return _numeric_fmxmlsnippet_ids(steps, errors)


def _validate_declared_counts(
    manifest: Any,
    actual_counts: dict[str, Any],
    label: str,
    errors: list[str],
) -> None:
    if not isinstance(manifest, dict):
        return
    validation = manifest.get("validation")
    if not isinstance(validation, dict):
        errors.append(f"{label}: validation must be an object")
        return
    for name, expected in EXPECTED_COUNTS.items():
        actual = actual_counts.get(name)
        declared = validation.get(name)
        if declared != actual or actual != expected:
            errors.append(
                f"{label}: manifest count mismatch for {name}; "
                f"declared={declared!r}, actual={actual!r}, expected={expected!r}"
            )
    for name, expected in EXPECTED_ZERO_COUNTS.items():
        actual = actual_counts.get(name)
        declared = validation.get(name)
        if declared != actual or actual != expected:
            errors.append(
                f"{label}: manifest count mismatch for {name}; "
                f"declared={declared!r}, actual={actual!r}, expected={expected!r}"
            )


def _validate_candidate_documents(
    source_registry: Any,
    catalog: Any,
    unresolved: Any,
    coverage: Any,
    outer_manifest: Any,
    candidate_manifest: Any,
    errors: list[str],
) -> None:
    if not isinstance(source_registry, dict):
        errors.append("research source registry: root must be an object")
        return
    if not isinstance(catalog, dict):
        errors.append("research catalog: root must be an object")
        return
    if not isinstance(unresolved, dict):
        errors.append("research unresolved questions: root must be an object")
        return
    if not isinstance(coverage, dict):
        errors.append("research coverage audit: root must be an object")
        return

    sources_value = source_registry.get("sources")
    sources = sources_value if isinstance(sources_value, list) else []
    source_ids = _string_ids(sources_value, "id", "research sources", errors)
    duplicate_source_ids = _duplicates(source_ids)
    if duplicate_source_ids:
        errors.append(
            f"research sources: duplicate source ID(s): {sorted(duplicate_source_ids)}"
        )

    steps_value = catalog.get("steps")
    steps = steps_value if isinstance(steps_value, list) else []
    step_names = _string_ids(steps_value, "name", "research steps", errors)
    duplicate_step_names = _duplicates(step_names)
    if duplicate_step_names:
        errors.append(
            f"research catalog: duplicate step name(s): {sorted(duplicate_step_names)}"
        )

    questions_value = unresolved.get("questions")
    questions = questions_value if isinstance(questions_value, list) else []
    unresolved_ids = _string_ids(
        questions_value,
        "id",
        "research unresolved questions",
        errors,
    )
    duplicate_unresolved_ids = _duplicates(unresolved_ids)
    if duplicate_unresolved_ids:
        errors.append(
            "research unresolved questions: duplicate unresolved ID(s): "
            f"{sorted(duplicate_unresolved_ids)}"
        )

    source_references = _collect_source_ids(
        [catalog, unresolved, coverage],
        "research candidates",
        errors,
    )
    unknown_source_references = sorted(set(source_references) - set(source_ids))
    if unknown_source_references:
        errors.append(
            "research candidates: unknown source reference(s): "
            f"{unknown_source_references}"
        )

    coverage_references = coverage.get("unresolvedQuestionIds")
    if not isinstance(coverage_references, list) or any(
        not isinstance(item, str) for item in coverage_references
    ):
        errors.append(
            "research coverage audit: unresolvedQuestionIds must be an array of strings"
        )
        coverage_references = []
    duplicate_coverage_references = _duplicates(coverage_references)
    if duplicate_coverage_references:
        errors.append(
            "research coverage audit: duplicate unresolved reference(s): "
            f"{sorted(duplicate_coverage_references)}"
        )
    unknown_unresolved = sorted(set(coverage_references) - set(unresolved_ids))
    if unknown_unresolved:
        errors.append(
            "research coverage audit references unknown unresolved ID(s): "
            f"{unknown_unresolved}"
        )

    numeric_ids = _validate_compatibility(sources, catalog, errors)
    _validate_candidate_evidence(
        [catalog, unresolved, coverage],
        "research candidates",
        errors,
    )

    functions = catalog.get("functions")
    errors_catalog = catalog.get("errors")
    exclusions = catalog.get("laterVersionExclusions")
    domains = coverage.get("domains")
    summary = catalog.get("coverageAuditSummary")
    if not isinstance(summary, dict):
        errors.append("research catalog: coverageAuditSummary must be an object")
        summary = {}
    summary_checks = {
        "totalStepEntries": len(steps),
        "functionEntries": len(functions) if isinstance(functions, list) else 0,
        "errorEntries": len(errors_catalog) if isinstance(errors_catalog, list) else 0,
        "exclusionEntries": len(exclusions) if isinstance(exclusions, list) else 0,
        "unresolvedQuestions": len(questions),
    }
    for name, actual in summary_checks.items():
        if summary.get(name) != actual:
            errors.append(
                f"research catalog: coverageAuditSummary.{name} mismatch; "
                f"declared={summary.get(name)!r}, actual={actual}"
            )

    requested = summary.get("requestedHighPrioritySteps")
    actual_counts = {
        "sources": len(sources),
        "steps": len(steps),
        "requestedHighPrioritySteps": (
            f"{requested}/51"
            if isinstance(requested, int) and not isinstance(requested, bool)
            else requested
        ),
        "additionalAuditedSteps": summary.get("additionalSteps"),
        "functions": len(functions) if isinstance(functions, list) else 0,
        "errors": len(errors_catalog) if isinstance(errors_catalog, list) else 0,
        "exclusionsAndTransitions": (
            len(exclusions) if isinstance(exclusions, list) else 0
        ),
        "unresolvedQuestions": len(questions),
        "coverageDomains": len(domains) if isinstance(domains, list) else 0,
        "duplicateSourceIds": len(duplicate_source_ids),
        "duplicateStepNames": len(duplicate_step_names),
        "unknownSourceReferences": len(unknown_source_references),
        "numericFmxmlsnippetIdsAsserted": numeric_ids,
    }
    _validate_declared_counts(
        outer_manifest,
        actual_counts,
        "research/issue-7/manifest.json",
        errors,
    )
    _validate_declared_counts(
        candidate_manifest,
        actual_counts,
        "research/issue-7/candidates/manifest.json",
        errors,
    )

    if isinstance(outer_manifest, dict):
        validation = outer_manifest.get("validation")
        if isinstance(validation, dict):
            for name in (
                "fileMakerPro19_5PasteVerified",
                "fileMakerServer19_5RuntimeVerified",
            ):
                if validation.get(name) is not False:
                    errors.append(
                        f"research/issue-7/manifest.json: {name} must remain false"
                    )


def validate_issue_7_research(root: str | Path) -> list[str]:
    repository_root = Path(root).resolve()
    issue_root = repository_root / "research/issue-7"
    errors: list[str] = []

    readme = _read_utf8(
        issue_root / "README.md",
        "research/issue-7/README.md",
        errors,
    )
    if readme is not None and not readme.strip():
        errors.append("research/issue-7/README.md: must not be empty")

    for relative in LEGACY_DUPLICATE_PATHS:
        if (issue_root / relative).exists():
            errors.append(
                f"research/issue-7/{relative}: legacy duplicate must not exist; "
                "candidates/ is canonical"
            )
    if (issue_root / "bundle").exists():
        errors.append(
            "research/issue-7/bundle: binary bundle directory must not exist"
        )
    for path in issue_root.rglob("*"):
        if path.is_file() and (
            path.suffix.lower() == ".zip" or ".zip.part" in path.name.lower()
        ):
            errors.append(f"{path}: ZIP artifacts must not be committed")

    manifest_raw = _read_utf8(
        issue_root / "manifest.json",
        "research/issue-7/manifest.json",
        errors,
    )
    outer_manifest = _parse_json(
        manifest_raw,
        "research/issue-7/manifest.json",
        errors,
    )
    parsed = _validate_outer_manifest_files(issue_root, outer_manifest, errors)
    candidate_manifest = parsed.get("candidates/manifest.json")
    _validate_candidate_manifest(
        issue_root / "candidates",
        candidate_manifest,
        errors,
    )

    required_documents = {
        "source_registry": "candidates/source-registry-candidates.json",
        "catalog": "candidates/script-step-catalog-candidates.json",
        "unresolved": "candidates/unresolved-questions.json",
        "coverage": "candidates/coverage-audit.json",
    }
    if all(parsed.get(path) is not None for path in required_documents.values()):
        _validate_candidate_documents(
            parsed[required_documents["source_registry"]],
            parsed[required_documents["catalog"]],
            parsed[required_documents["unresolved"]],
            parsed[required_documents["coverage"]],
            outer_manifest,
            candidate_manifest,
            errors,
        )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the Issue #7 research-candidate artifacts."
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="repository root (default: current directory)",
    )
    args = parser.parse_args(argv)
    errors = validate_issue_7_research(args.root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Issue #7 research candidate checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
