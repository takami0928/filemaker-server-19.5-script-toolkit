# Perform a server script and return JSON

The normative machine-readable record is
[`pattern.json`](pattern.json). This page explains how to review and apply it.

## 1. Problem this pattern solves

This pattern builds an explicit, versioned JSON request, calls a resolved server
script with Wait for completion On, reads `Get ( ScriptResult )`, and keeps
caller/session failure separate from the server script's business result.

## 2. When to use it

Use it when a client script needs synchronous server-side processing and must
receive a structured result.

## 3. When not to use it

Do not use this completed pattern with Wait for completion Off, when no result
is required, or when server context, authentication, idempotency, or the target
script is unresolved. Off is an asynchronous design with no dependable result
handoff to the initiating script.

## 4. Required placeholders

- `{{SERVER_SCRIPT_NAME}}`
- `{{REQUEST_SCHEMA_VERSION}}`
- `{{REQUEST_ID_EXPRESSION}}`
- `{{OPERATION_NAME}}`
- `{{PAYLOAD_EXPRESSION}}`
- `{{SERVER_CONTEXT_PLAN}}`
- `{{SENSITIVE_JSON_KEYS}}`
- `{{RELATED_FILE_AUTHENTICATION_PLAN}}`

All are blocking. Resolve the authentication plan to `not_applicable` only
after confirming that no related file is used.

## 5. Input JSON example

```json
{
  "schemaVersion": 1,
  "requestId": "req-synthetic-005",
  "operation": "synthetic-operation",
  "payload": {
    "primaryKey": "synthetic-key-005"
  }
}
```

## 6. Output JSON example

```json
{
  "ok": false,
  "code": "PSOS_CALL_FAILED",
  "message": "The server script could not be started or completed.",
  "data": null,
  "error": {
    "fileMakerCode": null,
    "step": "Perform Script on Server",
    "details": ""
  },
  "meta": {
    "pattern": "perform-script-on-server",
    "schemaVersion": 1
  }
}
```

## 7. FileMaker-style pseudocode

```text
# Caller
Set Error Capture [ On ]
Set Variable [ $request ; Value: JSONSetElement ( "{}" ;
    [ "schemaVersion" ; {{REQUEST_SCHEMA_VERSION}} ; JSONNumber ] ;
    [ "requestId" ; {{REQUEST_ID_EXPRESSION}} ; JSONString ] ;
    [ "operation" ; {{OPERATION_NAME}} ; JSONString ] ;
    [ "payload" ; {{PAYLOAD_EXPRESSION}} ; JSONObject ]
) ]
Perform Script on Server [
    Specified: {{SERVER_SCRIPT_NAME}} ;
    Parameter: $request ;
    Wait for completion: On
]
Set Variable [ $callError ; Value: Get ( LastError ) ]
Set Variable [ $serverResult ; Value: Get ( ScriptResult ) ]

If [ $callError ≠ 0 ]
    Exit Script [ Result: <PSOS call-error JSON> ]
End If
If [ <JSONFormatElements indicates that $serverResult is invalid> ]
    Exit Script [ Result: <INVALID_SERVER_RESULT JSON> ]
End If
Exit Script [ Result: $serverResult ]

# Server script
Set Error Capture [ On ]
Set Variable [ $input ; Value: Get ( ScriptParameter ) ]
<run json-parameter-validation>
<rebuild layout, found set, and current record from {{SERVER_CONTEXT_PLAN}}>
<run the selected business pattern>
Exit Script [ Result: <common JSON result> ]
```

The symbolic JSON type names illustrate the request shape; this repository does
not turn this pseudocode into XML.

## 8. Success path

The caller builds a request with schema version, request ID, operation, and
payload. The independent FMSE session validates it again, rebuilds all context,
and returns the common envelope. The caller first checks the immediate PSOS
error and only then parses the script result.

## 9. Error branches

Call failure, timeout, administrator stop, session-capacity failure, invalid
result JSON, duplicate request, and server business error are distinct. A
timeout or stop means completion may be unknown, so a write must be reconciled
by request ID before retry.

## 10. Client, PSOS, and server-schedule differences

The completed caller pattern supports `client`. The server target executes in
`psos` and gets a separate session. It inherits no client layout, found set,
current record, sort order, local/global variables, or global-field values.
A scheduled script can reuse the server-side business patterns directly, but it
is not the caller context defined by this pattern.

## 11. Concurrency

Each call creates an independent session. Nested calls and concurrent callers
consume capacity. Use request IDs and an approved idempotency design; never
blindly retry an interrupted write.

## 12. Security

Do not put credentials or unnecessary sensitive values in the parameter.
Redact `{{SENSITIVE_JSON_KEYS}}`, log only approved request metadata, resolve
related-file authentication, and verify script/object privileges for the
server account.

## 13. Renderer status

`Perform Script on Server` is `not_verified`; control steps are
`experimental`. The pattern cannot be rendered as a complete script by the
current renderer.

## 14. Unverified in FileMaker

No FileMaker Pro 19.5 paste/runtime test, no PSOS result test, and no FileMaker
Server 19.5 timeout/capacity/authentication test has been performed.

## 15. Sources

The pattern cites archived FileMaker 19 pages for PSOS, server execution,
`Get ( ScriptParameter )`, `Get ( ScriptResult )`, `Get ( LastError )`, and JSON
functions. Exact IDs are in `pattern.json`.
