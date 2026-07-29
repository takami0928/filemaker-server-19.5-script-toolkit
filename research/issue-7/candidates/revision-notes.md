# Revision notes — 2026-07-29

## Scope
Audited the first FileMaker Server 19.5 Deep Research deliverables for unexplored domains, factual errors, version contamination, source-provenance errors, and machine-readability.

## Outputs
- deep-research-report.md
- source-registry-candidates.json
- script-step-catalog-candidates.json
- unresolved-questions.json
- coverage-audit.json

## Validation
- Sources: 110
- Steps: 59
- Requested high-priority steps covered: 51/51
- Additional audited steps: 8
- Functions: 24
- Error entries: 117
- Later-version exclusions/transitions: 15
- Unresolved questions: 20
- Unknown source references: 0
- Duplicate source IDs: 0
- Duplicate step names: 0
- Clipboard fmxmlsnippet numerical IDs asserted: 0

## Final additional correction
The exact boundary between Get ( LastExternalErrorDetail ) and Get ( LastErrorDetail ) is not treated as settled. The catalog now uses separate official sources and records the 19.5/19.6.1 boundary as a critical unresolved item.
