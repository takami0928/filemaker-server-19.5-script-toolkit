# Update a record and verify commit

The normative machine-readable record is
[`pattern.json`](pattern.json). This page explains how to review and apply it.

## 1. Problem this pattern solves

This pattern composes primary-key lookup, opens the one matching record for
editing, applies only explicit changes, commits without a dialog, and separates
lock, validation, privilege, and concurrent-modification failures.

## 2. When to use it

Use it for a reviewed one-record partial update in client, PSOS, or
server-schedule execution.

## 3. When not to use it

Do not use it for bulk replacement, an unresolved primary key, blind
last-write-wins behavior, or a request that cannot distinguish omitted
properties from explicit empty strings.

## 4. Required placeholders

- `{{TARGET_LAYOUT}}`
- `{{TARGET_TABLE_OCCURRENCE}}`
- `{{PRIMARY_KEY_FIELD}}`
- `{{PRIMARY_KEY_VALUE_EXPRESSION}}`
- `{{FIELD_ASSIGNMENTS}}`
- `{{OUTPUT_FIELD_MAP}}`

`{{VERSION_FIELD}}` and `{{EXPECTED_VERSION}}` are an optional pair. Omit
optimistic locking if the target solution has no approved version field; never
invent one.

## 5. Input JSON example

```json
{
  "schemaVersion": 1,
  "requestId": "req-synthetic-004",
  "primaryKey": "synthetic-key-004",
  "changes": {
    "displayValue": "Updated synthetic value"
  },
  "expectedVersion": 3
}
```

## 6. Output JSON example

```json
{
  "ok": false,
  "code": "RECORD_LOCKED",
  "message": "The record is being edited in another session.",
  "data": null,
  "error": {
    "fileMakerCode": 301,
    "step": "Open Record/Request",
    "details": ""
  },
  "meta": {
    "pattern": "update-record",
    "schemaVersion": 1
  }
}
```

## 7. FileMaker-style pseudocode

```text
<run find-one-by-primary-key through the exactly-one check>
Open Record/Request
Set Variable [ $openError ; Value: Get ( LastError ) ]
Set Variable [ $openState ; Value: Get ( RecordOpenState ) ]

If [ $openError ≠ 0 or <record is not editable> ]
    Exit Script [ Result: <RECORD_LOCKED or PRIVILEGE_DENIED JSON> ]
End If

If [ <both version placeholders are resolved and versions do not match> ]
    Exit Script [ Result: <OPTIMISTIC_LOCK_CONFLICT JSON> ]
End If

Set Variable [ $before ; Value: <approved values from {{OUTPUT_FIELD_MAP}}> ]
<for each property present in {{FIELD_ASSIGNMENTS}}>
    Set Field [ <resolved target field> ; <validated new value> ]
    Set Variable [ $fieldError ; Value: Get ( LastError ) ]
    If [ $fieldError ≠ 0 ]
        <reviewed revert/error branch>
    End If
<end repetition>

Commit Records/Requests [ With dialog: Off ]
Set Variable [ $commitError ; Value: Get ( LastError ) ]
If [ $commitError ≠ 0 ]
    <classify lock, validation, privilege, or other commit failure>
    <optionally Revert Record/Request [ With dialog: Off ] under reviewed policy>
    Exit Script [ Result: <error JSON> ]
End If

Exit Script [ Result: <UPDATED JSON with approved before/after values> ]
```

## 8. Success path

The composed find returns one record, the explicit open succeeds, optional
version checks pass, only present input properties are written, and the
immediate commit error is zero.

## 9. Error branches

The pattern separates not found, duplicate key, record/table lock, optimistic
lock mismatch, privilege, field assignment, validation, concurrent commit, and
unclassified commit failures. It never updates when the find returns zero or
multiple records.

## 10. Client, PSOS, and server-schedule differences

Every context rebuilds layout and found set. PSOS and schedules have no inherited
client state. Server-side layout, Find mode, commit, revert, and error-capture
partial conditions are explicit in `pattern.json`.

## 11. Concurrency

Opening the record and verifying commit are both required. Optional optimistic
locking uses only an existing version field. A retry must reload the record and
re-evaluate intent; stale values must never be written blindly.

## 12. Security

Confirm record and field privileges. Return only approved before/after fields,
and avoid logging sensitive old or new values. Revert can discard all
uncommitted edits in the current record.

## 13. Renderer status

Find, open, field, commit, and revert steps are `not_verified`; control steps
are `experimental`. This pattern is not a complete renderer template.

## 14. Unverified in FileMaker

No FileMaker Pro 19.5 paste or runtime test and no FileMaker Server 19.5 lock or
commit test has been performed.

## 15. Sources

The pattern cites archived FileMaker 19 step/function pages, server execution
guidance, and the candidate error-code source. Exact IDs are in `pattern.json`.
