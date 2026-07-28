# ADR 0002: Adopt strict Script IR v2 with explicit unresolved references

- Status: accepted
- Date: 2026-07-29
- Related issues: #3

## Context

Script IR v1 contains only a target string, a kind, and a permissive step array. It cannot distinguish client, PSOS, and server-schedule execution; declare contracts or variables; describe FileMaker context; or preserve an object name whose internal ID is unknown. Its shared step property bag also permits invalid property combinations.

The repository must retain the existing v1 render command while ensuring that new v2 designs fail closed. Migration must not infer a layout, table occurrence, field, script, internal ID, execution mode, or business rule.

## Decision

1. Preserve the original schema as `script-ir-v1.schema.json`.
2. Make `script-ir-v2.schema.json` the canonical Draft 2020-12 schema through `script-ir.schema.json`.
3. Model target versions, execution, script metadata, JSON input/result contracts, context, variables, FileMaker object references, steps, unresolved issues, risks, and design/evidence status explicitly.
4. Define each of the seven existing step types as a separate `oneOf` branch with `additionalProperties: false`.
5. Use the `jsonschema` library for standards-based structural validation and keep non-schema invariants in a small semantic validation layer.
6. Allow unresolved object references in a design document, but reject XML generation whenever any object reference remains unresolved.
7. Migrate v1 deterministically in memory before rendering. Values present in v1 are copied; absent design facts become explicit unspecified metadata and unresolved issues. No FileMaker object reference or internal ID is created.
8. Reserve `execution: "unspecified"` for documents marked `migration.fromSchemaVersion: 1`. This exception prevents the migration from falsely choosing client, PSOS, or server schedule. Native v2 designs must use one of those three modes.
9. Preserve the existing XML templates, step IDs, names, default enabled behavior, and output formatting.

The runtime dependency is bounded to `jsonschema>=4.23,<5`. The minimum provides stable Draft 2020-12 validation on the supported Python range; the upper bound prevents an unreviewed major-version API change. The same schemas are published at the repository root and installed as package data.

## Alternatives considered

### Continue with hand-written validation only

- Benefits: no dependency and little initial code.
- Costs and risks: external tools cannot validate the contract; nested strictness and discriminated steps are easy to drift; documentation and runtime validation can disagree.

### Use a Python-only model library

- Benefits: convenient Python object construction and type coercion.
- Costs and risks: the normative contract becomes Python-specific; coercion can weaken fail-closed behavior; AI and non-Python consumers still need a JSON Schema.

### Infer missing v1 execution and FileMaker references

- Benefits: migrated documents appear complete.
- Costs and risks: a deterministic default would be presented as a FileMaker fact and could select the wrong environment or object. This conflicts with the repository's evidence and source policy.

### Reject all v1 input

- Benefits: simplest v2 implementation.
- Costs and risks: breaks the documented command and existing example without improving the safety of the seven object-independent steps.

## Consequences

### Positive

- Invalid step combinations and unknown properties fail before XML generation.
- FileMaker object names can be recorded without inventing internal IDs.
- v1 rendering remains byte-deterministic through an explicit migration path.
- Contracts and execution assumptions are available to AI and reviewers.
- Repository policy checks ensure the schemas, examples, and migration remain usable.

### Negative

- v2 documents are more verbose.
- JSON Schema cannot express every cross-field invariant, so semantic validation remains necessary.
- The package has one bounded runtime dependency.
- A migrated v1 document needs human completion before it is a fully specified v2 design, even though legacy rendering remains available.

### Risks and mitigations

- Risk: schema validation and semantic validation drift.
  - Mitigation: tests cover both layers, and repository policy validates the canonical examples and deterministic migration.
- Risk: `unspecified` is used for a native v2 design.
  - Mitigation: semantic validation requires the v1 migration marker and a target-execution unresolved issue.
- Risk: an unresolved object ID reaches XML.
  - Mitigation: rendering performs a separate renderability check after v2 validation and before writing the output file.
- Risk: automated XML checks are described as FileMaker verification.
  - Mitigation: status values follow `docs/EVIDENCE_MODEL.md`; no paste, runtime, or FMSE evidence is promoted.

## Evidence and sources

- `claris-fm19-running-scripts-on-server`: execution environments and independent FMSE context, `documented`
- `claris-fm19-script-steps-reference`: existing 19.5 step names and behavior, `documented`
- `claris-fm19-save-copy-as-xml`: FileMaker XML contains version- and file-specific structure, `documented`
- `agentic-fm-public-implementation`: existing public XML structures used by the original renderer, `public_fixture_observed`

This decision and its automated tests establish `structure_tested` behavior only. FileMaker Pro 19.5 paste/runtime and FileMaker Server 19.5 FMSE behavior remain unverified.

## Follow-up work

- [ ] Obtain FileMaker Pro 19.5 fixtures with provenance for the round-trip pipeline (#4).
- [ ] Add static analysis for context, variable, and server-safety rules (#5).
- [ ] Independently review Issue #3 before merge.
