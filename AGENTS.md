# Agent Entry Point

This repository is the public source of FileMaker Server 19.5 knowledge, decisions, and practical patterns that Microsoft 365 Copilot and other AI systems combine with separately managed internal system information to produce human-readable script design documents for manual implementation in Script Workspace. It must never contain company-specific system information.

## Required reading order

1. [Purpose and scope](docs/PURPOSE.md)
2. [AI usage contract](AI_GUIDE.md)
3. [Roadmap](ROADMAP.md)
4. [Compatibility catalog](docs/COMPATIBILITY_CATALOG.md)
5. [Practical script patterns](patterns/README.md)
6. [Script style](docs/SCRIPT_STYLE.md)
7. [Server execution design](docs/SERVER_EXECUTION.md)
8. [FileMaker Server 19.5 execution boundary](docs/FM_SERVER_19_5.md)
9. [Known limitations](docs/KNOWN_LIMITATIONS.md)
10. [Quality gates](QUALITY_GATES.md)
11. [Evidence model](docs/EVIDENCE_MODEL.md)
12. [Source policy](docs/SOURCE_POLICY.md)
13. [Definition of Done](docs/DEFINITION_OF_DONE.md)
14. [Script IR](docs/SCRIPT_IR.md)
15. [XML and clipboard](docs/XML_CLIPBOARD.md)
16. [Validation status](docs/VALIDATION_STATUS.md)

Treat internal company documents as the source of facts about the target system. Treat this repository as the source of implementation rules. Do not invent tables, fields, table occurrences, layouts, scripts, privileges, or internal FileMaker object IDs.

## Non-negotiable rules

- Target FileMaker Server 19.5 and FileMaker Pro 19.5 unless a separate compatibility track is explicitly approved.
- Treat the human-readable script design document as the primary formal output. A FileMaker developer manually implements and tests it in Script Workspace.
- Do not expand XML rendering, Script IR, or clipboard capabilities without explicit approval to reactivate that experimental track.
- Never store company-specific information in this public repository.
- Keep any future SharePoint public-knowledge package free of internal system information; internal content belongs in a separate library or clearly segregated area.
- Never present FileMaker Pro/Server 19.5-unverified XML as a formal or verified deliverable.
- Use deny-by-default behavior for unknown steps, options, object references, and compatibility.
- Do not convert CI success into FileMaker paste, runtime, or FMSE evidence.
- Do not promote evidence without the metadata required by `docs/EVIDENCE_MODEL.md`.
- Every compatibility or behavioral claim must reference IDs in its registered source registry. The normalized compatibility catalog uses `catalog/fm19.5/compatibility/sources.json`; other implementation claims use `sources/registry.json`.
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

This section applies only when maintaining or explicitly reactivating the experimental XML subsystem. A normal Copilot knowledge-document change does not require an XML fixture, IR schema change, renderer change, or parser change.

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
fms19 validate-ir examples/server-script-ir-v2.json
fms19 migrate-ir examples/server-script-ir.json migrated-ir-v2.json
fms19 validate-ir migrated-ir-v2.json
fms19 lint examples/server-script-steps.xml
fms19 render examples/server-script-ir.json generated-v1.xml
fms19 render examples/server-script-ir-v2.json generated-v2.xml
fms19 lint generated-v1.xml
fms19 lint generated-v2.xml
```

## Completion reporting

Use the repository-wide reporting format and legacy-label mappings in
[`docs/EVIDENCE_MODEL.md`](docs/EVIDENCE_MODEL.md#repository-wide-completion-reporting).
Report every dimension separately:

- Design status: `draft_design` or `implementation_ready`
- XML output: `not_requested`, `not_generated`, or `generated`
- Automated checks: `not_run`, `passed`, or `failed`
- FileMaker Pro 19.5 paste verification: `not_run`, `passed`, or `failed`
- FileMaker Pro 19.5 client runtime verification: `not_run`, `passed`, or `failed`
- FileMaker Server 19.5 FMSE verification: `not_run`, `passed`, or `failed`

Do not omit `not_run`. Do not infer one dimension from another. If the frozen
legacy labels `design_ready` or `xml_generated` are used, follow their narrower
meanings and mappings in the evidence model.
