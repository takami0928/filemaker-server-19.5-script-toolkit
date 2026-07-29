# SYN_Task status update through synchronous PSOS

この設計は完全な合成例です。名称、値、requirement、privilegeは実在環境を表しません。FileMaker Pro／Server 19.5でpasteまたはruntime testを行っていません。

## Synthetic internal context

| Type | Synthetic fact |
| --- | --- |
| File | `SYN_Operations`。FileMaker Server 19.5へhostされる想定。 |
| Table | `SYN_Task` |
| TO | `SYN_TASK__by_id`。base tableは`SYN_Task`。 |
| Layout | `SYN_Task_Server`。base TOは`SYN_TASK__by_id`。server処理専用で、animationやdialogを使用しない。 |
| Caller script | `SYN_UI_RequestTaskUpdate` |
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

## Script name

- `SYN_UI_RequestTaskUpdate`
- `SYN_SRV_UpdateTask`

## Purpose

- `SYN_UI_RequestTaskUpdate`: validated requestを同期PSOSへ渡し、call failureとserver business resultを分離してcallerへ返す。
- `SYN_SRV_UpdateTask`: 1件の`SYN_Task`をidempotentかつoptimistic version付きで更新し、Commit結果を返す。

## Execution context

- caller: `client`
- server target: `psos`

## Caller

`SYN_UI_RequestTaskUpdate`は、別の合成UI controllerからversion付きJSON parameterで呼ばれます。callerは`SYN_SRV_UpdateTask`を`Perform Script on Server`のWait for completion Onで呼びます。server scriptは独立sessionとして全contextを再構築します。

## Preconditions

- `SYN_Operations`がFileMaker Server 19.5へhostされている。
- `SYN_Task_Server`のbase TOが`SYN_TASK__by_id`である。
- `SYN_SYS_ValidateJsonContract`、`SYN_Result`、2つのcontractが上記どおり存在する。
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
| existing script | `SYN_SYS_ValidateJsonContract` | request／result validation |
| existing custom function | `SYN_Result` | 共通result生成 |

internal object IDは使用しません。

## Privilege requirements

`SYN_Automation`は次を持ちます。

- 3 scriptのexecute権限
- `SYN_Task`のrecord read／edit権限
- 6 fieldのview権限と、`SYN_Status`、`SYN_Version`、`SYN_LastRequestId`、`SYN_LastRequestJson`、`SYN_LastResultJson`のedit権限
- `SYN_Task_Server`を使用するために必要なaccess

delete、create、schema変更、credential参照の権限は不要です。

## Variables

| Variable | Calculation／initial value | Purpose |
| --- | --- | --- |
| `$rawInput` | `Get ( ScriptParameter )` | caller／serverのraw parameter |
| `$validationRequest` | helper用`contractName`＋`document` JSON | validation input |
| `$helperError` | helper `Perform Script`直後の`Get ( LastError )` | helper call error |
| `$validationResult` | `Get ( ScriptResult )` | helper result |
| `$request` | validated `data.document` | PSOS parameter |
| `$callError` | PSOS直後の`Get ( LastError )` | call-level error |
| `$serverResult` | PSOS直後の`Get ( ScriptResult )` | server business result |
| `$taskId` | validated `payload.taskId` | primary key |
| `$newStatus` | validated `payload.newStatus` | new value |
| `$expectedVersion` | validated `payload.expectedVersion` | optimistic check |
| `$requestId` | validated `requestId` | idempotency |
| `$attempt` | `0`からincrement | 最大2回のretry |
| `$lastRetryError` | emptyから開始 | exhaustion時に保持する最後のretryable error |
| `$lastRetryStep` | emptyから開始 | exhaustion時に保持するstep |
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
3. `Set Variable` [ `$validationRequest` ; Value: `JSONSetElement`で`contractName = "SYN_TaskUpdateRequest_v1"`と`document = $rawInput`を設定 ]
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
21. `Set Variable` [ `$validationRequest` ; Value: `JSONSetElement`で`contractName = "SYN_CommonResult_v1"`と`document = $serverResult`を設定 ]
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

1. `Set Error Capture` [ On。FMSEのOn動作に合わせ、Offへ切り替えない ]
2. `Set Variable` [ `$rawInput` ; Value: `Get ( ScriptParameter )` ]
3. `Set Variable` [ `$validationRequest` ; Value: `contractName = "SYN_TaskUpdateRequest_v1"`と`document = $rawInput` ]
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
23. `Go to Layout` [ `SYN_Task_Server` ; Animation: None ]
24. `Enter Find Mode` [ Pause: Off ]
25. `Set Field` [ `SYN_TASK__by_id::SYN_TaskId` ; `$taskId` ]
26. `Perform Find`
27. `Set Variable` [ `$findError` ; Value: `Get ( LastError )` ]
28. `Set Variable` [ `$foundCount` ; Value: `Get ( FoundCount )` ]
29. `If` [ `$findError = 401 or $foundCount = 0` ]
30. `Exit Script` [ Result: `SYN_Result ( False ; "RECORD_NOT_FOUND" ; "No matching task was found." ; "null" ; If ( $findError = 0 ; "" ; $findError ) ; "Perform Find" ; "" ; "update-record" )` ]
31. `End If`
32. `If` [ `$findError ≠ 0 or $foundCount ≠ 1` ]
33. `Exit Script` [ Result: `SYN_Result ( False ; If ( $foundCount > 1 ; "PRIMARY_KEY_NOT_UNIQUE" ; "FIND_FAILED" ) ; "The primary-key find did not resolve exactly one task." ; "null" ; If ( $findError = 0 ; "" ; $findError ) ; "Perform Find" ; "" ; "update-record" )` ]
34. `End If`
35. `Open Record/Request`
36. `Set Variable` [ `$openError` ; Value: `Get ( LastError )` ]
37. `If` [ `$openError = 301 or $openError = 302` ]
38. `Set Variable` [ `$lastRetryError` ; Value: `$openError` ]
39. `Set Variable` [ `$lastRetryStep` ; Value: `"Open Record/Request"` ]
40. `Exit Loop If` [ `$attempt ≥ 2` ]
41. `Else`
42. `If` [ `$openError ≠ 0` ]
43. `Exit Script` [ Result: `SYN_Result ( False ; If ( $openError = 200 or $openError = 201 or $openError = 202 ; "PRIVILEGE_DENIED" ; "OPEN_FAILED" ) ; "The task could not be opened for update." ; "null" ; $openError ; "Open Record/Request" ; "" ; "update-record" )` ]
44. `End If`
45. `If` [ `SYN_TASK__by_id::SYN_LastRequestId = $requestId` ]
46. `If` [ `SYN_TASK__by_id::SYN_LastRequestJson ≠ $request` ]
47. `Revert Record/Request` [ With dialog: Off ]
48. `Set Variable` [ `$revertError` ; Value: `Get ( LastError )` ]
49. `If` [ `$revertError ≠ 0` ]
50. `Exit Script` [ Result: `SYN_Result ( False ; "CLEANUP_FAILED" ; "The duplicate-request check could not release the record." ; "null" ; $revertError ; "Revert Record/Request" ; "" ; "update-record" )` ]
51. `End If`
52. `Exit Script` [ Result: `SYN_Result ( False ; "DUPLICATE_REQUEST" ; "The request ID was reused with different input." ; "null" ; "" ; "SYN_LastRequestJson" ; "" ; "perform-script-on-server" )` ]
53. `Else`
54. `Set Variable` [ `$replayResult` ; Value: `JSONSetElement ( SYN_TASK__by_id::SYN_LastResultJson ; "data.replayed" ; True ; JSONBoolean )` ]
55. `Revert Record/Request` [ With dialog: Off ]
56. `Set Variable` [ `$revertError` ; Value: `Get ( LastError )` ]
57. `If` [ `$revertError ≠ 0` ]
58. `Exit Script` [ Result: `SYN_Result ( False ; "CLEANUP_FAILED" ; "The duplicate request result could not release the record." ; "null" ; $revertError ; "Revert Record/Request" ; "" ; "update-record" )` ]
59. `End If`
60. `Exit Script` [ Result: `$replayResult` ]
61. `End If`
62. `End If`
63. `If` [ `SYN_TASK__by_id::SYN_Version ≠ $expectedVersion` ]
64. `Revert Record/Request` [ With dialog: Off ]
65. `Set Variable` [ `$revertError` ; Value: `Get ( LastError )` ]
66. `If` [ `$revertError ≠ 0` ]
67. `Exit Script` [ Result: `SYN_Result ( False ; "CLEANUP_FAILED" ; "The version-conflict branch could not release the record." ; "null" ; $revertError ; "Revert Record/Request" ; "" ; "update-record" )` ]
68. `End If`
69. `Exit Script` [ Result: `SYN_Result ( False ; "OPTIMISTIC_LOCK_CONFLICT" ; "The task version changed." ; "null" ; "" ; "SYN_Version" ; "" ; "update-record" )` ]
70. `End If`
71. `Set Variable` [ `$beforeStatus` ; Value: `SYN_TASK__by_id::SYN_Status` ]
72. `Set Variable` [ `$successResult` ; Value: `SYN_Result ( True ; "UPDATED" ; "" ; JSONSetElement ( "{}" ; [ "taskId" ; $taskId ; JSONNumber ] ; [ "beforeStatus" ; $beforeStatus ; JSONString ] ; [ "afterStatus" ; $newStatus ; JSONString ] ; [ "version" ; $expectedVersion + 1 ; JSONNumber ] ; [ "replayed" ; False ; JSONBoolean ] ) ; "" ; "" ; "" ; "update-record" )` ]
73. `Set Field` [ `SYN_TASK__by_id::SYN_Status` ; `$newStatus` ]
74. `Set Variable` [ `$fieldError` ; Value: `Get ( LastError )` ]
75. `If` [ `$fieldError ≠ 0` ]
76. `Revert Record/Request` [ With dialog: Off ]
77. `Set Variable` [ `$revertError` ; Value: `Get ( LastError )` ]
78. `Exit Script` [ Result: `If ( $revertError ≠ 0 ; SYN_Result ( False ; "CLEANUP_FAILED" ; "The failed status update could not be reverted." ; "null" ; $revertError ; "Revert Record/Request" ; "" ; "update-record" ) ; SYN_Result ( False ; "FIELD_ASSIGNMENT_FAILED" ; "The status field could not be set." ; "null" ; $fieldError ; "Set Field" ; "" ; "update-record" ) )` ]
79. `End If`
80. `Set Field` [ `SYN_TASK__by_id::SYN_Version` ; `$expectedVersion + 1` ]
81. `Set Variable` [ `$fieldError` ; Value: `Get ( LastError )` ]
82. `If` [ `$fieldError ≠ 0` ]
83. `Revert Record/Request` [ With dialog: Off ]
84. `Set Variable` [ `$revertError` ; Value: `Get ( LastError )` ]
85. `Exit Script` [ Result: `If ( $revertError ≠ 0 ; SYN_Result ( False ; "CLEANUP_FAILED" ; "The failed version update could not be reverted." ; "null" ; $revertError ; "Revert Record/Request" ; "" ; "update-record" ) ; SYN_Result ( False ; "FIELD_ASSIGNMENT_FAILED" ; "The version field could not be set." ; "null" ; $fieldError ; "Set Field" ; "" ; "update-record" ) )` ]
86. `End If`
87. `Set Field` [ `SYN_TASK__by_id::SYN_LastRequestId` ; `$requestId` ]
88. `Set Variable` [ `$fieldError` ; Value: `Get ( LastError )` ]
89. `If` [ `$fieldError ≠ 0` ]
90. `Revert Record/Request` [ With dialog: Off ]
91. `Set Variable` [ `$revertError` ; Value: `Get ( LastError )` ]
92. `Exit Script` [ Result: `If ( $revertError ≠ 0 ; SYN_Result ( False ; "CLEANUP_FAILED" ; "The failed request ID update could not be reverted." ; "null" ; $revertError ; "Revert Record/Request" ; "" ; "update-record" ) ; SYN_Result ( False ; "FIELD_ASSIGNMENT_FAILED" ; "The request ID could not be stored." ; "null" ; $fieldError ; "Set Field" ; "" ; "update-record" ) )` ]
93. `End If`
94. `Set Field` [ `SYN_TASK__by_id::SYN_LastRequestJson` ; `$request` ]
95. `Set Variable` [ `$fieldError` ; Value: `Get ( LastError )` ]
96. `If` [ `$fieldError ≠ 0` ]
97. `Revert Record/Request` [ With dialog: Off ]
98. `Set Variable` [ `$revertError` ; Value: `Get ( LastError )` ]
99. `Exit Script` [ Result: `If ( $revertError ≠ 0 ; SYN_Result ( False ; "CLEANUP_FAILED" ; "The failed request snapshot could not be reverted." ; "null" ; $revertError ; "Revert Record/Request" ; "" ; "update-record" ) ; SYN_Result ( False ; "FIELD_ASSIGNMENT_FAILED" ; "The request snapshot could not be stored." ; "null" ; $fieldError ; "Set Field" ; "" ; "update-record" ) )` ]
100. `End If`
101. `Set Field` [ `SYN_TASK__by_id::SYN_LastResultJson` ; `$successResult` ]
102. `Set Variable` [ `$fieldError` ; Value: `Get ( LastError )` ]
103. `If` [ `$fieldError ≠ 0` ]
104. `Revert Record/Request` [ With dialog: Off ]
105. `Set Variable` [ `$revertError` ; Value: `Get ( LastError )` ]
106. `Exit Script` [ Result: `If ( $revertError ≠ 0 ; SYN_Result ( False ; "CLEANUP_FAILED" ; "The failed result snapshot could not be reverted." ; "null" ; $revertError ; "Revert Record/Request" ; "" ; "update-record" ) ; SYN_Result ( False ; "FIELD_ASSIGNMENT_FAILED" ; "The result snapshot could not be stored." ; "null" ; $fieldError ; "Set Field" ; "" ; "update-record" ) )` ]
107. `End If`
108. `Commit Records/Requests` [ With dialog: Off ]
109. `Set Variable` [ `$commitError` ; Value: `Get ( LastError )` ]
110. `If` [ `$commitError = 0` ]
111. `Exit Script` [ Result: `$successResult` ]
112. `Else`
113. `Revert Record/Request` [ With dialog: Off ]
114. `Set Variable` [ `$revertError` ; Value: `Get ( LastError )` ]
115. `If` [ `$revertError ≠ 0` ]
116. `Exit Script` [ Result: `SYN_Result ( False ; "CLEANUP_FAILED" ; "The failed Commit could not be reverted." ; "null" ; $revertError ; "Revert Record/Request" ; "" ; "update-record" )` ]
117. `End If`
118. `If` [ `$commitError = 512` ]
119. `Set Variable` [ `$lastRetryError` ; Value: `$commitError` ]
120. `Set Variable` [ `$lastRetryStep` ; Value: `"Commit Records/Requests"` ]
121. `Exit Loop If` [ `$attempt ≥ 2` ]
122. `Else`
123. `Exit Script` [ Result: `SYN_Result ( False ; "COMMIT_FAILED" ; "The task update could not be committed." ; "null" ; $commitError ; "Commit Records/Requests" ; "" ; "update-record" )` ]
124. `End If`
125. `End If`
126. `End If`
127. `End Loop`
128. `Exit Script` [ Result: `SYN_Result ( False ; "RETRY_EXHAUSTED" ; "The update remained locked or conflicted after two attempts." ; JSONSetElement ( "{}" ; [ "attempts" ; $attempt ; JSONNumber ] ) ; $lastRetryError ; $lastRetryStep ; "" ; "update-record" )` ]

## Error branches

| Application code | Trigger | Action |
| --- | --- | --- |
| `INVALID_JSON`／validation code | helperがrequestまたはresultを拒否 | raw documentを返さず終了 |
| `VALIDATION_HELPER_FAILED` | helper scriptの呼出しerror | call errorを保持し、inputを未検証のまま使用しない |
| `PSOS_CALL_FAILED` | caller-side PSOS error | server business successを推測せず終了 |
| `INVALID_SERVER_RESULT` | server resultが共通contract外 | invalid resultとして終了 |
| `RECORD_NOT_FOUND` | error 401または0件 | updateせず終了 |
| `PRIMARY_KEY_NOT_UNIQUE` | 2件以上 | 任意recordを選ばず終了 |
| `RECORD_LOCKED` | open error 301／302 | 全contextを再構築し最大2 attempt |
| `DUPLICATE_REQUEST` | 同じrequest IDが異なる正規化済みrequestで再利用された | writeせずcallerにrequest ID再利用を訂正させる |
| `OPTIMISTIC_LOCK_CONFLICT` | current versionが`expectedVersion`と不一致 | retryせずcallerにreloadを要求 |
| `FIELD_ASSIGNMENT_FAILED` | `Set Field` error | Revert結果を確認して終了 |
| `COMMIT_FAILED` | non-retryable Commit error | Revert結果を確認して終了 |
| `RETRY_EXHAUSTED` | open error 301／302またはCommit error 512が2回 | 最後のerrorとstepを保持し、追加retryを行わず終了 |
| `CLEANUP_FAILED` | Revert error | original operationをsuccess扱いせず人間確認 |

numeric errorの分類は既存[`update-record/pattern.json`](../../../patterns/fm19.5/update-record/pattern.json)のsource-backed candidate boundaryを継承し、FileMaker 19.5実機結果を保証しません。

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
| record lock | `psos` | 別sessionがrecordをopen | 2 attempt後`RETRY_EXHAUSTED` |
| stale version | `psos` | current version 8、expected 7 | `OPTIMISTIC_LOCK_CONFLICT` |
| duplicate request | `psos` | `SYN_LastRequestId = "SYN_REQ_0001"`かつ保存requestが同一 | 保存済み`UPDATED`、`replayed = true`、追加writeなし |
| request ID reuse | `psos` | 同じrequest ID、異なる`newStatus` | `DUPLICATE_REQUEST`、writeなし |
| privilege | `psos` | edit privilegeなしの合成privilege copy | `PRIVILEGE_DENIED`、sensitive detailなし |
| Commit failure | `psos` | 合成validation failureを発生 | non-success result、Revert resultを確認 |
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
