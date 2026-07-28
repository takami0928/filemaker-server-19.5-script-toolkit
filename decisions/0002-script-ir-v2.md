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
8. Reserve `execution: "unspecified"`, `context.mode: "unspecified"`, `sideEffects.state: "unspecified"`, variable initialization `method: "unspecified"`, and variable `type: "unknown"` for v1 migration documents. Each active migration-only state requires a corresponding blocking unresolved issue, and the document must remain `draft/unverified`.
9. Treat every serialized v2 document identically at render time. A `migration` marker never authorizes XML generation, and any blocking unresolved issue rejects rendering.
10. Preserve direct v1 rendering only through an out-of-band source fact: `render_ir()` detects the original v1 input and invokes a private legacy path. A saved migrated v2 document cannot activate this exception.
11. Limit Script IR input evidence to `unverified` and `design_ready`. Do not accept `xml_generated` as self-attestation, and do not accept paste, runtime, or FMSE states without the separate verification-record pipeline.
12. Preserve the existing XML templates, step IDs, names, default enabled behavior, and output formatting.
13. Build a wheel in CI and smoke-test it from a clean virtual environment and a working directory outside the repository. The smoke test must prove that validation loads the installed schema data, then run v2 validation and v1-to-v2 migration.

The runtime dependency is bounded to `jsonschema>=4.23,<5`. The minimum provides stable Draft 2020-12 validation on the supported Python range; the upper bound prevents an unreviewed major-version API change. The same schemas are published at the repository root and installed as package data.

The wheel smoke test uses the CI-only optional dependency `build>=1.2,<2`. It is not a runtime dependency. The minimum supplies the standard `python -m build` frontend used by the test, while the upper bound prevents an unreviewed major-version change in the distribution check.

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

### Trust the serialized migration marker during rendering

- Benefits: one render path can accept both direct v1 input and saved migrated v2.
- Costs and risks: any v2 author can copy the marker and bypass blocking unresolved issues. Document content cannot prove the provenance of the original render input, so this design is rejected.

### Accept generated or runtime evidence as an IR status

- Benefits: one field appears to cover design and verification lifecycle states.
- Costs and risks: the input document can self-assert evidence without hashes, tool metadata, FileMaker builds, procedures, or results. Generation manifests and FileMaker verification records must remain separate.

## Consequences

### Positive

- Invalid step combinations and unknown properties fail before XML generation.
- FileMaker object names can be recorded without inventing internal IDs.
- Direct v1 rendering remains byte-deterministic through an origin-aware private compatibility path.
- Saved migrated v2 documents remain valid design records but fail closed at render time until completed.
- Contracts and execution assumptions are available to AI and reviewers.
- Repository policy checks ensure the schemas, examples, and migration remain usable.
- Installed wheels are tested without access to the repository schema directory.

### Negative

- v2 documents are more verbose.
- JSON Schema cannot express every cross-field invariant, so semantic validation remains necessary.
- The package has one bounded runtime dependency.
- A migrated v1 document needs human completion before it is a fully specified or renderable v2 design; legacy rendering is available only while the original input is still v1.
- Generation evidence remains transient until a renderer-owned sidecar manifest is implemented.

### Risks and mitigations

- Risk: schema validation and semantic validation drift.
  - Mitigation: tests cover both layers, and repository policy validates the canonical examples and deterministic migration.
- Risk: `unspecified` or `unknown` is used for a native v2 design.
  - Mitigation: schema and semantic validation reserve these values for a migration document, require a matching blocking issue, and require `draft/unverified`.
- Risk: a serialized marker is used to bypass blocking issues.
  - Mitigation: all v2 render paths enforce blocking issues; only `render_ir()`'s observation of an original v1 input selects the private compatibility path.
- Risk: an unresolved object ID reaches XML.
  - Mitigation: rendering performs a separate renderability check after v2 validation and before writing the output file.
- Risk: automated XML checks are described as FileMaker verification.
  - Mitigation: IR input accepts only `unverified` and `design_ready`; no generated, paste, runtime, or FMSE evidence can be self-asserted.
- Risk: editable installs hide missing wheel data files.
  - Mitigation: Windows and Linux CI build and install a wheel into a clean environment, execute outside the repository, and assert the installed schema path.

## Evidence and sources

- `claris-fm19-running-scripts-on-server`: execution environments and independent FMSE context, `documented`
- `claris-fm19-script-steps-reference`: existing 19.5 step names and behavior, `documented`
- `claris-fm19-save-copy-as-xml`: FileMaker XML contains version- and file-specific structure, `documented`
- `agentic-fm-public-implementation`: existing public XML structures used by the original renderer, `public_fixture_observed`

This decision and its automated tests establish `structure_tested` behavior only. FileMaker Pro 19.5 paste/runtime and FileMaker Server 19.5 FMSE behavior remain unverified.

## Follow-up work

- [ ] Obtain FileMaker Pro 19.5 fixtures with provenance for the round-trip pipeline (#4).
- [ ] Define a renderer-owned generation manifest with toolkit version, timestamps, source/output hashes, and automated validation result.
- [ ] Define machine-validated FileMaker paste/runtime/FMSE verification records in the fixture/evidence pipeline.
- [ ] Add static analysis for context, variable, and server-safety rules (#5).
- [ ] Independently review Issue #3 before merge.
