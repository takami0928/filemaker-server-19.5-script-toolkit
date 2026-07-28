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

v1には実行モードが存在しません。移行文書だけが`execution: "unspecified"`を使用でき、`migration.fromSchemaVersion: 1`、blockingな`target_execution`未解決事項、`status: draft/unverified`を必須にします。これはクライアント、PSOS、スケジュールのいずれかを推測しないための保存用状態であり、XML生成を許可するマーカーではありません。

## スクリプト情報とJSON契約

`script`は名前、目的、副作用、実行環境、入力契約、結果契約を持ちます。ネイティブv2の副作用は`state: "specified"`と配列で明示します。`state: "unspecified"`はv1移行文書だけが使用でき、blockingな`script_metadata`未解決事項を必要とします。入力と結果は`format: "json"`とDraft 2020-12のJSON Schemaで定義します。

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
- `unspecified`: v1移行文書で情報が存在しないことを明示する

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

`layoutRef`は`layout`参照、`tableOccurrenceRef`は`tableOccurrence`参照を指す必要があります。存在しないキーや種別不一致は拒否されます。ネイティブv2は`unspecified`を使用できません。移行文書で使用する場合はblockingな`context`未解決事項と`draft/unverified`状態が必要です。

## 変数

各変数は`name`、`scope`、`type`、`initialization`、`purpose`を持ちます。ネイティブv2の型は`text`、`number`、`boolean`、`date`、`time`、`timestamp`、`container`、`json`です。`unknown`はv1移行文書だけが使用できます。

- `$name`は`local`
- `$$name`は`global`
- 同じ名前の重複は禁止
- `set_variable`の対象は宣言済み変数に限る

初期化方法には計算式、リテラル、スクリプト引数、初回代入、初期化なしを表現できます。`unspecified`はv1移行文書専用です。`unknown`型または`unspecified`初期化を持つ移行文書にはblockingな`variable`未解決事項が必要です。`first_assignment`はv1移行で、既存の最初の`set_variable`計算式をそのまま記録するために使用します。

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

`unresolvedIssues`は一意なキー、カテゴリ、説明、XML生成を止めるかどうかを持ちます。v2文書は`migration`の有無に関係なく、`blocking: true`の事項が1件でもあれば`render`を停止します。保存済みの移行v2も、人間が不足情報を補完し、未解決事項を解消するまではXMLを生成できません。

直接のv1入力に限り、`render_ir()`が移行前の入力をv1と判定した事実に基づく非公開の互換経路で、従来のオブジェクト非依存7ステップを生成します。この権限はIR内にシリアライズされず、`migration`マーカーや他の文書値では有効化できません。

`status.design`は`draft`、`ready`、`blocked`です。IR入力の`status.evidence`は`unverified`と`design_ready`だけを受け付けます。未解決参照、blocking事項、移行専用の未指定値がある設計は`ready`にできず、証拠状態は`unverified`でなければなりません。

`xml_generated`は入力IRの自己申告として受け付けません。生成証拠を永続化する場合は、toolkit version、生成日時、XMLと元IRのSHA-256、自動検証結果をレンダラーが作るsidecar manifestへ記録する必要があります。このmanifestは現時点では未実装です。`paste_verified`、`runtime_verified`、`fmse_verified`は、`docs/EVIDENCE_MODEL.md`が要求する独立した実機証拠レコードなしには使用できず、IR入力の値には含めません。CI成功はFileMaker実機証拠へ昇格しません。

## CLI

```powershell
fms19 validate-ir examples/server-script-ir-v2.json
fms19 migrate-ir examples/server-script-ir.json migrated-ir-v2.json
fms19 render examples/server-script-ir.json generated-v1.xml
fms19 render examples/server-script-ir-v2.json generated-v2.xml
```

`validate-ir`は構造と意味の整合を確認します。不足情報を明示した`draft/unverified`の移行v2は、有効な設計文書として保存できるため検証に成功します。これはXML生成可能という意味ではありません。

`render`はv1/v2を自動判定します。完成したv2だけを通常経路で生成し、未解決参照またはblocking事項があれば出力ファイルを書きません。唯一の例外は、元入力がv1であることを`render_ir()`自身が判定した直接v1互換経路です。`migrate-ir`で保存したv2を再入力した場合、この例外は適用されません。

`migrate-ir`はv1だけを受け付け、同じ入力から常に同じUTF-8・LF・末尾改行付きJSONを生成します。FileMakerオブジェクト参照や内部IDは生成しません。

完全な合成例は`examples/server-script-ir-v2.json`を参照してください。
