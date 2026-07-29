# Issue #7 — FileMaker Server 19.5 Deep Research

This directory contains the research-candidate deliverables for Issue #7. They are intentionally separated from `catalog/fm19.5/verified-steps.json`: documented compatibility research is not FileMaker Pro 19.5 paste evidence or FileMaker Server 19.5 runtime evidence.

## Contents

Directly reviewable files:

- `coverage-audit.json` — explored-domain audit, corrected findings, and unresolved IDs
- `unresolved-questions.json` — 20 blockers requiring archived primary evidence, vendor evidence, or FileMaker 19.5 device tests
- `revision-notes.md` — revision and validation summary
- `manifest.json` — counts, hashes, and artifact classification

The complete deliverable set is stored as a split ZIP in `bundle/` because the connected repository writer has a per-write payload constraint:

- `issue-7-deep-research-artifacts.zip.part01`
- `issue-7-deep-research-artifacts.zip.part02`
- `issue-7-deep-research-artifacts.zip.part03`
- `issue-7-deep-research-artifacts.zip.part04`
- `issue-7-deep-research-artifacts.zip.part05`
- `issue-7-deep-research-artifacts.zip.part06`

Concatenate the binary parts in filename order. Expected reconstructed ZIP:

- size: `47115` bytes
- SHA-256: `a441f25400fcccd37e755019fe9d4de5a536a5a176a4592e320dcacee69ec278`

### Linux / macOS / Git Bash

```bash
cat research/issue-7/bundle/issue-7-deep-research-artifacts.zip.part* \
  > issue-7-deep-research-artifacts.zip
sha256sum issue-7-deep-research-artifacts.zip
unzip issue-7-deep-research-artifacts.zip
```

### PowerShell

```powershell
$parts = Get-ChildItem "research/issue-7/bundle/*.part*" | Sort-Object Name
$out = [System.IO.File]::OpenWrite("issue-7-deep-research-artifacts.zip")
try {
  foreach ($part in $parts) {
    $bytes = [System.IO.File]::ReadAllBytes($part.FullName)
    $out.Write($bytes, 0, $bytes.Length)
  }
} finally {
  $out.Dispose()
}
Get-FileHash issue-7-deep-research-artifacts.zip -Algorithm SHA256
Expand-Archive issue-7-deep-research-artifacts.zip
```

## Complete bundle files

- `README.md` — revised full research report
- `source-registry-candidates.json` — 110 source candidates
- `script-step-catalog-candidates.json` — 59 steps, 24 functions, 117 errors, and 15 later-version exclusions/transitions
- `unresolved-questions.json` — 20 unresolved questions
- `coverage-audit.json` — 18 audited domains
- `revision-notes.md`
- `manifest.json`

## Validation status

- requested high-priority steps: 51/51 classified
- duplicate source IDs: 0
- duplicate step names: 0
- unknown source references: 0
- asserted clipboard `fmxmlsnippet` numeric IDs: 0
- FileMaker Pro 19.5 paste verification: not performed
- FileMaker Server 19.5 runtime verification: not performed

The next implementation phase should normalize these candidates into repository schemas without promoting `partial`, `unknown`, cumulative-help claims, DDR IDs, or public fixtures beyond their evidence level.
