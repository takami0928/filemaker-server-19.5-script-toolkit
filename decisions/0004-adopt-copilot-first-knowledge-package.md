# ADR 0004: Adopt a Copilot-first public knowledge package

- Status: accepted
- Date: 2026-07-29
- Related issues: #4, #5, #6, #7, #8

## Context

This repository began as a tool for generating FileMaker script XML. That work established useful governance, evidence boundaries, a conservative Script IR, and limited XML and clipboard experiments.

The normalized FileMaker 19.5 compatibility catalog and the five practical, design-only patterns now provide more direct value for safe script design. They can guide execution-context selection, error handling, record locking, commit behavior, and fail-closed treatment of missing system information.

The current project cannot obtain provenance-aware FileMaker 19.5 XML fixtures or FileMaker Pro/Server 19.5 hardware evidence. Treating XML as the primary outcome would therefore add fixture, renderer, parser, analyzer, packaging, and maintenance dependencies without proving the result in the target environment.

Microsoft 365 Copilot needs a bounded set of short public knowledge documents together with separately managed internal system information. The useful outcome is a complete human-readable design that a FileMaker developer can review, implement manually in Script Workspace, and test.

## Decision

1. Maintain the current repository. Do not create a new repository at this time.
2. Use this public GitHub repository as the editing and review source of truth for general FileMaker Server 19.5 knowledge, decisions, and practical patterns.
3. In a later PR, create a limited Markdown knowledge package for controlled placement in SharePoint.
4. Keep internal FileMaker objects, workflows, privileges, naming rules, existing specifications, and implementation requirements in a separate SharePoint library or clearly segregated area.
5. Let Microsoft 365 Copilot combine the public knowledge package and internal information to produce a human-readable script design document.
6. Treat the human-readable design document as the formal output. A FileMaker developer remains responsible for manual Script Workspace implementation, review, and testing.
7. Retain existing XML, Script IR, and clipboard code as frozen experimental secondary functionality. Do not expand it without explicit reapproval.
8. Do not describe FileMaker Pro/Server 19.5-unverified XML as correct, verified, or formal output.
9. Do not fork external repositories. Use them only as upstream design or specification references under their applicable license and evidence boundaries.

## Alternatives considered

### 1. Continue the current repository as XML-first

- Benefit: preserves the original dependency sequence and could eventually automate more paste operations.
- Cost: makes unavailable 19.5 fixtures and hardware evidence prerequisites for the primary value. It also expands the renderer, parser, analyzer, and maintenance burden.
- Outcome: rejected as the primary direction. Existing XML functionality remains frozen and available for separately approved experiments.

### 2. Create a new repository for M365 Copilot

- Benefit: creates a clean boundary from the existing XML implementation.
- Cost: duplicates governance, compatibility knowledge, practical patterns, issue history, and review workflows.
- Outcome: rejected for now. The current repository already contains the public assets needed for the knowledge package.

### 3. Archive the current repository and move to a new repository

- Benefit: removes ambiguity about the former XML-first purpose.
- Cost: fragments history and makes the maintained compatibility and pattern assets appear abandoned.
- Outcome: rejected. The current repository remains active and its purpose is realigned in place.

### 4. Fork `petrowsky/agentic-fm`

- Benefit: starts from a broad FileMaker AI harness with extensive solution-analysis and generation capabilities.
- Cost: imports a much larger architecture, a FileMaker Pro 21.0+ baseline, and direct solution tooling that are not required by the M365 Copilot/SharePoint design.
- Outcome: rejected. It remains an upstream design reference only.

### 5. Fork an XML specification repository

- Benefit: could broaden step coverage and reduce local reverse-engineering work.
- Cost: centers the project on XML, introduces attribution and version-provenance obligations, and does not supply direct FileMaker 19.5 evidence.
- Outcome: rejected. XML references remain upstream-only and are consulted only if that experimental track is reapproved.

### 6. Use external repositories only as upstream references

- Benefit: permits architectural and specification comparison without importing code, version assumptions, or maintenance obligations.
- Cost: useful changes must be reviewed and adapted locally rather than inherited automatically.
- Outcome: adopted.

### 7. Separate public GitHub knowledge from internal SharePoint information

- Benefit: preserves public reviewability while keeping internal objects, workflows, privileges, and requirements within the organization's access boundary.
- Cost: requires an explicit package update process and SharePoint-side separation and permissions.
- Outcome: adopted.

## External upstream roles

### `petrowsky/agentic-fm`

- Do not fork it.
- Use it as an architectural reference for a comprehensive FileMaker AI foundation.
- Its repository license is Apache License 2.0.
- Its documented dependency is FileMaker Pro 21.0+, so it is not evidence of FileMaker 19.5 compatibility.
- Do not make it a direct dependency of the M365 Copilot/SharePoint architecture.

### `andykear/FileMaker-XMLsnippet-Claude-Skill`

- Do not fork it.
- Its README states CC BY 4.0.
- Use it as an upstream specification reference only if XML work is reapproved.
- Its documented paste testing centers on FileMaker 2024 and later, so it is not direct FileMaker 19.5 evidence.
- Confirm and satisfy attribution requirements before copying any content.

### `ariera/fmscript2xml`

- Do not fork it.
- Limit its role to a design reference for deterministic conversion.
- Its README points to a parent-project license, but this repository does not expose a clear root license file. Do not use its code until the applicable license is confirmed.
- Do not copy its code or documentation in this PR.

## Consequences

### Positive

- Copilot value can be delivered from the completed governance, compatibility, and practical-pattern foundation.
- Public knowledge remains reviewable in GitHub.
- Internal information remains inside the organization's SharePoint boundary.
- XML evidence limitations no longer block the primary knowledge package.
- The retained 59-step catalog, five patterns, shared JSON result contract, and fail-closed rules remain useful.

### Negative

- FileMaker developers must still implement designs manually.
- Every Copilot output requires human review and target-system testing.
- GitHub and SharePoint need an explicit update process.
- XML automation coverage does not expand.
- Existing XML code remains in the repository, so documentation must continue to distinguish it from the primary purpose.

## Evidence and sources

- `petrowsky/agentic-fm` README: https://github.com/petrowsky/agentic-fm/blob/main/README.md
- `petrowsky/agentic-fm` LICENSE: https://github.com/petrowsky/agentic-fm/blob/main/LICENSE
- `andykear/FileMaker-XMLsnippet-Claude-Skill` README and license statement: https://github.com/andykear/FileMaker-XMLsnippet-Claude-Skill/blob/main/README.md
- `ariera/fmscript2xml` README and license pointer: https://github.com/ariera/fmscript2xml/blob/main/README.md

No external code, XML specification, or documentation text is copied by this decision. These sources establish upstream scope and licensing context only; they do not promote FileMaker 19.5 paste, runtime, or FMSE evidence.

## Follow-up work

1. PR 1 — realign the repository purpose, responsibilities, and roadmap.
2. PR 2 — create `docs/copilot/` knowledge package v0.1.
3. PR 3 — create the SharePoint distribution package and Copilot acceptance tests.
