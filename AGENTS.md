# Agent Entry Point

This repository is a public FileMaker Server 19.5 implementation reference and script XML toolkit. It must never contain company-specific system information.

## Required reading order

1. [Purpose and scope](docs/PURPOSE.md)
2. [Roadmap](ROADMAP.md)
3. [Quality gates](QUALITY_GATES.md)
4. [AI usage contract](AI_GUIDE.md)
5. [Evidence model](docs/EVIDENCE_MODEL.md)
6. [Source policy](docs/SOURCE_POLICY.md)
7. [Definition of Done](docs/DEFINITION_OF_DONE.md)
8. [FileMaker Server 19.5 execution boundary](docs/FM_SERVER_19_5.md)
9. [Script style](docs/SCRIPT_STYLE.md)
10. [Server execution design](docs/SERVER_EXECUTION.md)
11. [XML and clipboard](docs/XML_CLIPBOARD.md)
12. [Validation status](docs/VALIDATION_STATUS.md)

Treat internal company documents as the source of facts about the target system. Treat this repository as the source of implementation rules. Do not invent tables, fields, table occurrences, layouts, scripts, privileges, or internal FileMaker object IDs.

## Non-negotiable rules

- Target FileMaker Server 19.5 and FileMaker Pro 19.5 unless a separate compatibility track is explicitly approved.
- Use deny-by-default behavior for unknown steps, options, object references, and compatibility.
- Do not convert CI success into FileMaker paste, runtime, or FMSE evidence.
- Do not promote evidence without the metadata required by `docs/EVIDENCE_MODEL.md`.
- Every compatibility or behavioral claim must reference IDs in `sources/registry.json`.
- Current documentation for later FileMaker versions must not be silently backported to 19.5.
- Clipboard output must remain unchanged after any validation failure.
- Keep examples synthetic and free of company information.

## Pull request discipline

- One pull request should have one primary responsibility.
- Start from current `main`; do not build on an unmerged feature branch unless the dependency is explicit.
- Update code, tests, catalog data, sources, documentation, evidence, and roadmap together when applicable.
- Add an ADR for material architecture, evidence, XML representation, object-reference, environment, or release-policy decisions.
- Run all repository checks before opening a PR.
- Do not merge with unresolved P0/P1 review findings or failing CI.

## Adding or changing a script step

A step change is incomplete unless every applicable artifact is included:

1. source-backed catalog entry
2. evidence and missing-evidence state
3. provenance-aware fixture or an explicit pending-fixture limitation
4. strict IR schema
5. renderer support
6. parser support once the fixture pipeline exists
7. positive, negative, malformed-input, and round-trip tests
8. AI/user documentation
9. exact FileMaker Pro/Server verification procedure

Use only steps registered in `catalog/fm19.5/verified-steps.json`. Unknown XML must not be guessed. If a new step is needed, capture or obtain a provenance-aware fixture and follow the evidence model.

## Required checks

```powershell
python -m pip install -e .
python scripts/check_repository.py
python -m unittest discover -s tests -v
fms19 lint examples/server-script-steps.xml
fms19 render examples/server-script-ir.json generated.xml
fms19 lint generated.xml
```

## Completion reporting

Report these states separately:

- design ready
- XML generated and automated checks passed
- FileMaker Pro 19.5 paste verified
- FileMaker Pro 19.5 runtime verified
- FileMaker Server 19.5 FMSE verified

Never describe an earlier state as a later one.
