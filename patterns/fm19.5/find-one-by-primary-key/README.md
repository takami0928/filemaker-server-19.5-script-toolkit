# Find one record by primary key

The normative machine-readable record is
[`pattern.json`](pattern.json). This page explains how to review and apply it.

## 1. Problem this pattern solves

This pattern rebuilds a known layout context, performs an exact primary-key
find, preserves the immediate find error, and treats zero, one, and multiple
matches as different outcomes.

## 2. When to use it

Use it whenever a client, PSOS, or scheduled script must identify one record
before reading or modifying it. The update pattern composes this pattern.

## 3. When not to use it

Do not use it for broad searches, user-entered multi-request finds, or a field
that is not an approved primary key. Do not choose the first record when
duplicates are found.

## 4. Required placeholders

- `{{TARGET_LAYOUT}}`
- `{{TARGET_TABLE_OCCURRENCE}}`
- `{{PRIMARY_KEY_FIELD}}`
- `{{PRIMARY_KEY_VALUE_EXPRESSION}}`
- `{{RESULT_FIELD_MAP}}`

All references must come from the target solution and approved contracts.
Missing metadata blocks a completed script.

## 5. Input JSON example

```json
{
  "schemaVersion": 1,
  "requestId": "req-synthetic-002",
  "primaryKey": "synthetic-key-001"
}
```

## 6. Output JSON example

```json
{
  "ok": false,
  "code": "RECORD_NOT_FOUND",
  "message": "No matching record was found.",
  "data": null,
  "error": {
    "fileMakerCode": 401,
    "step": "Perform Find",
    "details": ""
  },
  "meta": {
    "pattern": "find-one-by-primary-key",
    "schemaVersion": 1
  }
}
```

## 7. FileMaker-style pseudocode

```text
Set Error Capture [ On ]
Go to Layout [ {{TARGET_LAYOUT}} ; Animation: None ]
Enter Find Mode [ Pause: Off ]
Set Field [ {{PRIMARY_KEY_FIELD}} ; <reviewed exact-match criterion from {{PRIMARY_KEY_VALUE_EXPRESSION}}> ]
Perform Find
Set Variable [ $findError ; Value: Get ( LastError ) ]
Set Variable [ $foundCount ; Value: Get ( FoundCount ) ]

If [ $findError = 401 or $foundCount = 0 ]
    Exit Script [ Result: <RECORD_NOT_FOUND JSON> ]
Else
    If [ $findError ≠ 0 ]
        Exit Script [ Result: <FIND_FAILED JSON> ]
    End If
End If

If [ $foundCount ≠ 1 ]
    Exit Script [ Result: <PRIMARY_KEY_NOT_UNIQUE JSON> ]
End If

Exit Script [ Result: <OK JSON built from {{RESULT_FIELD_MAP}}> ]
```

The exact-match and escaping calculation is a required design decision. Do not
place untrusted text into Find mode until that calculation is reviewed.

## 8. Success path

The layout is selected explicitly, the primary-key criterion is set in Find
mode, `Get ( LastError )` is captured immediately after `Perform Find`, and only
an exactly-one found count produces an OK result.

## 9. Error branches

- Empty or invalid criteria: `INVALID_FIND_CRITERIA`.
- No match, including FileMaker error 401: `RECORD_NOT_FOUND`.
- More than one match: `PRIMARY_KEY_NOT_UNIQUE`.
- Other find error: `FIND_FAILED`.

The candidate error catalog is the basis for numeric examples; exact frozen
19.5 wording remains research-candidate evidence.

## 10. Client, PSOS, and server-schedule differences

Client execution may start from any layout, but this pattern still selects its
own. PSOS and schedules have an independent session and must never assume the
client's layout, current record, found set, or sort order. `Go to Layout` and
`Enter Find Mode` are partial server-side entries whose animation/pause options
must be disabled as recorded in `pattern.json`.

## 11. Concurrency

A record may change after the find. A writing caller must open it and verify the
commit. A unique data-model rule, not this script alone, prevents duplicate
primary keys.

## 12. Security

Confirm read privileges and return only `{{RESULT_FIELD_MAP}}`. Never expose a
FileMaker record object, hidden field, or internal object identifier.

## 13. Renderer status

The context/find steps are `not_verified`; the existing control shell is
`experimental`. This complete pattern is not an XML-renderer template.

## 14. Unverified in FileMaker

No FileMaker Pro 19.5 paste or runtime test and no PSOS/server-schedule test has
been performed.

## 15. Sources

The pattern cites archived FileMaker 19 pages for every step and function,
server-session behavior, and the candidate error-code source. Exact IDs are in
`pattern.json`.
