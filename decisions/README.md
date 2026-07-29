# Architecture Decision Records

Use an ADR when a change affects repository architecture, evidence semantics, XML representation, FileMaker object reference handling, supported environments, or release policy.

## Naming

```text
NNNN-short-kebab-title.md
```

Numbers are sequential. `0000-template.md` is not a decision.

## Status

- `proposed`
- `accepted`
- `superseded`
- `rejected`
- `deprecated`

## Required content

- Context
- Decision
- Alternatives considered
- Consequences
- Evidence and sources
- Follow-up work

An ADR records why a choice was made. It does not replace implementation documentation or source-backed compatibility data.

## Records

- [ADR 0001](0001-govern-source-evidence-and-generation.md): govern sources, evidence, and generation
- [ADR 0002](0002-script-ir-v2.md): adopt strict Script IR v2
- [ADR 0003](0003-normalize-compatibility-catalog-and-cli.md): normalize the 19.5 compatibility catalog for reference CLI use
