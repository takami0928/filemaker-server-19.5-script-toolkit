# ADR 0001: Govern sources, evidence, and generation separately

- Status: accepted
- Date: 2026-07-28
- Related issues: #2, #3, #4, #5, #7, #8

## Context

The toolkit must help AI generate FileMaker Server 19.5 scripts without treating web research, public XML examples, syntactically valid XML, FileMaker Pro paste acceptance, client runtime behavior, and FMSE behavior as equivalent proof.

A single Markdown handbook or a single `verified` flag would collapse these different claims. It would also allow documentation, renderer code, and AI-facing knowledge to drift apart.

## Decision

The repository separates four concerns:

1. `sources/registry.json` records where a claim came from.
2. machine-readable catalogs record compatibility and currently held evidence.
3. `docs/EVIDENCE_MODEL.md` defines what each evidence level proves and the required promotion path.
4. renderer/analyzer code consumes catalogs and fails closed when data is unknown or unresolved.

The source registry, catalogs, renderer constants, forbidden-step checks, and evidence values are checked in CI. FileMaker Pro/Server verification is represented only by explicit evidence metadata and cannot be inferred from CI.

## Alternatives considered

### Markdown-only handbook

- Benefits: easy to write and read.
- Costs and risks: difficult to validate mechanically; code and AI instructions can drift; ambiguous evidence language.

### One `verified: true/false` flag

- Benefits: simple data model.
- Costs and risks: cannot distinguish public observation, structure tests, paste acceptance, client runtime, and FMSE runtime.

### Generate XML directly from model output without a catalog

- Benefits: broad apparent coverage.
- Costs and risks: unknown XML and object IDs may be invented; version contamination is difficult to detect.

## Consequences

### Positive

- Claims are traceable to stable source IDs.
- Evidence limits remain visible to AI and humans.
- Unknown features remain fail-closed.
- Future Copilot documentation can be generated from the same machine-readable sources as the compiler.

### Negative

- Adding a script step requires more artifacts and tests.
- FileMaker hardware validation remains a separate manual activity.
- Source and evidence maintenance adds process overhead.

### Risks and mitigations

- Risk: governance documents claim checks that CI does not enforce.
  - Mitigation: repository policy tests and independent PR review.
- Risk: current-version Claris documentation is incorrectly applied to 19.5.
  - Mitigation: archived FileMaker 19 sources are preferred and version applicability is explicit.
- Risk: evidence is promoted without adequate metadata.
  - Mitigation: runtime evidence requires machine-validated verification records.

## Evidence and sources

- `claris-fm19-running-scripts-on-server`
- `claris-fm19-script-steps-reference`
- `claris-fm19-save-copy-as-xml`
- `claris-copy-paste-scripts`
- `agentic-fm-public-implementation`

Current evidence remains limited to `documented`, `public_fixture_observed`, `structure_tested`, and `clipboard_payload_tested` where recorded. No FileMaker Pro 19.5 paste/runtime or FMSE evidence is claimed.

## Follow-up work

- [ ] Implement strict IR v2 (#3)
- [ ] Implement fixture provenance and round-trip pipeline (#4)
- [ ] Implement static analysis (#5)
- [ ] Build source-backed compatibility catalog (#7)
- [ ] Generate the Microsoft 365 Copilot knowledge package (#8)
