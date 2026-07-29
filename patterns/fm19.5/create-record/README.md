# Create a record and verify commit

The normative machine-readable record is
[`pattern.json`](pattern.json). This page explains how to review and apply it.

## 1. Problem this pattern solves

This pattern validates required data, creates one record in a resolved context,
sets approved fields, commits without a dialog, captures the commit error
immediately, and returns the new primary key in the shared JSON envelope.

## 2. When to use it

Use it for a reviewed one-record create operation in client, PSOS, or
server-schedule execution.

## 3. When not to use it

Do not use it for bulk import, an unresolved primary-key rule, an operation that
requires an interactive validation dialog, or a create that lacks a reviewed
duplicate/idempotency policy.

## 4. Required placeholders

- `{{TARGET_LAYOUT}}`
- `{{TARGET_TABLE_OCCURRENCE}}`
- `{{PRIMARY_KEY_FIELD}}`
- `{{GENERATED_PRIMARY_KEY_EXPRESSION}}`
- `{{FIELD_ASSIGNMENTS}}`

`{{IDEMPOTENCY_FIELD}}` and `{{IDEMPOTENCY_KEY_EXPRESSION}}` are an optional
pair. If the target solution does not define them, omit idempotency handling and
document the risk; never invent a field.

## 5. Input JSON example

```json
{
  "schemaVersion": 1,
  "requestId": "req-synthetic-003",
  "payload": {
    "displayValue": "Synthetic value"
  },
  "idempotencyKey": "idem-synthetic-003"
}
```

## 6. Output JSON example

```json
{
  "ok": true,
  "code": "CREATED",
  "message": "",
  "data": {
    "primaryKey": "synthetic-key-003"
  },
  "error": null,
  "meta": {
    "pattern": "create-record",
    "schemaVersion": 1
  }
}
```

## 7. FileMaker-style pseudocode

```text
Set Error Capture [ On ]
<validate required input>
<apply resolved idempotency check, or explicitly omit it>
Go to Layout [ {{TARGET_LAYOUT}} ; Animation: None ]
New Record/Request
Set Variable [ $createError ; Value: Get ( LastError ) ]
If [ $createError ≠ 0 ]
    Exit Script [ Result: <CREATE_FAILED JSON> ]
End If

Set Field [ {{PRIMARY_KEY_FIELD}} ; {{GENERATED_PRIMARY_KEY_EXPRESSION}} ]
Set Variable [ $fieldError ; Value: Get ( LastError ) ]
If [ $fieldError ≠ 0 ]
    <reviewed failure/revert branch>
End If

<repeat Set Field and immediate error capture for {{FIELD_ASSIGNMENTS}}>
Commit Records/Requests [ With dialog: Off ]
Set Variable [ $commitError ; Value: Get ( LastError ) ]

If [ $commitError ≠ 0 ]
    If [ <reviewed revert policy permits discarding all uncommitted values> ]
        Revert Record/Request [ With dialog: Off ]
    End If
    Exit Script [ Result: <classified commit error JSON> ]
End If

Exit Script [ Result: <CREATED JSON> ]
```

## 8. Success path

Input validation finishes before creation. Every write error is captured before
another step runs. Only a zero commit error produces `CREATED`, using the actual
resolved primary-key value.

## 9. Error branches

The pattern separates creation, field assignment, privilege, validation,
uniqueness, commit, and duplicate-request failures. It records candidate
FileMaker codes such as 504 only where Issue #7 provides a source-backed
candidate mapping.

## 10. Client, PSOS, and server-schedule differences

All contexts select `{{TARGET_LAYOUT}}` explicitly. PSOS and schedules do not
inherit client context. Server-side `Go to Layout`, commit, revert, and error
capture are partial entries with the no-animation/no-dialog/FMSE-always-On
conditions in `pattern.json`.

## 11. Concurrency

Two sessions can create the same logical entity. A preflight find is not an
atomic uniqueness guarantee. Prefer an existing unique or idempotency field
when the target design provides one, and reconcile uncertain retries by request
ID.

## 12. Security

Confirm record-create and field-edit privileges. Do not return or log fields
outside the approved contract. An automatic revert can discard data and must be
approved explicitly.

## 13. Renderer status

Create, field, commit, and revert steps are `not_verified`; control steps are
`experimental`. The pattern is design-only and cannot be rendered as a complete
script by the current renderer.

## 14. Unverified in FileMaker

No FileMaker Pro 19.5 paste or runtime test and no FileMaker Server 19.5 create
test has been performed.

## 15. Sources

The pattern cites archived FileMaker 19 step/function pages, server execution
guidance, and the candidate error-code source. Exact IDs are in `pattern.json`.
