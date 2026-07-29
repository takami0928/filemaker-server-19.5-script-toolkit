# ADR 0003: Normalize the FileMaker 19.5 compatibility catalog for reference CLI use

- Status: accepted
- Date: 2026-07-29
- Related issues: #7

## Context

Issue #7 produced a comprehensive but deliberately non-verified research candidate. Users and AI need a small, installed, deterministic interface for checking whether a script step exists in FileMaker Pro 19.5, whether it is usable in a particular execution context, and whether separate XML renderer evidence exists.

Using the large research JSON directly at runtime would couple a reference CLI to unrelated functions, errors, exclusions, and audit metadata. Copying renderer status into the compatibility catalog would create a second source of truth and could turn documented compatibility into an unsupported XML-generation claim.

## Decision

1. Deterministically normalize all 59 research-candidate script steps into `catalog/fm19.5/compatibility/script-steps.json`.
2. Copy the complete records for the 64 source IDs referenced by those steps into the dedicated `catalog/fm19.5/compatibility/sources.json` registry without changing source type or evidence meaning.
3. Normalize execution values to `available`, `unavailable`, `partial`, and `unknown` for seven canonical contexts. Treat `unknown` as fail closed and require recorded conditions for `partial`.
4. Preserve `introducedIn` and `serverSupportIntroducedIn` as separate fields. Reject 19.5 PSOS or server-schedule support when server support began after 19.5.
5. Do not persist renderer status in compatibility entries. Derive it at query time from `catalog/fm19.5/verified-steps.json`:
   - `verified` requires a `supported` renderer entry and `fm19_5_paste_verified`;
   - an implementation entry without that evidence is `experimental`;
   - no entry is `not_verified`.
6. Package both normalized catalogs and the existing verified renderer catalog as installed data so `fms19 compat` and `fms19 list-steps` work outside a source checkout.
7. Keep exact-name lookup conservative. Case and surrounding whitespace are ignored, but partial or fuzzy candidates are never selected automatically.
8. Keep this change to Phase A. It does not add renderer templates, Script IR types, clipboard IDs, fixtures, or FileMaker verification.

## Alternatives considered

### Read the full research artifact at runtime

- Benefits: no normalized copy.
- Costs and risks: unnecessarily large runtime data; internal research schema changes would break the CLI; research and product reference boundaries become unclear.

### Store renderer status in each compatibility entry

- Benefits: one JSON lookup.
- Costs and risks: status drifts from `verified-steps.json`; implementation could be misrepresented as FileMaker evidence; the same fact is maintained twice.

### Add the selected sources to the general source registry

- Benefits: one repository-wide registry.
- Costs and risks: duplicates 64 complete research records into a registry with a different schema and purpose. A dedicated registry preserves every selected candidate record exactly and is checked against its source.

### Treat partial compatibility as available

- Benefits: simpler filters.
- Costs and risks: hides option-level and environment constraints. This conflicts with deny-by-default behavior.

## Consequences

### Positive

- Humans and AI can query 19.5 compatibility before designing a script.
- Runtime data is bounded to 59 steps and 64 referenced sources.
- Search, filtering, and JSON output are deterministic.
- Compatibility, renderer implementation, and FileMaker evidence remain separate.
- Installed wheels contain the same reference data as source checkouts.

### Negative

- Normalized files must be regenerated when the research candidate changes.
- The catalog duplicates selected research records on disk, although policy checks make drift fail CI.
- A documented compatibility result still requires object-reference resolution and, when XML is needed, separate renderer evidence.

### Risks and mitigations

- Risk: normalized claims drift from the research candidate.
  - Mitigation: repository policy rebuilds the expected documents in memory and compares them exactly.
- Risk: `unknown` or `partial` is interpreted as unconditional support.
  - Mitigation: closed value enumeration, exact filtering, required conditions, documentation, and negative tests.
- Risk: later Server support is silently backported.
  - Mitigation: separate version fields and a policy check that forces PSOS and server schedule to `unavailable` when Server support began after 19.5.
- Risk: renderer code is promoted to verified without FileMaker evidence.
  - Mitigation: renderer status is derived, and `verified` requires `fm19_5_paste_verified`.

## Evidence and sources

The normalized entries retain the exact source IDs and `documented` research evidence from `research/issue-7/candidates/`. The dedicated registry preserves each selected source record without promoting `secondary` evidence or current-version material.

Automated tests establish deterministic normalization, lookup, filtering, and policy enforcement only. They are not FileMaker Pro 19.5 paste/runtime evidence or FileMaker Server 19.5 FMSE evidence.

## Follow-up work

- [ ] Design source-backed practical server-script patterns using this catalog.
- [ ] Resolve prioritized Issue #7 unknowns with archived sources or explicit tests.
- [ ] Obtain provenance-aware FileMaker Pro 19.5 fixtures in the fixture pipeline.
- [ ] Expand renderer coverage only in separate evidence-backed changes.
