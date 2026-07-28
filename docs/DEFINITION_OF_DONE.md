# Definition of Done

A change is complete only when every applicable item below is satisfied. Non-applicable items must be stated in the pull request.

## Repository-wide change

- Scope and target remain clear.
- No company-specific information is included.
- Documentation, code, tests, and roadmap are consistent.
- CI and repository policy checks pass.
- Known limitations and evidence state are accurate.

## New or changed compatibility claim

- At least one source registry entry exists.
- The claim references source IDs.
- Version and execution environments are explicit.
- Unknown values are not inferred.
- Evidence does not exceed what was demonstrated.

## New script step support

Required artifacts:

1. catalog entry with name, numeric ID, target version, compatibility, source IDs, and evidence
2. provenance-aware fixture or an explicitly documented reason why fixture support is pending
3. strict IR schema definition
4. renderer support
5. parser support when the fixture pipeline exists
6. positive and negative tests
7. XML lint/semantic round-trip coverage
8. user/AI-facing documentation
9. known limitations and required FileMaker verification procedure

A step must not be called `verified` solely because the renderer emits well-formed XML.

## New analyzer rule

- Rule ID and P0–P3 severity are stable.
- Unsafe and safe examples are documented.
- Positive, negative, and boundary tests exist.
- The failure message states the risk and corrective action.
- Blocking behavior matches `QUALITY_GATES.md`.

## New fixture

- Manifest records exact provenance, target version if known, platform, object type, clipboard format if applicable, capture date, and SHA-256.
- XML contains no company-specific identifiers or data.
- Normalization is deterministic.
- Semantic round-trip result is recorded.
- Evidence promotion is justified.

## AI evaluation case

- System context is synthetic and sufficient.
- Required facts and forbidden assumptions are explicit.
- Expected properties are machine-checkable where practical.
- Scoring dimensions and failure severity are defined.
- The case does not depend on one model's exact wording.

## Release

- Version and changelog are updated.
- Release notes state supported scope and exact evidence limitations.
- Source registry and generated knowledge package are reproducible.
- Checksums are published for release artifacts.
- Independent review has no unresolved P0/P1 findings.
- Alpha/beta/stable criteria in `QUALITY_GATES.md` are met.
