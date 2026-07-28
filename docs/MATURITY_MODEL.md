# Maturity Model

The maturity level describes the repository as a whole. Individual steps and patterns retain their own evidence levels.

## M0 — Documentation only

- Purpose and scope exist.
- No deterministic XML generation or validation.

## M1 — Safe proof of concept

- Deny-by-default renderer supports a small set of steps.
- XML structure and Windows payload can be checked automatically.
- FileMaker Pro/Server evidence is incomplete.

## M2 — Governed design and compilation

- Evidence model, source policy, Definition of Done, and quality gates are enforced.
- Strict IR represents execution mode, contracts, context, variables, and object references.
- Invalid native v2 designs and unresolved FileMaker object references fail before XML output; legacy v1 rendering retains explicit migration limitations.

Current repository level after the governance foundation and strict Script IR v2 work through Issue #3.

## M3 — Fixture-backed compiler

- Supported steps have provenance-aware fixtures.
- XML can be normalized, parsed, rendered, semantically diffed, and round-tripped.
- Parser, renderer, catalog, fixtures, and tests remain synchronized.

## M4 — Safety analyzer

- Static analysis detects variable, error-handling, context, found-set, destructive-operation, and server-compatibility risks.
- P0/P1 findings block clipboard output.
- AI evaluation cases detect version contamination and object hallucination.

## M5 — FileMaker 19.5 validated toolkit

- Core clipboard round-trip is verified on FileMaker Pro 19.5.
- High-priority supported steps are paste-verified.
- Representative client and hosted-file scripts are runtime-verified.

## M6 — FMSE-validated server toolkit

- Core PSOS and server-schedule patterns are verified on FileMaker Server 19.5.
- Compatibility catalog and Copilot knowledge package are complete for supported scope.
- Stable releases are reproducible and independently reviewed.

## Level assignment rules

- The repository cannot claim a level if a required quality gate is intentionally bypassed.
- Partial work is reported at the lower completed level.
- A level does not imply all FileMaker script steps are supported.
- Evidence limitations remain visible at every level.
