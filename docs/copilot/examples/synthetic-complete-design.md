# SYN_Task status update through synchronous PSOS

この設計は完全な合成例です。名称、値、requirement、privilegeは実在環境を表しません。FileMaker Pro／Server 19.5でpasteまたはruntime testを行っていません。

## Synthetic internal context

| Type | Synthetic fact |
| --- | --- |
| File | `SYN_Operations`。FileMaker Server 19.5へhostされる想定。 |
| Table | `SYN_Task` |
| TO | `SYN_TASK__by_id`。base tableは`SYN_Task`。 |
| Layout | `SYN_Task_Server`。base TOは`SYN_TASK__by_id`。server処理専用で、animationやdialogを使用しない。 |
| Existing entry caller script | `SYN_UI_TaskController`。合成UIからentry scriptを呼ぶ既存caller。 |
| Client entry script | `SYN_UI_RequestTaskUpdate` |
| Server script | `SYN_SRV_UpdateTask` |
| Existing helper script | `SYN_SYS_ValidateJsonContract`。`json-parameter-validation` patternを実装済みとする合成helper。 |
| Existing custom function | `SYN_Result ( ok ; code ; message ; dataJson ; fileMakerCode ; stepName ; details ; patternName )` |
| Privilege set | `SYN_Automation` |
| Related file | 使用しない。authentication planは`not_applicable`。 |

### Synthetic fields

| Field | Type／rule | Purpose |
| --- | --- | --- |
| `SYN_TASK__by_id::SYN_TaskId` | Number、stored、not empty、unique、positive integer | primary key |
| `SYN_TASK__by_id::SYN_Status` | Text、`SYN_queued`／`SYN_active`／`SYN_done`のみ | 更新対象 |
| `SYN_TASK__by_id::SYN_Version` | Number、stored、not empty、non-negative integer | optimistic version |
| `SYN_TASK__by_id::SYN_LastRequestId` | Text、stored、not empty、unique | idempotency |
| `SYN_TASK__by_id::SYN_LastRequestJson` | Text、stored、not empty | 最後にCommitした正規化済みrequest |
| `SYN_TASK__by_id::SYN_LastResultJson` | Text、stored、not empty | 最後にCommitした共通success result |

合成初期recordは、`SYN_TaskId = 1001`、`SYN_Status = "SYN_active"`、`SYN_Version = 7`、`SYN_LastRequestId = "SYN_REQ_0000"`です。`SYN_LastRequestJson`と`SYN_LastResultJson`には、`SYN_REQ_0000`に対応する有効な合成requestと共通success resultが保存済みです。

### Existing helper contract

`SYN_SYS_ValidateJsonContract`は、次を確認済みfactとして扱う合成existing scriptです。

- parameterは`contractName`と`document`を持つJSON。
- `SYN_TaskUpdateRequest_v1`は、rootの追加keyを拒否し、`schemaVersion = 1`、`requestId`が`SYN_REQ_`と4桁数字、`operation = "SYN_updateTaskStatus"`、positive integerの`payload.taskId`、列挙済み`payload.newStatus`、non-negative integerの`payload.expectedVersion`を必須とする。
- `SYN_CommonResult_v1`は[`common-result.schema.json`](../../../patterns/fm19.5/common-result.schema.json)のfieldとtypeを確認する。
- success時は`meta.pattern = "json-parameter-validation"`の共通resultを返し、`data.document`に正規化済みdocumentを入れる。
- failure時は`INVALID_JSON`またはcontract別validation codeを返し、raw documentやcredentialをmessage／diagnosticへ含めない。
- `client`と`psos`で実行可能で、内部FileMaker IDを必要としない。

### Existing result function contract

`SYN_Result`は、`dataJson`を有効なJSON valueとして共通resultへ設定します。`ok = True`なら`error = null`、`ok = False`なら`fileMakerCode`、`stepName`、`details`から`error` objectを作り、空の`fileMakerCode`はJSON nullとします。`patternName`は既存5 patternのIDだけを受け付け、返り値は常に[`common-result.schema.json`](../../../patterns/fm19.5/common-result.schema.json)へ適合します。

helper scriptとcustom functionはいずれも合成対象systemのconfirmed existing objectであり、第6の公開standard patternではありません。対象systemに同等objectが存在しない場合、この例をそのまま`implementation_ready`として使えません。

## Requirement

`SYN_UI_RequestTaskUpdate`は合成JSON requestを検証し、`SYN_SRV_UpdateTask`をWait for completion Onの同期PSOSで呼び出します。server scriptはtaskをprimary keyで1件特定し、record lockとexpected versionを確認してstatusを更新します。同一request IDは二重適用せず、retryable lock／Commit conflictは全contextを再構築して最大2 attemptとします。

## Design status

Design status: implementation_ready

採用した機能に必要な合成object、helper contract、privilege、exact option、retry上限、idempotency field、version fieldはすべてこの例で解決済みです。

## Script map

| Script | Primary responsibility | Context | Caller／trigger |
| --- | --- | --- | --- |
| `SYN_UI_RequestTaskUpdate` | requestを検証し、同期PSOSのcall resultとbusiness resultを分離する | `client` | `SYN_UI_TaskController`からversion付きJSON parameterで呼ばれる |
| `SYN_SRV_UpdateTask` | 1件のtaskをidempotentかつoptimistic version付きで更新する | `psos` | `SYN_UI_RequestTaskUpdate`の`Perform Script on Server`、Wait for completion On |

## Purpose

- `SYN_UI_RequestTaskUpdate`: validated requestを同期PSOSへ渡し、call failureとserver business resultを分離してcallerへ返す。
- `SYN_SRV_UpdateTask`: 1件の`SYN_Task`をidempotentかつoptimistic version付きで更新し、Commit結果を返す。

## Execution topology

```text
SYN_UI_TaskController — client（既存の外部caller）
    └─ Parameter: SYN_TaskUpdateRequest_v1 document
       SYN_UI_RequestTaskUpdate — client（entry point）
           └─ Perform Script on Server; Wait for completion: On
              Parameter: $request
              Result: Get ( ScriptResult ) → $serverResult
              SYN_SRV_UpdateTask — psos
```

`SYN_UI_TaskController`からentry pointへのcallは同期で、parameterは[Input JSON contract](#input-json-contract)の完全なdocument、resultは`SYN_UI_RequestTaskUpdate`の`Exit Script` resultです。entry pointからserver scriptへのcallも同期で、validated `$request`を渡し、`Get ( ScriptResult )`を`$serverResult`へ保存します。server scriptは独立sessionとして全contextを再構築します。

## Entry point and trigger

- entry point: `SYN_UI_RequestTaskUpdate`
- external caller／trigger: `SYN_UI_TaskController`が、合成UIのsubmit actionでversion付きJSON parameterを渡して同期実行する。
- callee: `SYN_SRV_UpdateTask`
- callee context: `psos`
- wait behavior: Wait for completion On
- callee parameter: `$request`
- callee result: `Get ( ScriptResult )`を`$serverResult`へ保存し、contract検証後にentry callerへ返す。

## Preconditions

- `SYN_Operations`がFileMaker Server 19.5へhostされている。
- `SYN_Task_Server`のbase TOが`SYN_TASK__by_id`である。
- `SYN_SYS_ValidateJsonContract`、`SYN_Result`、2つのcontractが上記どおり存在する。
- `SYN_UI_TaskController`が上記Input JSON contractをparameterとして`SYN_UI_RequestTaskUpdate`を同期実行する。
- 実行sessionが`SYN_Automation` privilegeを持つ。
- `SYN_TaskId`、`SYN_Version`、`SYN_LastRequestId`のvalidation ruleが上記どおり設定済みである。`requestId`は1つのlogical requestへ一度だけ割り当て、異なるpayloadへ再利用しない。
- server側のrelated-file authenticationは`not_applicable`である。

## Confirmed facts

すべてのfactはこの合成context内だけで確認済みです。59-step compatibility catalogと既存5 patternを公開側の正本とし、実在FileMaker fileでの存在または動作を主張しません。

## Assumptions

なし。合成context外へ適用するときは、すべてを対象systemのconfirmed factへ置換します。

## Unresolved required information

なし。

## Unresolved optional information

なし。

## Explicitly omitted optional features

- auxiliary retry-wait layout: 省略。retryは同じserver script内で直ちに最大2 attemptとする。将来backoffを採用する場合、FMSE session消費と許容delayを確認する。
- audit field: 省略。現在のresultはbefore／afterをcallerへ返すが、永続audit logは作らない。将来追加する場合、保存field、retention、privilegeを確認する。
- recovery script: 省略。Commit前のfield errorまたはCommit failureではcurrent recordをRevertする。複数record compensationはscope外。

## Input JSON contract

```json
{
  "schemaVersion": 1,
  "requestId": "SYN_REQ_0001",
  "operation": "SYN_updateTaskStatus",
  "payload": {
    "taskId": 1001,
    "newStatus": "SYN_done",
    "expectedVersion": 7
  }
}
```

追加keyは禁止します。`requestId`、`operation`、`payload`のtype／value ruleは`SYN_TaskUpdateRequest_v1`で検証します。

## Result JSON contract

成功例:

```json
{
  "ok": true,
  "code": "UPDATED",
  "message": "",
  "data": {
    "taskId": 1001,
    "beforeStatus": "SYN_active",
    "afterStatus": "SYN_done",
    "version": 8,
    "replayed": false
  },
  "error": null,
  "meta": {
    "pattern": "update-record",
    "schemaVersion": 1
  }
}
```

すべてのresultは[`common-result.schema.json`](../../../patterns/fm19.5/common-result.schema.json)に従います。caller-side PSOS failureの`meta.pattern`は`perform-script-on-server`、validation failureは`json-parameter-validation`です。

## Required FileMaker objects

| Type | Exact synthetic name | Use |
| --- | --- | --- |
| file | `SYN_Operations` | caller／server scriptをhostする |
| table | `SYN_Task` | task record |
| TO | `SYN_TASK__by_id` | server layout context |
| layout | `SYN_Task_Server` | find／update context |
| field | `SYN_TASK__by_id::SYN_TaskId` | primary-key find |
| field | `SYN_TASK__by_id::SYN_Status` | status update |
| field | `SYN_TASK__by_id::SYN_Version` | optimistic version |
| field | `SYN_TASK__by_id::SYN_LastRequestId` | idempotency |
| field | `SYN_TASK__by_id::SYN_LastRequestJson` | idempotency key reuse検出 |
| field | `SYN_TASK__by_id::SYN_LastResultJson` | duplicate requestへのresult replay |
| script | `SYN_UI_RequestTaskUpdate` | client wrapper |
| script | `SYN_SRV_UpdateTask` | PSOS business script |
| existing script | `SYN_UI_TaskController` | entry pointへversion付きJSONを渡すUI caller |
| existing script | `SYN_SYS_ValidateJsonContract` | request／result validation |
| existing custom function | `SYN_Result` | 共通result生成 |

internal object IDは使用しません。

## Privilege requirements

`SYN_Automation`は次を持ちます。

- 4 scriptのexecute権限
- `SYN_Task`のrecord read／edit権限
- 6 fieldのview権限と、`SYN_Status`、`SYN_Version`、`SYN_LastRequestId`、`SYN_LastRequestJson`、`SYN_LastResultJson`のedit権限
- `SYN_Task_Server`を使用するために必要なaccess

delete、create、schema変更、credential参照の権限は不要です。

## Variables

| Variable | Calculation／initial value | Purpose |
| --- | --- | --- |
| `$rawInput` | `Get ( ScriptParameter )` | caller／serverのraw parameter |
| `$validationRequest` | 各validation call直前のexact `JSONSetElement` calculation | validation input |
| `$helperError` | helper `Perform Script`直後の`Get ( LastError )` | helper call error |
| `$validationResult` | `Get ( ScriptResult )` | helper result |
| `$request` | validated `data.document` | PSOS parameter |
| `$callError` | PSOS直後の`Get ( LastError )` | call-level error |
| `$serverResult` | PSOS直後の`Get ( ScriptResult )` | server business result |
| `$taskId` | validated `payload.taskId` | primary key |
| `$newStatus` | validated `payload.newStatus` | new value |
| `$expectedVersion` | validated `payload.expectedVersion` | optimistic check |
| `$requestId` | validated `requestId` | idempotency |
| `$attempt` | 初期値`0`、各loop先頭で`$attempt + 1` | 最大2回のretry |
| `$lastRetryError` | 初期値`""` | exhaustion時に保持する最後のretryable error |
| `$lastRetryStep` | 初期値`""` | exhaustion時に保持するstep |
| `$layoutError` | `Go to Layout`直後の`Get ( LastError )` | server layout context |
| `$findModeError` | `Enter Find Mode`直後の`Get ( LastError )` | find-mode transition |
| `$criteriaError` | find条件用`Set Field`直後の`Get ( LastError )` | primary-key criterion |
| `$findError` | `Perform Find`直後の`Get ( LastError )` | find result |
| `$foundCount` | `Get ( FoundCount )` | exactly-one check |
| `$openError` | `Open Record/Request`直後の`Get ( LastError )` | lock／privilege |
| `$beforeStatus` | current `SYN_Status` | approved result |
| `$successResult` | `SYN_Result`で作るsuccess JSON | Commit成功後に返すresult |
| `$replayResult` | 保存済みresultの`data.replayed`をtrueにしたJSON | duplicate response |
| `$fieldError` | 各`Set Field`直後の`Get ( LastError )` | assignment result |
| `$commitError` | Commit直後の`Get ( LastError )` | persistence result |
| `$revertError` | Revert直後の`Get ( LastError )` | cleanup result |

## FileMaker-format script steps

### SYN_UI_RequestTaskUpdate — `client`

1. `Set Error Capture` [ On ]
2. `Set Variable` [ `$rawInput` ; Value: `Get ( ScriptParameter )` ]
3. `Set Variable` [ `$validationRequest` ; Value: `JSONSetElement ( "{}" ; [ "contractName" ; "SYN_TaskUpdateRequest_v1" ; JSONString ] ; [ "document" ; $rawInput ; JSONString ] )` ]
4. `Perform Script` [ Specified: `SYN_SYS_ValidateJsonContract` ; Parameter: `$validationRequest` ]
5. `Set Variable` [ `$helperError` ; Value: `Get ( LastError )` ]
6. `Set Variable` [ `$validationResult` ; Value: `Get ( ScriptResult )` ]
7. `If` [ `$helperError ≠ 0` ]
8. `Exit Script` [ Result: `SYN_Result ( False ; "VALIDATION_HELPER_FAILED" ; "The request validator could not run." ; "null" ; $helperError ; "Perform Script" ; "" ; "json-parameter-validation" )` ]
9. `End If`
10. `If` [ `JSONGetElement ( $validationResult ; "ok" ) ≠ 1` ]
11. `Exit Script` [ Result: `$validationResult` ]
12. `End If`
13. `Set Variable` [ `$request` ; Value: `JSONGetElement ( $validationResult ; "data.document" )` ]
14. `Perform Script on Server` [ Specified: `SYN_SRV_UpdateTask` ; Parameter: `$request` ; Wait for completion: On ]
15. `Set Variable` [ `$callError` ; Value: `Get ( LastError )` ]
16. `Set Variable` [ `$serverResult` ; Value: `Get ( ScriptResult )` ]
17. `If` [ `$callError ≠ 0` ]
18. `Set Variable` [ `$serverResult` ; Value: `SYN_Result ( False ; "PSOS_CALL_FAILED" ; "The server script could not be completed." ; "null" ; $callError ; "Perform Script on Server" ; "" ; "perform-script-on-server" )` ]
19. `Exit Script` [ Result: `$serverResult` ]
20. `End If`
21. `Set Variable` [ `$validationRequest` ; Value: `JSONSetElement ( "{}" ; [ "contractName" ; "SYN_CommonResult_v1" ; JSONString ] ; [ "document" ; $serverResult ; JSONString ] )` ]
22. `Perform Script` [ Specified: `SYN_SYS_ValidateJsonContract` ; Parameter: `$validationRequest` ]
23. `Set Variable` [ `$helperError` ; Value: `Get ( LastError )` ]
24. `Set Variable` [ `$validationResult` ; Value: `Get ( ScriptResult )` ]
25. `If` [ `$helperError ≠ 0` ]
26. `Exit Script` [ Result: `SYN_Result ( False ; "INVALID_SERVER_RESULT" ; "The server result could not be validated." ; "null" ; $helperError ; "Perform Script" ; "" ; "perform-script-on-server" )` ]
27. `End If`
28. `If` [ `JSONGetElement ( $validationResult ; "ok" ) ≠ 1` ]
29. `Exit Script` [ Result: `SYN_Result ( False ; "INVALID_SERVER_RESULT" ; "The server result is outside the approved contract." ; "null" ; "" ; "SYN_SYS_ValidateJsonContract" ; JSONGetElement ( $validationResult ; "code" ) ; "perform-script-on-server" )` ]
30. `End If`
31. `Exit Script` [ Result: `$serverResult` ]

### SYN_SRV_UpdateTask — `psos`

1. `Set Error Capture` [ On ]
2. `Set Variable` [ `$rawInput` ; Value: `Get ( ScriptParameter )` ]
3. `Set Variable` [ `$validationRequest` ; Value: `JSONSetElement ( "{}" ; [ "contractName" ; "SYN_TaskUpdateRequest_v1" ; JSONString ] ; [ "document" ; $rawInput ; JSONString ] )` ]
4. `Perform Script` [ Specified: `SYN_SYS_ValidateJsonContract` ; Parameter: `$validationRequest` ]
5. `Set Variable` [ `$helperError` ; Value: `Get ( LastError )` ]
6. `Set Variable` [ `$validationResult` ; Value: `Get ( ScriptResult )` ]
7. `If` [ `$helperError ≠ 0` ]
8. `Exit Script` [ Result: `SYN_Result ( False ; "VALIDATION_HELPER_FAILED" ; "The request validator could not run." ; "null" ; $helperError ; "Perform Script" ; "" ; "json-parameter-validation" )` ]
9. `End If`
10. `If` [ `JSONGetElement ( $validationResult ; "ok" ) ≠ 1` ]
11. `Exit Script` [ Result: `$validationResult` ]
12. `End If`
13. `Set Variable` [ `$request` ; Value: `JSONGetElement ( $validationResult ; "data.document" )` ]
14. `Set Variable` [ `$taskId` ; Value: `JSONGetElement ( $request ; "payload.taskId" )` ]
15. `Set Variable` [ `$newStatus` ; Value: `JSONGetElement ( $request ; "payload.newStatus" )` ]
16. `Set Variable` [ `$expectedVersion` ; Value: `JSONGetElement ( $request ; "payload.expectedVersion" )` ]
17. `Set Variable` [ `$requestId` ; Value: `JSONGetElement ( $request ; "requestId" )` ]
18. `Set Variable` [ `$attempt` ; Value: `0` ]
19. `Set Variable` [ `$lastRetryError` ; Value: `""` ]
20. `Set Variable` [ `$lastRetryStep` ; Value: `""` ]
21. `Loop`
22. `Set Variable` [ `$attempt` ; Value: `$attempt + 1` ]
23. `Go to Layout` [ Layout: `SYN_Task_Server` ; Animation: None ]
24. `Set Variable` [ `$layoutError` ; Value: `Get ( LastError )` ]
25. `If` [ `$layoutError ≠ 0` ]
26. `Exit Script` [ Result: `SYN_Result ( False ; "CONTEXT_SETUP_FAILED" ; "The server layout context could not be established." ; "null" ; $layoutError ; "Go to Layout" ; "" ; "update-record" )` ]
27. `End If`
28. `Enter Find Mode` [ Pause: Off ]
29. `Set Variable` [ `$findModeError` ; Value: `Get ( LastError )` ]
30. `If` [ `$findModeError ≠ 0` ]
31. `Exit Script` [ Result: `SYN_Result ( False ; "FIND_MODE_FAILED" ; "Find mode could not be entered." ; "null" ; $findModeError ; "Enter Find Mode" ; "" ; "find-one-by-primary-key" )` ]
32. `End If`
33. `Set Field` [ `SYN_TASK__by_id::SYN_TaskId` ; `$taskId` ]
34. `Set Variable` [ `$criteriaError` ; Value: `Get ( LastError )` ]
35. `If` [ `$criteriaError ≠ 0` ]
36. `Exit Script` [ Result: `SYN_Result ( False ; "FIND_CRITERIA_FAILED" ; "The primary-key find criterion could not be set." ; "null" ; $criteriaError ; "Set Field" ; "" ; "find-one-by-primary-key" )` ]
37. `End If`
38. `Perform Find`
39. `Set Variable` [ `$findError` ; Value: `Get ( LastError )` ]
40. `Set Variable` [ `$foundCount` ; Value: `Get ( FoundCount )` ]
41. `If` [ `$findError = 401 or $foundCount = 0` ]
42. `Exit Script` [ Result: `SYN_Result ( False ; "RECORD_NOT_FOUND" ; "No matching task was found." ; "null" ; If ( $findError = 0 ; "" ; $findError ) ; "Perform Find" ; "" ; "update-record" )` ]
43. `End If`
44. `If` [ `$findError ≠ 0 or $foundCount ≠ 1` ]
45. `Exit Script` [ Result: `SYN_Result ( False ; If ( $foundCount > 1 ; "PRIMARY_KEY_NOT_UNIQUE" ; "FIND_FAILED" ) ; "The primary-key find did not resolve exactly one task." ; "null" ; If ( $findError = 0 ; "" ; $findError ) ; "Perform Find" ; "" ; "update-record" )` ]
46. `End If`
47. `Open Record/Request`
48. `Set Variable` [ `$openError` ; Value: `Get ( LastError )` ]
49. `If` [ `$openError = 301 or $openError = 302` ]
50. `Set Variable` [ `$lastRetryError` ; Value: `$openError` ]
51. `Set Variable` [ `$lastRetryStep` ; Value: `"Open Record/Request"` ]
52. `Exit Loop If` [ `$attempt ≥ 2` ]
53. `Else`
54. `If` [ `$openError ≠ 0` ]
55. `Exit Script` [ Result: `SYN_Result ( False ; If ( $openError = 200 or $openError = 201 or $openError = 202 ; "PRIVILEGE_DENIED" ; "OPEN_FAILED" ) ; "The task could not be opened for update." ; "null" ; $openError ; "Open Record/Request" ; "" ; "update-record" )` ]
56. `End If`
57. `If` [ `SYN_TASK__by_id::SYN_LastRequestId = $requestId` ]
58. `If` [ `SYN_TASK__by_id::SYN_LastRequestJson ≠ $request` ]
59. `Revert Record/Request` [ With dialog: Off ]
60. `Set Variable` [ `$revertError` ; Value: `Get ( LastError )` ]
61. `If` [ `$revertError ≠ 0` ]
62. `Exit Script` [ Result: `SYN_Result ( False ; "CLEANUP_FAILED" ; "The duplicate-request check could not release the record." ; "null" ; $revertError ; "Revert Record/Request" ; "" ; "update-record" )` ]
63. `End If`
64. `Exit Script` [ Result: `SYN_Result ( False ; "DUPLICATE_REQUEST" ; "The request ID was reused with different input." ; "null" ; "" ; "SYN_LastRequestJson" ; "" ; "perform-script-on-server" )` ]
65. `Else`
66. `Set Variable` [ `$replayResult` ; Value: `JSONSetElement ( SYN_TASK__by_id::SYN_LastResultJson ; "data.replayed" ; True ; JSONBoolean )` ]
67. `Revert Record/Request` [ With dialog: Off ]
68. `Set Variable` [ `$revertError` ; Value: `Get ( LastError )` ]
69. `If` [ `$revertError ≠ 0` ]
70. `Exit Script` [ Result: `SYN_Result ( False ; "CLEANUP_FAILED" ; "The duplicate request result could not release the record." ; "null" ; $revertError ; "Revert Record/Request" ; "" ; "update-record" )` ]
71. `End If`
72. `Exit Script` [ Result: `$replayResult` ]
73. `End If`
74. `End If`
75. `If` [ `SYN_TASK__by_id::SYN_Version ≠ $expectedVersion` ]
76. `Revert Record/Request` [ With dialog: Off ]
77. `Set Variable` [ `$revertError` ; Value: `Get ( LastError )` ]
78. `If` [ `$revertError ≠ 0` ]
79. `Exit Script` [ Result: `SYN_Result ( False ; "CLEANUP_FAILED" ; "The version-conflict branch could not release the record." ; "null" ; $revertError ; "Revert Record/Request" ; "" ; "update-record" )` ]
80. `End If`
81. `Exit Script` [ Result: `SYN_Result ( False ; "OPTIMISTIC_LOCK_CONFLICT" ; "The task version changed." ; "null" ; "" ; "SYN_Version" ; "" ; "update-record" )` ]
82. `End If`
83. `Set Variable` [ `$beforeStatus` ; Value: `SYN_TASK__by_id::SYN_Status` ]
84. `Set Variable` [ `$successResult` ; Value: `SYN_Result ( True ; "UPDATED" ; "" ; JSONSetElement ( "{}" ; [ "taskId" ; $taskId ; JSONNumber ] ; [ "beforeStatus" ; $beforeStatus ; JSONString ] ; [ "afterStatus" ; $newStatus ; JSONString ] ; [ "version" ; $expectedVersion + 1 ; JSONNumber ] ; [ "replayed" ; False ; JSONBoolean ] ) ; "" ; "" ; "" ; "update-record" )` ]
85. `Set Field` [ `SYN_TASK__by_id::SYN_Status` ; `$newStatus` ]
86. `Set Variable` [ `$fieldError` ; Value: `Get ( LastError )` ]
87. `If` [ `$fieldError ≠ 0` ]
88. `Revert Record/Request` [ With dialog: Off ]
89. `Set Variable` [ `$revertError` ; Value: `Get ( LastError )` ]
90. `Exit Script` [ Result: `If ( $revertError ≠ 0 ; SYN_Result ( False ; "CLEANUP_FAILED" ; "The failed status update could not be reverted." ; "null" ; $revertError ; "Revert Record/Request" ; "" ; "update-record" ) ; SYN_Result ( False ; "FIELD_ASSIGNMENT_FAILED" ; "The status field could not be set." ; "null" ; $fieldError ; "Set Field" ; "" ; "update-record" ) )` ]
91. `End If`
92. `Set Field` [ `SYN_TASK__by_id::SYN_Version` ; `$expectedVersion + 1` ]
93. `Set Variable` [ `$fieldError` ; Value: `Get ( LastError )` ]
94. `If` [ `$fieldError ≠ 0` ]
95. `Revert Record/Request` [ With dialog: Off ]
96. `Set Variable` [ `$revertError` ; Value: `Get ( LastError )` ]
97. `Exit Script` [ Result: `If ( $revertError ≠ 0 ; SYN_Result ( False ; "CLEANUP_FAILED" ; "The failed version update could not be reverted." ; "null" ; $revertError ; "Revert Record/Request" ; "" ; "update-record" ) ; SYN_Result ( False ; "FIELD_ASSIGNMENT_FAILED" ; "The version field could not be set." ; "null" ; $fieldError ; "Set Field" ; "" ; "update-record" ) )` ]
98. `End If`
99. `Set Field` [ `SYN_TASK__by_id::SYN_LastRequestId` ; `$requestId` ]
100. `Set Variable` [ `$fieldError` ; Value: `Get ( LastError )` ]
101. `If` [ `$fieldError ≠ 0` ]
102. `Revert Record/Request` [ With dialog: Off ]
103. `Set Variable` [ `$revertError` ; Value: `Get ( LastError )` ]
104. `Exit Script` [ Result: `If ( $revertError ≠ 0 ; SYN_Result ( False ; "CLEANUP_FAILED" ; "The failed request ID update could not be reverted." ; "null" ; $revertError ; "Revert Record/Request" ; "" ; "update-record" ) ; SYN_Result ( False ; "FIELD_ASSIGNMENT_FAILED" ; "The request ID could not be stored." ; "null" ; $fieldError ; "Set Field" ; "" ; "update-record" ) )` ]
105. `End If`
106. `Set Field` [ `SYN_TASK__by_id::SYN_LastRequestJson` ; `$request` ]
107. `Set Variable` [ `$fieldError` ; Value: `Get ( LastError )` ]
108. `If` [ `$fieldError ≠ 0` ]
109. `Revert Record/Request` [ With dialog: Off ]
110. `Set Variable` [ `$revertError` ; Value: `Get ( LastError )` ]
111. `Exit Script` [ Result: `If ( $revertError ≠ 0 ; SYN_Result ( False ; "CLEANUP_FAILED" ; "The failed request snapshot could not be reverted." ; "null" ; $revertError ; "Revert Record/Request" ; "" ; "update-record" ) ; SYN_Result ( False ; "FIELD_ASSIGNMENT_FAILED" ; "The request snapshot could not be stored." ; "null" ; $fieldError ; "Set Field" ; "" ; "update-record" ) )` ]
112. `End If`
113. `Set Field` [ `SYN_TASK__by_id::SYN_LastResultJson` ; `$successResult` ]
114. `Set Variable` [ `$fieldError` ; Value: `Get ( LastError )` ]
115. `If` [ `$fieldError ≠ 0` ]
116. `Revert Record/Request` [ With dialog: Off ]
117. `Set Variable` [ `$revertError` ; Value: `Get ( LastError )` ]
118. `Exit Script` [ Result: `If ( $revertError ≠ 0 ; SYN_Result ( False ; "CLEANUP_FAILED" ; "The failed result snapshot could not be reverted." ; "null" ; $revertError ; "Revert Record/Request" ; "" ; "update-record" ) ; SYN_Result ( False ; "FIELD_ASSIGNMENT_FAILED" ; "The result snapshot could not be stored." ; "null" ; $fieldError ; "Set Field" ; "" ; "update-record" ) )` ]
119. `End If`
120. `Commit Records/Requests` [ With dialog: Off ]
121. `Set Variable` [ `$commitError` ; Value: `Get ( LastError )` ]
122. `If` [ `$commitError = 0` ]
123. `Exit Script` [ Result: `$successResult` ]
124. `Else`
125. `Revert Record/Request` [ With dialog: Off ]
126. `Set Variable` [ `$revertError` ; Value: `Get ( LastError )` ]
127. `If` [ `$revertError ≠ 0` ]
128. `Exit Script` [ Result: `SYN_Result ( False ; "CLEANUP_FAILED" ; "The failed Commit could not be reverted." ; "null" ; $revertError ; "Revert Record/Request" ; "" ; "update-record" )` ]
129. `End If`
130. `If` [ `$commitError = 512` ]
131. `Set Variable` [ `$lastRetryError` ; Value: `$commitError` ]
132. `Set Variable` [ `$lastRetryStep` ; Value: `"Commit Records/Requests"` ]
133. `Exit Loop If` [ `$attempt ≥ 2` ]
134. `Else`
135. `Exit Script` [ Result: `SYN_Result ( False ; "COMMIT_FAILED" ; "The task update could not be committed." ; "null" ; $commitError ; "Commit Records/Requests" ; "" ; "update-record" )` ]
136. `End If`
137. `End If`
138. `End If`
139. `End Loop`
140. `Exit Script` [ Result: `SYN_Result ( False ; "RETRY_EXHAUSTED" ; "The update remained locked or conflicted after two attempts." ; JSONSetElement ( "{}" ; [ "attempts" ; $attempt ; JSONNumber ] ) ; $lastRetryError ; $lastRetryStep ; "" ; "update-record" )` ]

## Error branches

| Application code | Trigger | Action |
| --- | --- | --- |
| `INVALID_JSON`／validation code | helperがrequestまたはresultを拒否 | raw documentを返さず終了 |
| `VALIDATION_HELPER_FAILED` | helper scriptの呼出しerror | call errorを保持し、inputを未検証のまま使用しない |
| `PSOS_CALL_FAILED` | caller-side PSOS error | server business successを推測せず終了 |
| `INVALID_SERVER_RESULT` | server resultが共通contract外 | invalid resultとして終了 |
| `CONTEXT_SETUP_FAILED` | `Go to Layout` error | findへ進まず、layout errorを保持して終了 |
| `FIND_MODE_FAILED` | `Enter Find Mode` error | criteriaを設定せず、mode errorを保持して終了 |
| `FIND_CRITERIA_FAILED` | find条件用`Set Field` error | findを実行せず、field errorを保持して終了 |
| `RECORD_NOT_FOUND` | error 401または0件 | updateせず終了 |
| `PRIMARY_KEY_NOT_UNIQUE` | 2件以上 | 任意recordを選ばず終了 |
| `FIND_FAILED` | 401以外のfind errorまたはexactly-one判定失敗 | updateせず、find errorを保持して終了 |
| `PRIVILEGE_DENIED`／`OPEN_FAILED` | non-retryableな`Open Record/Request` error | writeせず、error 200／201／202はprivilege failureとして分離 |
| `DUPLICATE_REQUEST` | 同じrequest IDが異なる正規化済みrequestで再利用された | writeせずcallerにrequest ID再利用を訂正させる |
| `OPTIMISTIC_LOCK_CONFLICT` | current versionが`expectedVersion`と不一致 | retryせずcallerにreloadを要求 |
| `FIELD_ASSIGNMENT_FAILED` | `Set Field` error | Revert結果を確認して終了 |
| `COMMIT_FAILED` | non-retryable Commit error | Revert結果を確認して終了 |
| `RETRY_EXHAUSTED` | open error 301／302またはCommit error 512が2回 | 最後のerrorとstepを保持し、追加retryを行わず終了 |
| `CLEANUP_FAILED` | Revert error | original operationをsuccess扱いせず人間確認 |

open error 301／302とCommit error 512は返却application codeではなく内部retry条件です。1回目は全contextを再構築し、2回目にも継続した場合だけ`RETRY_EXHAUSTED`を返します。numeric errorの分類は既存[`update-record/pattern.json`](../../../patterns/fm19.5/update-record/pattern.json)と登録済み`claris-fm19-error-codes`のFileMaker Pro 19 archive boundaryを継承し、FileMaker 19.5実機結果を保証しません。

## Commit／Revert design

5 fieldのassignment直後にerrorを確認し、すべてzeroの場合だけCommitします。Commit直後のerrorがzeroの場合だけ`UPDATED`です。assignmentまたはCommit failureではWith dialog OffでRevertし、その直後のerrorも確認します。Revert failureは`CLEANUP_FAILED`です。

## Lock／conflict design

primary-key findの後に`Open Record/Request`を実行します。open lockはsuccess扱いしません。recordを開いた状態でduplicate requestとrequest ID再利用を確認し、その後に`SYN_Version = expectedVersion`を再確認します。Commit conflictもopen lockと別に分類します。

## Retry／idempotency design

- retry対象: open error 301／302、Commit error 512
- maximum attempts: 2
- 各attempt: layout移動、find、idempotency check、open、version checkを最初からやり直す
- backoff: 採用しない
- exhaustion: `RETRY_EXHAUSTED`
- idempotency: `SYN_LastRequestId = requestId`かつ保存済みrequestが一致すればwriteせず、保存済みsuccess resultの`data.replayed`だけをtrueにして返す。requestが不一致なら`DUPLICATE_REQUEST`とする
- version: `SYN_Version`を`expectedVersion + 1`へ更新し、stale requestを拒否する

## Security considerations

- JSONへcredentialを含めない。
- raw input、before／afterの未承認field、privilege detailをresultまたはlogへ含めない。
- callerへ返すdataはtask ID、status、version、replayedだけに限定する。
- 保存するrequest／result snapshotも承認済みcontractのkeyだけとし、credentialまたは追加のsensitive fieldを含めない。
- objectはexact synthetic nameで参照し、internal IDを埋めない。
- delete、create、bulk updateは実行しない。

## Human test cases

| Case | Context | Synthetic setup／input | Expected |
| --- | --- | --- | --- |
| normal | `client`→`psos` | 初期recordと上記input | `UPDATED`、status `SYN_done`、version 8、request ID保存 |
| malformed input | `client` | malformed JSON | helperの`INVALID_JSON`、PSOS未実行 |
| not found | `psos` | `taskId = 9999` | `RECORD_NOT_FOUND`、writeなし |
| duplicate primary key | `psos` | 合成testでID 1001を2件作る | `PRIMARY_KEY_NOT_UNIQUE`、writeなし |
| target layout missing／unavailable | `psos` | test copyで`SYN_Task_Server`を削除、rename、または利用不可にする | `CONTEXT_SETUP_FAILED`、find／writeなし |
| Enter Find Mode failure | `psos` | test copyで`Enter Find Mode` failureを発生させる | `FIND_MODE_FAILED`、criteria／writeなし |
| find criterion assignment failure | `psos` | test copyで`SYN_TaskId`を設定不可にする | `FIND_CRITERIA_FAILED`、find／writeなし |
| record lock then success | `psos` | attempt 1だけopen error 301または302、attempt 2でlock解放 | attempt 2で`UPDATED` |
| record lock exhaustion | `psos` | open error 301または302が2 attempt継続 | `RETRY_EXHAUSTED`、最後のerrorと`Open Record/Request`を保持 |
| stale version | `psos` | current version 8、expected 7 | `OPTIMISTIC_LOCK_CONFLICT` |
| duplicate request | `psos` | `SYN_LastRequestId = "SYN_REQ_0001"`かつ保存requestが同一 | 保存済み`UPDATED`、`replayed = true`、追加writeなし |
| request ID reuse | `psos` | 同じrequest ID、異なる`newStatus` | `DUPLICATE_REQUEST`、writeなし |
| privilege | `psos` | edit privilegeなしの合成privilege copy | `PRIVILEGE_DENIED`、sensitive detailなし |
| Commit 512 then success | `psos` | attempt 1だけCommit error 512、Revert成功、version条件を維持してattempt 2はCommit成功 | attempt 2で`UPDATED` |
| Commit 512 exhaustion | `psos` | Commit error 512が2 attempt継続し、各Revertは成功 | `RETRY_EXHAUSTED`、最後のerrorと`Commit Records/Requests`を保持 |
| non-retryable Commit failure | `psos` | 512以外のCommit errorを発生 | `COMMIT_FAILED`、Revert resultを確認 |
| invalid server result | `client` | server test doubleがcontract外result | `INVALID_SERVER_RESULT` |

これらは将来実機で実施するtest designであり、実行済みresultではありません。

## Compatibility ledger

| Step | Context | Catalog support | Resolved condition |
| --- | --- | --- | --- |
| Set Error Capture | client | available | — |
| Set Variable | client | available | — |
| Perform Script | client | available | — |
| Perform Script on Server | client | available | — |
| If | client | available | — |
| End If | client | available | — |
| Exit Script | client | available | — |
| Set Error Capture | psos | partial | FMSEは常にOnとして動作するため、設計はOff状態へ依存しない。 |
| Set Variable | psos | available | — |
| Perform Script | psos | available | — |
| If | psos | available | — |
| Else | psos | available | — |
| End If | psos | available | — |
| Exit Script | psos | available | — |
| Loop | psos | available | — |
| Exit Loop If | psos | available | — |
| End Loop | psos | available | — |
| Go to Layout | psos | partial | `SYN_Task_Server`を明示し、AnimationはNone。client contextを継承しない。 |
| Enter Find Mode | psos | partial | PauseはOff。interactive inputを要求しない。 |
| Set Field | psos | available | — |
| Perform Find | psos | available | — |
| Open Record/Request | psos | available | — |
| Commit Records/Requests | psos | partial | With dialogはOff。validationと直後のerrorを明示的に確認する。 |
| Revert Record/Request | psos | partial | With dialogはOff。current recordの未Commit変更だけをreview済みbranchで破棄する。 |

renderer statusはこのledgerのsupportとは別です。この表はXML生成可能性を表しません。

## Verification status

```text
Design status: implementation_ready
XML output: not_requested
Automated checks: not_run
Paste verification: not_run
Client runtime verification: not_run
FMSE verification: not_run
```

`implementation_ready`は、この完全合成contextに対して手作業実装情報が揃っていることだけを意味します。FileMaker runtime evidenceではありません。
