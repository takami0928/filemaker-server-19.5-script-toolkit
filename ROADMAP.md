# Roadmap

This roadmap orders work by Copilot value delivery. The primary outcome is a human-readable FileMaker Server 19.5 script design document, not generated XML.

## Current state

- Target: FileMaker Server 19.5 with manual implementation in FileMaker Pro 19.5 Script Workspace
- Public source of truth: this GitHub repository
- Internal source of truth: a separate SharePoint library or clearly segregated area
- Policy: deny by default and do not infer missing FileMaker objects, privileges, business rules, or internal IDs
- FileMaker Pro/Server 19.5 evidence: not yet collected
- Copilot knowledge package and SharePoint distribution package: not yet created

## Foundation — completed

The following completed work remains the foundation for the Copilot-first path.

- Issue #2: governance, quality gates, source policy, evidence boundaries, ADRs, and repository policy checks
- Deny-by-default handling for unknown compatibility and unresolved FileMaker object references
- `research-candidate` separation from normalized reference data and FileMaker evidence
- Issue #7 Phase A: all 59 researched script steps normalized into the FileMaker 19.5 compatibility catalog
- Issue #7 Phase A: deterministic `compat` and `list-steps` reference CLI
- Issue #7 Phase B: exactly five design-only practical patterns for JSON validation, primary-key find, create, update, and synchronous PSOS
- A shared JSON result contract across the five patterns
- Required placeholders that fail closed instead of being inferred

Issue #3 also completed strict Script IR v2, deterministic v1 migration, installed-wheel checks, and conservative XML renderability rules. Those results remain as historical, maintained assets, but their expansion is now a deferred experimental track rather than a prerequisite for Copilot work.

## Next — Copilot knowledge package

Tracking: #8. This is the next central implementation step.

The next PR will create `docs/copilot/` as a small set of Markdown documents. That directory does not exist yet.

- Keep one document focused on one purpose.
- Explain execution-context selection across client, PSOS, server schedule, WebDirect, and other relevant contexts.
- Cover error handling, record locks, Commit, Revert, retries, idempotency, and security.
- State which internal system information Copilot must retrieve.
- Define the difference between a draft design and an implementation-ready design.
- Define stop conditions and prohibit inferred object names, IDs, privileges, and business rules.
- Define the complete human-readable design-document output.
- Define human review and FileMaker test procedures.
- Include a complete synthetic example.

Issue #7 continues only for unresolved FileMaker 19.5 knowledge that the Copilot package actually needs. Broad catalog completion, XML fixture capture, and unrelated research are not prerequisites for Issue #8.

Exit condition: the public Markdown gives Copilot enough bounded guidance to produce a reviewable design without claiming that `docs/copilot/`, SharePoint integration, or FileMaker runtime evidence already exists.

## Following — SharePoint package and pilot

Tracking: #15.

After the knowledge documents are reviewed:

- Build a distribution package containing only `docs/copilot/`.
- Add package version information and exact scope.
- Document manual placement into SharePoint.
- Keep the public package separate from internal objects, workflows, privileges, naming rules, specifications, and requirements.
- Define representative acceptance tests.
- Define instructions for the Copilot agent.

Automatic GitHub-to-SharePoint synchronization is not an initial requirement. The first pilot may use a documented manual update process.

## Deferred experimental tracks

The following work is frozen or optional until explicitly reapproved. None is a prerequisite for the Copilot knowledge package or the initial SharePoint pilot.

- Issue #4: fixture capture and semantic round-trip pipeline
- Issue #5: large static analyzer
- Issue #6: large AI evaluation suite
- XML renderer expansion
- clipboard expansion
- Script IR v2 expansion
- wheel distribution expansion
- FileMaker Pro/Server 19.5 hardware validation

Existing code remains in the repository. Deferred status does not promote its evidence or imply that XML is a formal deliverable.

## Previous phase history

The former dependency-ordered phases are retained here for traceability.

| Previous phase | Tracking | Historical result or current disposition |
| --- | --- | --- |
| Phase 0 — Governance foundation | #2 | Completed and retained in the Copilot foundation |
| Phase 1 — Strict Script IR v2 | #3 | Completed; retained as a frozen experimental subsystem |
| Phase 2 — Fixture and round-trip pipeline | #4 | Deferred |
| Phase 3 — Static analyzer | #5 | Deferred |
| Phase 4 — AI evaluation suite | #6 | Deferred |
| Phase 5 — Source-backed 19.5 catalog | #7 | Phase A and Phase B completed; further work is selective |
| Phase 6 — Expand renderer coverage | — | Deferred |
| Phase 7 — M365 Copilot knowledge package | #8 | Reordered as the next central implementation step |
| Phase 8 — FileMaker 19.5 hardware validation | — | Deferred and still required before any corresponding evidence promotion |

## Dependency rule

Copilot knowledge work depends on the completed governance and public knowledge foundation. It does not depend on Issues #4–#6, renderer or clipboard expansion, Script IR expansion, wheel expansion, or hardware validation.

No document, package, automated check, or Copilot output may be described as FileMaker paste-, runtime-, or FMSE-verified without the evidence required by [the evidence model](docs/EVIDENCE_MODEL.md).
