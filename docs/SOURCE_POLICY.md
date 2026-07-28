# Source Policy

## Source priority

1. Claris FileMaker 19 archived documentation and official release notes
2. Current Claris documentation when the behavior is explicitly version-stable or used only for comparison
3. Microsoft or platform documentation for Windows/API behavior
4. Reputable public FileMaker standards and open-source implementations
5. Community articles and forum discussions as leads, not sole proof of compatibility

## Primary versus secondary evidence

A source registry entry declares `sourceType`:

- `primary`: product vendor or platform owner documentation
- `secondary`: independent standard, implementation, article, or community material

Secondary sources may establish `public_fixture_observed` or identify questions for research. They do not independently establish FileMaker Server 19.5 compatibility or runtime behavior.

## Version discipline

- Every compatibility claim names the applicable FileMaker version or uses `unknown`.
- FileMaker 20/2023/2024/2025/2026 material must not be silently backported to 19.5.
- A current help page is not assumed to describe 19.5 unless its version history or archived equivalent supports that conclusion.
- Patch-specific behavior is recorded at the most precise available version.

## Recording sources

`sources/registry.json` is the canonical registry. Each entry includes:

- stable ID
- title and URL
- source type
- publisher
- target version or `version-neutral`
- scope
- retrieval date
- status
- notes

Catalogs and design rules reference sources by ID rather than duplicating URLs.

## Claim requirements

A claim affecting generated XML, server compatibility, data safety, or evidence promotion must:

- cite at least one source ID
- identify the execution environment
- separate documented behavior from inferred design guidance
- record uncertainty explicitly
- remain fail-closed when required information is absent

## Research artifacts

Deep Research and exploratory notes belong under a future `research/` area and are not normative. A separate review must extract accepted claims into the source registry, catalogs, and documentation.

## Copyright

Do not copy substantial portions of proprietary documentation. Store concise summaries, version applicability, decision-relevant facts, and source links.

## Link and staleness management

- Broken or redirected links do not automatically invalidate a claim, but they create a maintenance issue.
- Archived URLs are preferred for 19.5 where available.
- Retrieval dates support later auditing; they are not proof that content was current for 19.5.
