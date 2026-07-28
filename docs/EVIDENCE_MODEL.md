# Evidence Model

Evidence describes what has actually been demonstrated. It is not a confidence score and must not be inferred from model capability or code review.

## Ordered levels

### `documented`

A behavior or compatibility claim is supported by an identified source, preferably Claris documentation for FileMaker 19.

Does not prove:

- exact `fmxmlsnippet` shape
- clipboard acceptance
- runtime behavior in the target environment

### `public_fixture_observed`

A relevant XML or clipboard implementation has been observed in a public source with provenance recorded.

Does not prove that the fixture originated from FileMaker Pro 19.5 or works in the target environment.

### `structure_tested`

The repository can parse, normalize, render, lint, or round-trip the structure in automated tests.

Does not prove that FileMaker Pro accepts the XML.

### `clipboard_payload_tested`

The repository can deterministically encode and decode the expected Windows clipboard payload in automated tests.

Does not prove that FileMaker Pro 19.5 registers the assumed format name or accepts the payload.

### `fm19_5_paste_verified`

A named FileMaker Pro 19.5.x build accepted the clipboard payload and produced the intended script step or script structure without unresolved problems.

Required metadata:

- exact FileMaker Pro build
- Windows version
- fixture hash
- test procedure and result
- date and tester

### `fm19_5_runtime_verified`

The pasted object executed as intended in a FileMaker Pro 19.5 client against a controlled hosted test file.

Required metadata includes the paste evidence plus test case, input, expected result, actual result, and relevant context.

### `fmse_verified`

The script or pattern executed as intended in FileMaker Server 19.5 FMSE through PSOS or a FileMaker script schedule.

Required metadata:

- exact FileMaker Server build and OS
- execution mode (`psos` or `server_schedule`)
- account/privilege assumptions without credentials
- input and expected/actual result
- log or result evidence with sensitive information removed

## Promotion rules

Evidence is monotonic and cumulative. Promotion requires the relevant preceding evidence unless a documented exception is recorded in an ADR.

Allowed progression:

```text
documented
  -> public_fixture_observed
  -> structure_tested
  -> clipboard_payload_tested
  -> fm19_5_paste_verified
  -> fm19_5_runtime_verified
  -> fmse_verified
```

A claim may carry multiple applicable evidence values. For example, a server-compatibility claim can be `documented` and later `fmse_verified`.

## Prohibited promotions

- CI success must not create `fm19_5_paste_verified`, `fm19_5_runtime_verified`, or `fmse_verified`.
- A public fixture must not be described as a FileMaker 19.5 fixture unless its provenance proves that version.
- Human visual inspection of generated XML is not runtime evidence.
- A successful client execution is not FMSE evidence.
- One step or pattern's evidence must not be generalized to unrelated steps.

## Evidence state in outputs

AI and tooling should use these user-facing states:

- `design_ready`: design and required references are complete
- `xml_generated`: XML was generated and automated checks passed
- `paste_verified`: maps to `fm19_5_paste_verified`
- `runtime_verified`: maps to `fm19_5_runtime_verified`
- `fmse_verified`: maps directly to `fmse_verified`

Unverified states must be shown explicitly rather than omitted.

### Script IR v2 input boundary

Script IR v2 is a design input, not a verification record. Its
`status.evidence` field accepts only:

- `unverified`
- `design_ready`

It does not accept `xml_generated`, `paste_verified`, `runtime_verified`, or
`fmse_verified` as document assertions. In particular, a user-authored IR cannot
prove that its own XML was generated or validated.

If XML generation evidence is persisted in a future pipeline, it must be emitted
by the renderer as a sidecar manifest containing at least the toolkit version,
generation time, generated XML SHA-256, source IR SHA-256, and automated
validation result. Until that manifest exists, command and CI results are
transient `structure_tested` evidence only.

FileMaker paste, client runtime, and FMSE states require separate verification
records carrying the metadata defined above. They are never inferred from the
Script IR, generated XML, code review, wheel installation, or CI success.
