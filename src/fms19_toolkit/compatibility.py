from __future__ import annotations

from copy import deepcopy
from difflib import get_close_matches
from functools import lru_cache
import json
from pathlib import Path
import sysconfig
from typing import Any


TARGET = {
    "proVersion": "19.5",
    "serverVersion": "19.5",
}
CONTEXTS = (
    "client",
    "psos",
    "server_schedule",
    "webdirect",
    "filemaker_go",
    "data_api",
    "custom_web_publishing",
)
RESEARCH_CONTEXT_KEYS = {
    "client": "client",
    "psos": "psos",
    "server_schedule": "serverSchedule",
    "webdirect": "webDirect",
    "filemaker_go": "fileMakerGo",
    "data_api": "dataApi",
    "custom_web_publishing": "customWebPublishing",
}
CONTEXT_ALIASES = {
    **{context: context for context in CONTEXTS},
    "schedule": "server_schedule",
    "server": "server_schedule",
    "web_direct": "webdirect",
    "go": "filemaker_go",
    "cwp": "custom_web_publishing",
}
SUPPORT_VALUES = (
    "available",
    "unavailable",
    "partial",
    "unknown",
)
RENDERER_STATUSES = (
    "verified",
    "experimental",
    "not_verified",
)
COMPATIBILITY_CATALOG_FILE = "script-steps.json"
COMPATIBILITY_SOURCES_FILE = "sources.json"
VERIFIED_CATALOG_FILE = "verified-steps.json"
RESEARCH_CATALOG_PATH = (
    "research/issue-7/candidates/script-step-catalog-candidates.json"
)
RESEARCH_SOURCES_PATH = (
    "research/issue-7/candidates/source-registry-candidates.json"
)


class CompatibilityCatalogError(ValueError):
    """Raised when compatibility catalog data or a query is invalid."""


def normalize_context(value: str) -> str:
    normalized = value.strip().casefold().replace("-", "_")
    try:
        return CONTEXT_ALIASES[normalized]
    except KeyError as exc:
        expected = ", ".join(CONTEXTS)
        raise CompatibilityCatalogError(
            f"unknown context {value!r}; expected one of: {expected}"
        ) from exc


def normalize_support(value: Any) -> str:
    if value is True:
        return "available"
    if value is False:
        return "unavailable"
    if value == "partial":
        return "partial"
    if value is None or value == "unknown":
        return "unknown"
    raise CompatibilityCatalogError(
        f"unsupported research compatibility value: {value!r}"
    )


def _normalize_step(step: dict[str, Any]) -> dict[str, Any]:
    evidence = step.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        research_status = "unknown"
        research_evidence: list[str] = []
    else:
        research_evidence = deepcopy(evidence)
        research_status = str(evidence[-1])

    return {
        "name": step["name"],
        "category": step["category"],
        "availableIn19_5": step["availableIn19_5"],
        "introducedIn": step["introducedIn"],
        "serverSupportIntroducedIn": step["serverSupportIntroducedIn"],
        "execution": {
            context: normalize_support(
                step["execution"].get(RESEARCH_CONTEXT_KEYS[context])
            )
            for context in CONTEXTS
        },
        "summary": step.get("notes", ""),
        "options": deepcopy(step.get("options", [])),
        "contextRequirements": deepcopy(step.get("contextRequirements", [])),
        "contextEffects": deepcopy(step.get("contextEffects", [])),
        "dialogBehavior": step.get("dialogBehavior", ""),
        "risks": deepcopy(step.get("risks", [])),
        "commonErrors": deepcopy(step.get("commonErrors", [])),
        "sourceIds": deepcopy(step.get("sourceIds", [])),
        "confidence": step.get("confidence", "unknown"),
        "researchStatus": research_status,
        "researchEvidence": research_evidence,
        "compatibilityBasis": step.get("compatibilityBasis", ""),
        "versionTransitions": deepcopy(step.get("versionTransitions", [])),
    }


def build_normalized_catalog(
    research_catalog: dict[str, Any],
) -> dict[str, Any]:
    research_steps = research_catalog.get("steps")
    if not isinstance(research_steps, list):
        raise CompatibilityCatalogError("research catalog steps must be an array")
    steps = sorted(
        (_normalize_step(step) for step in research_steps),
        key=lambda step: (
            step["category"].casefold(),
            step["name"].casefold(),
        ),
    )
    return {
        "schemaVersion": 1,
        "target": deepcopy(TARGET),
        "classification": "compatibility-reference",
        "derivedFrom": {
            "classification": "research-candidate",
            "scriptSteps": RESEARCH_CATALOG_PATH,
        },
        "scope": {
            "normalization": "all research candidate script steps",
            "stepCount": len(steps),
        },
        "policy": {
            "unknown": "fail-closed",
            "partial": "requires documented conditions or constraints",
            "laterServerSupport": "must not be backported to 19.5",
            "rendererStatus": "derived from catalog/fm19.5/verified-steps.json",
        },
        "contexts": list(CONTEXTS),
        "supportValues": list(SUPPORT_VALUES),
        "steps": steps,
    }


def _collect_step_source_ids(research_catalog: dict[str, Any]) -> set[str]:
    references: set[str] = set()

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "sourceIds" and isinstance(child, list):
                    references.update(
                        item for item in child if isinstance(item, str)
                    )
                else:
                    walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(research_catalog.get("steps", []))
    return references


def build_normalized_sources(
    research_catalog: dict[str, Any],
    research_sources: dict[str, Any],
) -> dict[str, Any]:
    referenced_ids = _collect_step_source_ids(research_catalog)
    source_entries = research_sources.get("sources")
    if not isinstance(source_entries, list):
        raise CompatibilityCatalogError("research sources must be an array")
    by_id = {
        source.get("id"): source
        for source in source_entries
        if isinstance(source, dict) and isinstance(source.get("id"), str)
    }
    missing = sorted(referenced_ids - by_id.keys())
    if missing:
        raise CompatibilityCatalogError(
            f"research catalog references missing sources: {missing}"
        )
    sources = [
        deepcopy(by_id[source_id])
        for source_id in sorted(referenced_ids)
    ]
    return {
        "schemaVersion": 1,
        "target": deepcopy(TARGET),
        "classification": "compatibility-source-registry",
        "derivedFrom": {
            "classification": "research-candidate",
            "sources": RESEARCH_SOURCES_PATH,
        },
        "scope": {
            "normalization": "sources referenced by normalized script steps",
            "sourceCount": len(sources),
        },
        "sources": sources,
    }


def _source_tree_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _installed_catalog_root() -> Path:
    return (
        Path(sysconfig.get_path("data"))
        / "share"
        / "fms19-script-toolkit"
        / "catalog"
        / "fm19.5"
    )


def _compatibility_directories() -> tuple[Path, ...]:
    return (
        _source_tree_root() / "catalog/fm19.5/compatibility",
        _installed_catalog_root() / "compatibility",
    )


def _verified_catalog_paths() -> tuple[Path, ...]:
    return (
        _source_tree_root() / "catalog/fm19.5" / VERIFIED_CATALOG_FILE,
        _installed_catalog_root() / VERIFIED_CATALOG_FILE,
    )


def _locate_compatibility_path(filename: str) -> Path:
    for directory in _compatibility_directories():
        path = directory / filename
        if path.is_file():
            return path
    searched = ", ".join(
        str(directory / filename)
        for directory in _compatibility_directories()
    )
    raise CompatibilityCatalogError(
        f"unable to locate compatibility catalog {filename}; searched: {searched}"
    )


def _locate_verified_catalog_path() -> Path:
    for path in _verified_catalog_paths():
        if path.is_file():
            return path
    searched = ", ".join(str(path) for path in _verified_catalog_paths())
    raise CompatibilityCatalogError(
        f"unable to locate verified renderer catalog; searched: {searched}"
    )


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CompatibilityCatalogError(
            f"unable to load compatibility data from {path}: {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise CompatibilityCatalogError(f"{path}: root must be a JSON object")
    return data


@lru_cache(maxsize=1)
def load_compatibility_catalog() -> dict[str, Any]:
    return _load_json(_locate_compatibility_path(COMPATIBILITY_CATALOG_FILE))


@lru_cache(maxsize=1)
def load_compatibility_sources() -> dict[str, Any]:
    return _load_json(_locate_compatibility_path(COMPATIBILITY_SOURCES_FILE))


@lru_cache(maxsize=1)
def load_verified_catalog() -> dict[str, Any]:
    return _load_json(_locate_verified_catalog_path())


def derive_renderer_metadata(
    step_name: str,
    verified_catalog: dict[str, Any],
) -> dict[str, Any]:
    entries = verified_catalog.get("steps")
    if not isinstance(entries, list):
        raise CompatibilityCatalogError(
            "verified renderer catalog steps must be an array"
        )
    by_name = {
        entry.get("name", "").strip().casefold(): entry
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("name"), str)
    }
    entry = by_name.get(step_name.strip().casefold())
    if entry is None:
        return {
            "rendererStatus": "not_verified",
            "fileMakerPro19_5Fixture": "not_available",
            "rendererEvidence": [],
        }

    evidence_value = entry.get("evidence")
    evidence = (
        [str(item) for item in evidence_value]
        if isinstance(evidence_value, list)
        else []
    )
    has_paste_fixture = "fm19_5_paste_verified" in evidence
    renderer_status = (
        "verified"
        if entry.get("status") == "supported" and has_paste_fixture
        else "experimental"
    )
    return {
        "rendererStatus": renderer_status,
        "fileMakerPro19_5Fixture": (
            "available" if has_paste_fixture else "not_available"
        ),
        "rendererEvidence": evidence,
    }


def enrich_step(
    step: dict[str, Any],
    verified_catalog: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if verified_catalog is None:
        verified_catalog = load_verified_catalog()
    result = deepcopy(step)
    result.update(derive_renderer_metadata(step["name"], verified_catalog))
    return result


def compatibility_steps() -> list[dict[str, Any]]:
    catalog = load_compatibility_catalog()
    raw_steps = catalog.get("steps")
    if not isinstance(raw_steps, list):
        raise CompatibilityCatalogError(
            "compatibility catalog steps must be an array"
        )
    verified = load_verified_catalog()
    return [
        enrich_step(step, verified)
        for step in sorted(
            raw_steps,
            key=lambda item: (
                str(item.get("category", "")).casefold(),
                str(item.get("name", "")).casefold(),
            ),
        )
    ]


def find_exact_step(
    query: str,
    steps: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    normalized = query.strip().casefold()
    if not normalized:
        return None
    if steps is None:
        steps = compatibility_steps()
    return next(
        (
            step
            for step in steps
            if step.get("name", "").strip().casefold() == normalized
        ),
        None,
    )


def suggest_steps(
    query: str,
    steps: list[dict[str, Any]] | None = None,
    *,
    limit: int = 5,
) -> list[str]:
    normalized = query.strip().casefold()
    if not normalized:
        return []
    if steps is None:
        steps = compatibility_steps()
    names = sorted(
        (
            str(step["name"])
            for step in steps
            if isinstance(step.get("name"), str)
        ),
        key=str.casefold,
    )
    partial = [
        name
        for name in names
        if normalized in name.casefold()
    ]
    if partial:
        return partial[:limit]
    normalized_names = {name.casefold(): name for name in names}
    matches = get_close_matches(
        normalized,
        list(normalized_names),
        n=limit,
        cutoff=0.35,
    )
    return [normalized_names[match] for match in matches]


def filter_steps(
    steps: list[dict[str, Any]],
    *,
    context: str | None = None,
    support: str | None = None,
    category: str | None = None,
    renderer_status: str | None = None,
) -> list[dict[str, Any]]:
    if support is not None and context is None:
        raise CompatibilityCatalogError("--support requires --context")
    if context is not None:
        context = normalize_context(context)
    if support is not None and support not in SUPPORT_VALUES:
        raise CompatibilityCatalogError(
            f"unknown support value {support!r}"
        )
    if renderer_status is not None and renderer_status not in RENDERER_STATUSES:
        raise CompatibilityCatalogError(
            f"unknown renderer status {renderer_status!r}"
        )

    normalized_category = (
        category.strip().casefold()
        if category is not None
        else None
    )
    categories = {
        str(step.get("category", "")).casefold()
        for step in steps
    }
    if normalized_category is not None and normalized_category not in categories:
        expected = ", ".join(sorted(categories))
        raise CompatibilityCatalogError(
            f"unknown category {category!r}; expected one of: {expected}"
        )

    filtered = []
    for step in steps:
        if (
            normalized_category is not None
            and str(step.get("category", "")).casefold() != normalized_category
        ):
            continue
        if (
            renderer_status is not None
            and step.get("rendererStatus") != renderer_status
        ):
            continue
        if (
            support is not None
            and step.get("execution", {}).get(context) != support
        ):
            continue
        filtered.append(step)
    return sorted(
        filtered,
        key=lambda step: (
            str(step.get("category", "")).casefold(),
            str(step.get("name", "")).casefold(),
        ),
    )
