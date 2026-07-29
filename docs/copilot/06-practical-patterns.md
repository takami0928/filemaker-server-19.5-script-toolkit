# Practical patterns

このpackageが標準patternとして扱うのは、[`patterns/fm19.5/index.json`](../../patterns/fm19.5/index.json)に登録された次の5件だけです。各`pattern.json`がmachine-readableな正本であり、この文書は選択と組合せを要約します。

## 1. JSON parameter validation

- 正本: [`json-parameter-validation/pattern.json`](../../patterns/fm19.5/json-parameter-validation/pattern.json)
- purpose: JSON script parameterを受け取り、空、malformed、未対応contract、必須key／type違反を拒否する。
- applicable context: `client`、`psos`、`server_schedule`
- required placeholders: `EXPECTED_SCHEMA_VERSION`、`REQUIRED_JSON_KEYS`、`SENSITIVE_JSON_KEYS`
- input: version付きJSON parameter
- output: [共通result contract](../../patterns/fm19.5/common-result.schema.json)
- main failure: `EMPTY_PARAMETER`、`INVALID_JSON`、`UNSUPPORTED_SCHEMA_VERSION`、`MISSING_REQUIRED_KEY`、`INVALID_VALUE_TYPE`

## 2. Find one record by primary key

- 正本: [`find-one-by-primary-key/pattern.json`](../../patterns/fm19.5/find-one-by-primary-key/pattern.json)
- purpose: 明示layoutでprimary key検索を行い、0件、1件、複数件を分ける。
- applicable context: `client`、`psos`、`server_schedule`
- required placeholders: `TARGET_LAYOUT`、`TARGET_TABLE_OCCURRENCE`、`PRIMARY_KEY_FIELD`、`PRIMARY_KEY_VALUE_EXPRESSION`、`RESULT_FIELD_MAP`
- input: schema version、request ID、primary keyを含むJSON
- output: 共通result contract
- main failure: invalid criteria、not found、primary key not unique、other find failure

## 3. Create record and verify commit

- 正本: [`create-record/pattern.json`](../../patterns/fm19.5/create-record/pattern.json)
- purpose: 1 recordを作成し、承認fieldを設定してCommit結果を確認する。
- applicable context: `client`、`psos`、`server_schedule`
- required placeholders: `TARGET_LAYOUT`、`TARGET_TABLE_OCCURRENCE`、`PRIMARY_KEY_FIELD`、`GENERATED_PRIMARY_KEY_EXPRESSION`、`FIELD_ASSIGNMENTS`
- optional pair: `IDEMPOTENCY_FIELD`、`IDEMPOTENCY_KEY_EXPRESSION`
- input: schema version、request ID、payloadを含むJSON
- output: 共通result contract
- main failure: create、field assignment、validation、unique constraint、privilege、Commit、duplicate request

## 4. Update record and verify commit

- 正本: [`update-record/pattern.json`](../../patterns/fm19.5/update-record/pattern.json)
- purpose: primary keyで1 recordを特定し、lockを確認して明示fieldだけを更新し、Commit結果を確認する。
- applicable context: `client`、`psos`、`server_schedule`
- required placeholders: `TARGET_LAYOUT`、`TARGET_TABLE_OCCURRENCE`、`PRIMARY_KEY_FIELD`、`PRIMARY_KEY_VALUE_EXPRESSION`、`FIELD_ASSIGNMENTS`、`OUTPUT_FIELD_MAP`
- optional pair: `VERSION_FIELD`、`EXPECTED_VERSION`
- input: schema version、request ID、primary key、changesを含むJSON
- output: 共通result contract
- main failure: not found、non-unique、record lock、optimistic conflict、field assignment、validation、privilege、Commit conflict／failure

## 5. Perform server script and return JSON

- 正本: [`perform-script-on-server/pattern.json`](../../patterns/fm19.5/perform-script-on-server/pattern.json)
- purpose: clientからversion付きJSONを渡し、Wait for completion Onの同期PSOSを実行してJSON resultを受け取る。
- applicable context: callerは`client`、server targetは`psos`
- required placeholders: `SERVER_SCRIPT_NAME`、`REQUEST_SCHEMA_VERSION`、`REQUEST_ID_EXPRESSION`、`OPERATION_NAME`、`PAYLOAD_EXPRESSION`、`SERVER_CONTEXT_PLAN`、`SENSITIVE_JSON_KEYS`、`RELATED_FILE_AUTHENTICATION_PLAN`
- input: schema version、request ID、operation、payloadを含むJSON
- output: 共通result contract
- main failure: PSOS call、timeout／stop／capacity、invalid server result、duplicate request、server business failure

## 組合せ順

1. JSON parameter validationでinput contractを確定する。
2. read／updateならprimary-key findでexactly oneを確定する。
3. createまたはupdateの一方を適用し、Commitを確認する。
4. clientからserver処理を同期実行する場合だけPSOS patternで包み、server側でも1から検証し直す。
5. 全経路を共通result contractへ揃える。

5件で要求を表現できない場合、暗黙の第6 standard patternを追加しません。利用できるcatalog stepとsource-backed guidanceだけで個別設計を`draft_design`として提示し、不足事実とreview範囲を明記します。

すべてのpatternは`design_only`です。required placeholderが未解決なら`draft_design`で停止します。patternを完成script、Script IR、XML template、renderer対応、paste／runtime／FMSE証拠と呼びません。

## Source IDs

Source IDs: `claris-fm19-script-steps-reference`, `claris-fm19-running-scripts-on-server`, `claris-fm19-functions-reference`, `claris-current-error-codes`
