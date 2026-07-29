# 必要なinternal context

Copilotは、対象システム情報を次の分類で受け取ります。事実、仮定、未解決事項を混在させません。

## Required for design selection

- business purpose
- caller
- execution timing
- expected side effects
- input／output requirements
- target context
- error requirements

この情報が不足してcontextまたは処理方式を選べない場合、選択可能な範囲だけを`draft_design`として示します。

## Required for implementation-ready

- file
- table
- TO
- field
- layout
- existing script
- privilege
- naming rule
- exact calculation
- exact step option

採用した設計をScript Workspaceへ実装するために必要な項目が未解決なら、`implementation_ready`と報告しません。

## Conditional／optional

- idempotency field
- version field
- auxiliary layout
- retry policy
- audit field
- recovery script

optional機能を採用した場合、その実装に必要な情報はrequiredへ変わります。採用しない場合は、何を省略したか、現在の設計への影響、将来追加時の確認事項を記録します。

## Prohibited assumptions

次を存在する事実として推測しません。

- object existence
- object name
- internal ID
- privilege
- field type
- relationship
- layout context
- current found set
- current record
- global value
- business rule

## 記録template

公開repositoryへ社内情報を記入した完成表を保存しません。対象system用の作業copyで次の形を埋めます。

| Classification | Item | Value／evidence | Design effect |
| --- | --- | --- | --- |
| confirmed fact |  |  |  |
| assumption |  |  |  |
| unresolved required information |  |  | `draft_design`のblocking理由 |
| unresolved optional information |  |  | 採用判断までの影響 |
| explicit omission |  |  | 省略する機能 |
| effect of omission |  |  | safety／operation上の影響 |
| future confirmation item |  |  | 将来採用時の確認事項 |

分類と停止条件の正本は[AI利用契約](../../AI_GUIDE.md#設計状態と停止条件)です。完成した設計書では[output contract](09-output-contract.md)の該当sectionへ転記します。
