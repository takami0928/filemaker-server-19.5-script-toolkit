# Changelog

## Unreleased

- Issue #7のresearch candidate全59ステップと参照出典64件を、FileMaker 19.5互換性参照カタログへ決定的に正規化
- `fms19 compat`と`fms19 list-steps`を追加し、7実行コンテキスト、4互換性状態、カテゴリ、renderer状態を検索・絞り込み可能に変更
- renderer状態をverified catalogとFileMaker証拠から算出し、互換性、XML生成対応、実機検証を分離
- 正規化差分、出典、後続版遡及、unknown／partial、renderer証拠を検査する品質ゲートとinstalled-wheel smoke testを追加
- 厳格なScript IR v2とDraft 2020-12 JSON Schemaを追加
- 対象バージョン、実行環境、JSON契約、コンテキスト、変数、オブジェクト参照、リスク、設計・証拠状態を明示
- 7種類の既存ステップを`additionalProperties: false`のdiscriminated unionへ変更
- `fms19 validate-ir`と`fms19 migrate-ir`を追加
- v1/v2自動判定とv1の決定的なメモリ内移行をレンダラーへ追加
- 未解決FileMakerオブジェクト参照の内部ID捏造を防止し、XML生成を拒否
- IRスキーマ、例、移行決定性をリポジトリポリシー検査へ追加
- Windows／Linux CIでIR検証、移行、v1/v2レンダリングを実行
- 直接v1入力だけにrender互換例外を限定し、保存済みmigration v2のblocking事項回避を禁止
- ネイティブv2の`unspecified`／`unknown`を拒否し、移行文書へblocking事項と`draft/unverified`を必須化
- IR入力の証拠状態を`unverified`／`design_ready`へ限定し、XML生成・実機証拠の自己申告を拒否
- Windows／Linux CIへinstalled-wheelスキーマ・移行smoke testを追加
- 標準JSON Schema検証のため`jsonschema>=4.23,<5`を追加
- ロードマップ、品質ゲート、成熟度、Definition of Doneを追加
- 出典ポリシーと機械可読な出典レジストリを追加
- FileMaker証拠レベルと昇格規則を追加
- ステップカタログへ出典ID、証拠、未取得証拠、対象外機能の根拠を追加
- カタログ、レンダラー、禁止リスト、出典、証拠を検査するリポジトリ品質チェックを追加
- Codex／AI向け`AGENTS.md`を強化
- Architecture Decision Recordの運用を追加

## 0.1.0

- FileMaker Server 19.5向けの目的・AI利用契約・スクリプト作法を追加
- `fmxmlsnippet`検証器を追加
- 保守的なJSON IRレンダラーを追加
- WindowsのFileMaker専用クリップボード読み書きを追加
- 基本ユニットテストとGitHub Actionsを追加
- 公開リポジトリへ初期版を反映
