# Script IR

Script IRは、FileMaker Server / Pro 19.5向けスクリプト設計と、現在対応する7種類のXMLステップを結ぶJSON中間表現です。v2は設計情報を明示し、未知のプロパティ、矛盾した変数、無効なステップ、捏造されたオブジェクトIDをfail closedで扱います。

## スキーマ

- `schemas/script-ir-v1.schema.json`: 初期版の最小IRを固定保存
- `schemas/script-ir-v2.schema.json`: 現在の厳格なIR
- `schemas/script-ir.schema.json`: 現行版としてv2を参照する入口

すべてJSON Schema Draft 2020-12です。CLIは`jsonschema>=4.23,<5`で構造検証し、その後に重複や参照整合などの意味検証を行います。

## v2のトップレベル

```json
{
  "schemaVersion": 2,
  "target": {},
  "script": {},
  "context": {},
  "variables": [],
  "objectReferences": [],
  "steps": [],
  "unresolvedIssues": [],
  "risks": [],
  "status": {}
}
```

各オブジェクトは、埋め込みJSON Schemaである契約の`schema`を除き、未知のプロパティを拒否します。

## 対象と実行環境

```json
{
  "serverVersion": "19.5",
  "proVersion": "19.5",
  "execution": "client",
  "platform": "windows"
}
```

通常のv2設計では`execution`を`client`、`psos`、`server_schedule`から選びます。`serverVersion`と`proVersion`は`19.5`、`platform`は`windows`以外を受け付けません。`script.execution`にも同じ値を記載し、`target.execution`との一致を検査します。

v1には実行モードが存在しません。移行時だけ`execution: "unspecified"`を使用し、`migration.fromSchemaVersion: 1`と`target_execution`の未解決事項を必須にします。これはクライアント、PSOS、スケジュールのいずれかを推測しないための移行専用状態です。

## スクリプト情報とJSON契約

`script`は名前、目的、副作用、実行環境、入力契約、結果契約を持ちます。副作用は、明示済みの配列または未指定状態として表現します。入力と結果は`format: "json"`とDraft 2020-12のJSON Schemaで定義します。

```json
{
  "name": "SRV | Process Synthetic Request",
  "purpose": "Process a synthetic request.",
  "sideEffects": {
    "state": "specified",
    "items": [
      "Updates one synthetic record after validation."
    ]
  },
  "execution": "psos",
  "inputContract": {
    "format": "json",
    "description": "Synthetic request.",
    "schema": {
      "type": "object",
      "required": ["recordId"]
    }
  },
  "resultContract": {
    "format": "json",
    "description": "Synthetic result.",
    "schema": {
      "type": "object",
      "required": ["ok", "code"]
    }
  }
}
```

契約内の`schema`自体もDraft 2020-12として検査されます。

## FileMakerコンテキスト

コンテキストには3状態があります。

- `none`: レイアウトやレコードを使用しないことを明示する
- `required`: レイアウト、基準TO、対象レコード特定方法、対象集合の扱いを明示する
- `unspecified`: v1移行など、情報が存在しないことを明示する

`required`の例:

```json
{
  "mode": "required",
  "layoutRef": "layout.syntheticProcessing",
  "tableOccurrenceRef": "to.syntheticRecord",
  "recordIdentification": {
    "method": "script_parameter",
    "description": "Use the synthetic recordId from the JSON parameter."
  },
  "foundSet": {
    "handling": "rebuild",
    "description": "Rebuild the found set in the independent FMSE session."
  }
}
```

`layoutRef`は`layout`参照、`tableOccurrenceRef`は`tableOccurrence`参照を指す必要があります。存在しないキーや種別不一致は拒否されます。

## 変数

各変数は`name`、`scope`、`type`、`initialization`、`purpose`を持ちます。型は`text`、`number`、`boolean`、`date`、`time`、`timestamp`、`container`、`json`、`unknown`です。

- `$name`は`local`
- `$$name`は`global`
- 同じ名前の重複は禁止
- `set_variable`の対象は宣言済み変数に限る

初期化方法には計算式、リテラル、スクリプト引数、初回代入、初期化なし、未指定を表現できます。`first_assignment`はv1移行で、既存の最初の`set_variable`計算式をそのまま記録するために使用します。

## FileMakerオブジェクト参照

対応種別は`field`、`layout`、`tableOccurrence`、`script`、`valueList`です。

解決済み:

```json
{
  "key": "layout.syntheticProcessing",
  "type": "layout",
  "name": "Synthetic Processing",
  "internalId": 1001,
  "resolution": "resolved"
}
```

未解決:

```json
{
  "key": "field.syntheticStatus",
  "type": "field",
  "name": "SyntheticRecord::Status",
  "resolution": "unresolved"
}
```

参照キーはIR内で一意です。`resolved`は`internalId`が必須で、`unresolved`は`internalId`を設定できません。移行処理は参照やIDを生成しません。`validate-ir`は未解決参照を正直な設計状態として受理しますが、`render`は未解決参照が1件でもあればXMLを書き出しません。

## ステップ

現在の7種類は、各分岐が`additionalProperties: false`のdiscriminated unionです。

| `type` | 固有の必須プロパティ |
| --- | --- |
| `comment` | `text` |
| `set_error_capture` | `state` |
| `set_variable` | `name`, `calculation`, `repetition` |
| `if` | `calculation` |
| `else` | なし |
| `end_if` | なし |
| `exit_script` | `calculation` |

すべてのステップで`enabled`は省略可能で、省略時は従来どおり有効としてレンダリングされます。別種類のプロパティ、未知の種類、閉じていない`if`、不正な`else`を拒否します。XMLテンプレート、ステップ名、数値IDは既存カタログのままです。

## 未解決事項、リスク、状態

`unresolvedIssues`は一意なキー、カテゴリ、説明、XML生成を止めるかどうかを持ちます。ネイティブv2で`blocking: true`の事項が残る場合、`render`は停止します。v1互換レンダリングだけは、移行由来であることを明示した未解決メタデータを保持したまま、従来のオブジェクト非依存7ステップを生成します。

`status.design`は`draft`、`ready`、`blocked`、`status.evidence`は`unverified`、`design_ready`、`xml_generated`、`paste_verified`、`runtime_verified`、`fmse_verified`です。未解決参照またはblocking事項がある設計は`ready`にできず、証拠状態は`unverified`でなければなりません。`unverified`を超える証拠状態には`ready`な設計が必要です。CI成功は`paste_verified`以降の証拠へ昇格させません。

## CLI

```powershell
fms19 validate-ir examples/server-script-ir-v2.json
fms19 migrate-ir examples/server-script-ir.json migrated-ir-v2.json
fms19 render examples/server-script-ir.json generated-v1.xml
fms19 render examples/server-script-ir-v2.json generated-v2.xml
```

`validate-ir`と`render`はv1/v2を自動判定します。`migrate-ir`はv1だけを受け付け、同じ入力から常に同じUTF-8・LF・末尾改行付きJSONを生成します。

完全な合成例は`examples/server-script-ir-v2.json`を参照してください。
