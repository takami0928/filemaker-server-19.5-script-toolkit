# Quality Gates

These gates apply to every pull request. A gate marked **blocking** must pass before merge.

## G0 — Information safety

**Blocking**

- No company-specific table, field, TO, layout, script, account, server, URL, credential, DDR, Save a Copy as XML output, screenshot, log, or production data.
- Examples use synthetic names and values.
- Secrets are neither committed nor requested by tests.

## G1 — Target and scope

**Blocking**

- Target remains FileMaker Server 19.5 and FileMaker Pro 19.5 unless a separate compatibility track is explicitly approved.
- Client, PSOS, and server-schedule behavior are not conflated.
- Later-version features are not represented as 19.5 capabilities.

## G2 — Source and claim traceability

**Blocking for catalog/specification changes**

- Every compatibility or behavioral claim has at least one valid `sourceId` in `sources/registry.json`.
- Primary Claris documentation is preferred where available.
- Secondary sources cannot independently promote a claim beyond `public_fixture_observed`.
- Unknown behavior remains `unknown` or fail-closed.

## G3 — Evidence honesty

**Blocking**

- Evidence uses only values defined in `docs/EVIDENCE_MODEL.md`.
- Evidence levels are monotonic and cannot skip required proof.
- Automated tests cannot claim FileMaker paste, runtime, or FMSE verification.
- Script IR input cannot self-assert XML generation or FileMaker verification.
- Documentation distinguishes design-ready, XML-generated, paste-verified, runtime-verified, and FMSE-verified states.

## G4 — XML and catalog integrity

**Blocking for XML/catalog changes**

- Unknown steps are denied by default.
- Step name and numeric ID are catalog-backed.
- New step support includes catalog data, source references, fixture/provenance metadata, parser/renderer support where applicable, and tests.
- Unresolved FileMaker object IDs are not invented or silently defaulted.

## G5 — Code quality

**Blocking**

- Unit tests pass on all supported Python versions.
- Repository policy validation passes.
- A built wheel validates and migrates IR outside the repository using installed schema data.
- Generated output is deterministic.
- Invalid input fails closed with an actionable error.
- Clipboard contents are not modified after validation failure.

## G6 — Test adequacy

**Blocking**

- Every defect fix includes a regression test.
- Every new validation rule has positive and negative tests.
- Every renderer/parser addition has golden or semantic round-trip tests.
- Boundary inputs include malformed XML/JSON, Unicode, Japanese text, CDATA termination, missing properties, and unsupported values where relevant.

## G7 — Documentation and decisions

**Blocking when behavior or architecture changes**

- User-facing commands and limitations are documented.
- Material architectural choices receive an ADR under `decisions/`.
- `ROADMAP.md`, evidence state, and known limitations are updated when scope changes.

## G8 — Independent review

Required before stable releases and recommended for every substantive PR.

- Review is performed from the original requirement and full diff, not only the implementation summary.
- Reviewer checks version compatibility, source claims, evidence promotion, fail-closed behavior, and test sufficiency.
- Unresolved P0/P1 findings block merge.

## Release gates

### Alpha

- Automated gates pass.
- FileMaker paste/runtime evidence may remain incomplete.
- README and release notes state the exact limitations.

### Beta

- Core clipboard round-trip verified in FileMaker Pro 19.5.
- High-priority supported steps have paste evidence.
- Representative hosted-file scripts have runtime evidence.

### Stable

- Supported server-side patterns have FMSE evidence.
- AI evaluation suite has a saved baseline with no unresolved critical regressions.
- Release artifact and source registry are reproducible.
