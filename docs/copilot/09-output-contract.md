# 設計書output contract

Copilotは、次の24 sectionをこの順序で出力します。値を不明なまま`TBD`で隠さず、section 9または10へ分類します。

1. Design status
2. Script name
3. Purpose
4. Execution context
5. Caller
6. Preconditions
7. Confirmed facts
8. Assumptions
9. Unresolved required information
10. Unresolved optional information
11. Explicitly omitted optional features
12. Input JSON contract
13. Result JSON contract
14. Required FileMaker objects
15. Privilege requirements
16. Variables
17. FileMaker-format script steps
18. Error branches
19. Commit／Revert design
20. Lock／conflict design
21. Retry／idempotency design
22. Security considerations
23. Human test cases
24. Verification status

## 状態規則

- required情報が不足する場合は`draft_design`とする。
- optional情報だけが不足する場合、一律に`draft_design`へ戻さない。採用しない機能と影響をsection 11へ記録する。
- `implementation_ready`は、採用範囲を手作業実装できる情報が揃った設計状態であり、runtime verifiedを意味しない。
- XMLを依頼されていない場合は`XML output: not_requested`とする。
- 実機試験を行っていないverificationは`not_run`とする。
- internal IDを生成・推測しない。

## Script stepの粒度

section 17は、FileMaker担当者が上から順に実装できる粒度で記載します。各stepにexact English step name、option、calculation、target object、branch conditionを併記します。各execution contextのcompatibilityを確認し、`partial`の解決条件も示します。

## 完全template

次をcopyし、角括弧部分を確認済み情報で置換します。空欄がrequiredかoptionalかを必ず分類します。

````markdown
# [設計書名]

## 1. Design status

Design status: draft_design | implementation_ready

## 2. Script name

[exact script name]

## 3. Purpose

[one primary responsibility]

## 4. Execution context

[client | psos | server_schedule | webdirect | filemaker_go | data_api | custom_web_publishing]

## 5. Caller

[exact caller and trigger]

## 6. Preconditions

- [precondition]

## 7. Confirmed facts

- [fact and source]

## 8. Assumptions

- [assumption; noneの場合は「なし」]

## 9. Unresolved required information

- [blocking item; noneの場合は「なし」]

## 10. Unresolved optional information

- [non-blocking item; noneの場合は「なし」]

## 11. Explicitly omitted optional features

- Feature: [name]
  - Effect of omission: [effect]
  - Future confirmation: [item]

## 12. Input JSON contract

```json
{}
```

## 13. Result JSON contract

`patterns/fm19.5/common-result.schema.json`に従う。

```json
{
  "ok": true,
  "code": "OK",
  "message": "",
  "data": {},
  "error": null,
  "meta": {
    "pattern": "json-parameter-validation",
    "schemaVersion": 1
  }
}
```

## 14. Required FileMaker objects

| Type | Exact name | Purpose／context |
| --- | --- | --- |
| file |  |  |
| table |  |  |
| TO |  |  |
| field |  |  |
| layout |  |  |
| script |  |  |

## 15. Privilege requirements

- [record, field, layout, script execution requirements]

## 16. Variables

| Variable | Initial value／calculation | Purpose |
| --- | --- | --- |
|  |  |  |

## 17. FileMaker-format script steps

### [exact script name] — [canonical context]

1. `Exact catalog step name` [exact options, calculation, target, branch]

## 18. Error branches

| Application code | Trigger | Preserved FileMaker error | Action／result |
| --- | --- | --- | --- |
|  |  |  |  |

## 19. Commit／Revert design

[Commit check, uncommitted state, Revert criteria and Revert failure]

## 20. Lock／conflict design

[open, lock, version and concurrent Commit behavior]

## 21. Retry／idempotency design

[retryable conditions, maximum attempts, duplicate prevention, exhaustion result]

## 22. Security considerations

- [privilege, sensitive input/result, logging and destructive-operation controls]

## 23. Human test cases

| Case | Context | Input／setup | Expected result |
| --- | --- | --- | --- |
|  |  |  |  |

## 24. Verification status

Design status: draft_design | implementation_ready
XML output: not_requested | not_generated | generated
Automated checks: not_run | passed | failed
Paste verification: not_run | passed | failed
Client runtime verification: not_run | passed | failed
FMSE verification: not_run | passed | failed
````

完成例は[synthetic complete design](examples/synthetic-complete-design.md)を参照します。
