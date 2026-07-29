# M365 Copilot knowledge package

```text
Knowledge package version: 0.1.0
Target: FileMaker Pro 19.5 / FileMaker Server 19.5
Primary output: human-readable script design
Implementation method: manual implementation in Script Workspace
SharePoint pilot status: not_run
FileMaker device verification: not_run
```

## 目的

このディレクトリは、Microsoft 365 Copilot等のAIが、別管理された対象システム情報と組み合わせて、FileMaker担当者がFileMaker Pro 19.5のScript Workspaceへ手作業で実装できる設計書を生成するための公開知識です。

対象読者は、設計書を生成するAI、生成結果を確認するFileMaker担当者、公開知識を保守するreviewerです。XMLはformal deliverableではありません。

## 責任分担

- 公開GitHub: FileMaker Server 19.5の一般知識、互換性、設計規則、公開patternを編集・レビューする正本。
- 社内SharePoint: 対象システム固有のtable、TO、field、layout、script、privilege、業務要件を公開知識と分離して管理する場所。
- Microsoft 365 Copilot: 公開知識と許可された社内情報を組み合わせ、review対象の人間向け設計書を生成する利用者。

`docs/copilot/`には公開知識と完全な合成例だけを置きます。社内情報を記入した文書、SharePoint配布package、agent設定、pilot手順、受入試験は含みません。SharePoint pilotは未実施です。

## 読解順

1. [目的とscope](00-purpose-and-scope.md)
2. [FileMaker Server 19.5規則](01-filemaker-server-19.5-rules.md)
3. [execution context判断](02-execution-context-decision.md)
4. [script style](03-script-style.md)
5. [error handling](04-error-handling.md)
6. [record lock、Commit、retry、idempotency](05-record-lock-commit-retry-idempotency.md)
7. [5つのpractical patterns](06-practical-patterns.md)
8. [later-version除外](07-later-version-exclusions.md)
9. [必要な社内context](08-required-internal-context.md)
10. [設計書output contract](09-output-contract.md)
11. [人間reviewとtesting](10-human-review-and-testing.md)
12. [合成完全例](examples/synthetic-complete-design.md)

## 正本とSource IDs

59-step互換性カタログの機械可読な正本は[`script-steps.json`](../../catalog/fm19.5/compatibility/script-steps.json)、そのsource registryは[`sources.json`](../../catalog/fm19.5/compatibility/sources.json)です。一般的な実装・証拠主張のsource registryは[`sources/registry.json`](../../sources/registry.json)です。各文書末尾のSource IDsは、この2つのregistryで解決します。

利用できる標準patternは、[`patterns/fm19.5/index.json`](../../patterns/fm19.5/index.json)に登録された5件だけです。各`pattern.json`が機械可読な正本であり、このpackageは別仕様を作りません。5件はすべて`design_only`です。

## Evidence boundary

このv0.1は、FileMakerファイル、DDR、Save a Copy as XML、screenshot、log、credential、FileMaker Pro／Server 19.5実機環境を使用せずに作成されています。

- source-backedな互換性はFileMaker実機動作の保証ではありません。
- package policyとCIは文書構造、source ID、link、Compatibility ledgerの整合だけを検査します。
- CI成功はpaste、client runtime、FMSE runtimeの証拠ではありません。
- Copilot出力は必ず人間がreviewし、対象環境で手作業実装・testします。
- packageの配布manifestとsource commitはIssue #15の後続工程で扱います。
