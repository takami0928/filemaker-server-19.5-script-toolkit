# Roadmap

This roadmap orders work by dependency and safety. Expanding XML coverage before the evidence, schema, and analyzer layers exist is intentionally avoided.

## Current state

- Maturity: **M2 — governed design and compilation**
- Target: FileMaker Server 19.5 with FileMaker Pro 19.5 development on Windows
- Policy: deny by default
- Runtime evidence: not yet collected from FileMaker Pro or FileMaker Server 19.5

## Phase 0 — Governance foundation

Tracking: #2

- Quality gates and Definition of Done
- Evidence levels and promotion rules
- Source registry and source policy
- Architecture Decision Records
- Agent/Codex contribution rules
- CI checks for repository policy

Exit condition: repository claims, evidence, and generated assets are governed by machine-checkable rules.

## Phase 1 — Strict Script IR v2

Tracking: #3. Blocked by Phase 0.

- [x] Versioned target and execution mode
- [x] Script input/output contracts
- [x] Declared variables and context
- [x] Strict per-step schemas
- [x] Unresolved FileMaker object references
- [x] Migration from the current minimal IR
- [x] Installed-wheel schema and migration smoke test

Exit condition: met by Issue #3 implementation. Invalid native v2 designs, blocking issues, and unresolved object IDs cannot reach XML rendering. Direct v1 compatibility is selected only from the original input version; saved migration v2 documents remain blocked until completed. Independent PR review and FileMaker hardware verification remain separate gates.

## Phase 2 — Fixture and round-trip pipeline

Tracking: #4. Blocked by Phases 0–1.

- Fixture manifests and hashes
- Import, normalize, inspect, semantic diff, parse, and round-trip commands
- XML-to-IR parser
- Golden fixtures and tests

Exit condition: FileMaker-copied XML can be captured once and processed deterministically.

## Phase 3 — Static analyzer

Tracking: #5. Blocked by Phases 0–2.

- P0–P3 rule engine
- Variable, error, context, found-set, destructive-operation, and server-compatibility rules
- Machine-readable and human-readable reports

Exit condition: unsafe design patterns are detected before clipboard output.

## Phase 4 — AI evaluation suite

Tracking: #6. Blocked by Phases 0–1; strengthened by Phase 3.

- Synthetic system descriptions and tasks
- Expected properties and forbidden assumptions
- Version contamination and hallucination checks
- Saved baselines and regression reports

Exit condition: repository changes can be shown to improve or preserve AI output quality.

## Phase 5 — Source-backed FileMaker Server 19.5 catalog

Tracking: #7. Blocked by Phase 0. Requires a focused Deep Research pass.

- Script steps and execution compatibility
- Important functions, errors, paths, PSOS, schedules, import/export, ODBC, and plug-ins
- Source IDs, confidence, evidence, and unknown/fail-closed states
- Generated human/AI-readable documentation

Exit condition: high-priority server-side design decisions can be made without ad hoc web research.

## Phase 6 — Expand renderer coverage

Blocked by Phases 1–3 and the relevant subset of Phase 5.

Priority order:

1. Control and contracts
2. Layout/context and find operations
3. Record create/update/commit/revert
4. Server execution and integration
5. Destructive or high-risk operations

A step is not added merely because its XML is available. It must satisfy the evidence and Definition of Done requirements.

## Phase 7 — Microsoft 365 Copilot knowledge package

Tracking: #8. Blocked by Phases 0 and 5; benefits from Phases 2–4.

- Deterministic Markdown generation from catalogs
- Versioned package and limitations
- Drift checks
- Release archive for controlled internal import

Exit condition: Microsoft 365 Copilot can use a compact, internally consistent package rather than searching the repository ad hoc.

## Phase 8 — FileMaker 19.5 hardware validation

Human/FileMaker environment required.

- Clipboard format detection
- Copy/read/write/paste round-trip
- Step-by-step fixture capture
- FileMaker Pro 19.5 paste validation
- Hosted test file runtime validation
- PSOS and server-schedule validation

Exit condition: evidence can be promoted to `fm19_5_paste_verified`, `fm19_5_runtime_verified`, or `fmse_verified` as applicable.

## Dependency rule

A later phase may prototype interfaces, but it must not claim completion or promote evidence while prerequisite phases remain incomplete.
