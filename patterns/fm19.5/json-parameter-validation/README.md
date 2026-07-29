# Validate a JSON script parameter

The normative machine-readable record is
[`pattern.json`](pattern.json). This page explains how to review and apply it.

## 1. Problem this pattern solves

This pattern reads `Get ( ScriptParameter )`, rejects an empty or malformed
value, checks the agreed schema version and required keys, and passes only
validated values to subsequent work. Every failure returns the shared JSON
result envelope through `Exit Script`.

## 2. When to use it

Use it at the start of a client, PSOS, or server-schedule script that accepts a
JSON parameter. It is also the required server-side entry guard for the PSOS
pattern.

## 3. When not to use it

Do not use it as proof that arbitrary business values are semantically valid.
Do not accept an unknown schema version, silently coerce ambiguous data, or log
the raw parameter by default.

## 4. Required placeholders

- `{{EXPECTED_SCHEMA_VERSION}}`: version accepted by caller and callee.
- `{{REQUIRED_JSON_KEYS}}`: explicit required-key and expected-type rules.
- `{{SENSITIVE_JSON_KEYS}}`: values that must be redacted from logs.

All three must be resolved. An unresolved value blocks a completed script.

## 5. Input JSON example

```json
{
  "schemaVersion": 1,
  "requestId": "req-synthetic-001",
  "operation": "validate-example",
  "payload": {
    "value": "synthetic"
  }
}
```

## 6. Output JSON example

```json
{
  "ok": false,
  "code": "INVALID_JSON",
  "message": "The script parameter is not valid JSON.",
  "data": null,
  "error": {
    "fileMakerCode": null,
    "step": "JSONFormatElements",
    "details": ""
  },
  "meta": {
    "pattern": "json-parameter-validation",
    "schemaVersion": 1
  }
}
```

## 7. FileMaker-style pseudocode

```text
Set Error Capture [ On ]
Set Variable [ $input ; Value: Get ( ScriptParameter ) ]

If [ $input = "" ]
    Exit Script [ Result: <EMPTY_PARAMETER JSON> ]
End If

Set Variable [ $formatted ; Value: JSONFormatElements ( $input ) ]
If [ <JSONFormatElements indicates a parse failure> ]
    Exit Script [ Result: <INVALID_JSON JSON> ]
End If

Set Variable [ $schemaVersion ; Value: JSONGetElement ( $input ; "schemaVersion" ) ]
If [ $schemaVersion ≠ {{EXPECTED_SCHEMA_VERSION}} ]
    Exit Script [ Result: <UNSUPPORTED_SCHEMA_VERSION JSON> ]
End If

Set Variable [ $keys ; Value: JSONListKeys ( $input ; "" ) ]
If [ <a resolved rule in {{REQUIRED_JSON_KEYS}} fails> ]
    Exit Script [ Result: <MISSING_REQUIRED_KEY or INVALID_VALUE_TYPE JSON> ]
End If

Set Variable [ $validatedData ; Value: <resolved validated values> ]
```

The parse-failure and value-type calculations must be resolved against
FileMaker 19.5 behavior; the pseudocode does not invent a generic JSON-schema
engine.

## 8. Success path

The raw value is stored once, parsed before extraction, checked against the
resolved version and key rules, and copied into local validated variables. The
next pattern receives those variables rather than reading untrusted text again.

## 9. Error branches

- Empty parameter: `EMPTY_PARAMETER`.
- Malformed JSON: `INVALID_JSON`.
- Missing or unknown version: `UNSUPPORTED_SCHEMA_VERSION`.
- Missing required key: `MISSING_REQUIRED_KEY`.
- Unsupported value type: `INVALID_VALUE_TYPE`.

Each branch exits immediately with the shared result envelope.

## 10. Client, PSOS, and server-schedule differences

The calculation flow is the same. In PSOS and schedules, FMSE always behaves as
Set Error Capture On; an Off branch must not be designed. Local variables are
session-local and the caller's variables are not inherited by PSOS.

## 11. Concurrency

This pattern modifies no records. It can validate a request ID but cannot by
itself prevent a later write from running twice.

## 12. Security

Do not log raw JSON. Redact `{{SENSITIVE_JSON_KEYS}}`, limit diagnostic details,
and reject wider or newer contracts by default.

## 13. Renderer status

The control steps are `experimental` in the renderer evidence model. That does
not mean this full pattern can be rendered: JSON calculations and the completed
business script are design-only.

## 14. Unverified in FileMaker

No FileMaker Pro 19.5 paste or runtime test and no FileMaker Server 19.5 FMSE
test has been performed for this pattern.

## 15. Sources

The pattern cites the archived FileMaker 19 functions and script-step reference,
the individual function pages for `Get ( ScriptParameter )` and the JSON
functions, and the archived server-script execution guidance. Exact IDs are in
`pattern.json`.
