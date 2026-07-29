# FileMaker Server 19.5 Script Toolkit

[![CI](https://github.com/takami0928/filemaker-server-19.5-script-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/takami0928/filemaker-server-19.5-script-toolkit/actions/workflows/ci.yml)

このリポジトリは、Microsoft 365 Copilot等のAIが社内のFileMakerシステム情報と組み合わせて、FileMaker Server 19.5に適合する安全で保守可能なスクリプト設計書を生成するための、公開知識・判断・実用パターンパッケージです。

正式な中心成果物は、FileMaker担当者がScript Workspaceへ手作業で実装できる完全な人間向け設計書です。XMLは正式成果物ではありません。

この公開リポジトリに社内システム固有情報は保存しません。情報境界と責任範囲の正本は[目的と責任範囲](docs/PURPOSE.md)を参照してください。

## 成果物の区分

### 主成果物

- FileMaker Server 19.5の互換性知識と後続バージョン機能の除外
- client、PSOS、server schedule、WebDirect等の実行コンテキスト判断
- エラー処理、レコードロック、Commit／Revert、冪等性、セキュリティを含むスクリプト設計ルール
- 全59ステップの正規化互換性カタログ
- JSON検証、1件検索、作成、更新、PSOSの5つの実用パターンと共通JSON結果契約
- 人間向け設計書の出力契約
- FileMaker担当者によるレビューとテストの手順
- 必須情報が不足したときの停止条件と、推測せずに残す未解決事項

### 保守用の裏側

- 互換性JSON
- `research-candidate`
- 出典レジストリと証拠境界
- 互換性CLI
- カタログ／パターン検査
- CIによるリポジトリ品質検査

### 凍結された実験領域

- Script IR v2の拡張
- 独自XML rendererの拡張
- clipboard機能の拡張
- fixture round-trip pipeline
- wheel配布機能の拡張
- 大規模静的解析
- 大規模AI評価基盤

既存実装は削除しませんが、明示的な再承認なしに拡張しません。XML／IR／clipboardは副次的な実験機能であり、FileMaker Pro／Server 19.5実機未検証です。

Copilot向け公開知識パッケージv0.1は、[`docs/copilot/README.md`](docs/copilot/README.md)をknowledge-first入口として提供します。FileMakerファイルや実機環境を使わず、公開資料、59-step互換性カタログ、5つの`design_only`パターン、完全な合成例だけで作成しています。

SharePoint配布パッケージとM365 Copilot pilotは未作成・未実施です。FileMaker Pro／Server 19.5実機検証も未実施で、XMLは引き続きformal outputではありません。次工程は[ロードマップ](ROADMAP.md)のIssue #15です。

## 情報の役割分担

- **公開GitHub**: FileMaker Server 19.5の一般知識、設計ルール、判断、実用パターンを編集・レビューする正本
- **社内SharePoint**: 対象システム固有のオブジェクト、業務フロー、権限、命名規則、既存仕様、実装要求を、公開知識とは分離して管理する場所
- **Microsoft 365 Copilot**: 公開知識と社内情報を組み合わせ、人間向け設計書を生成する利用者

## 対象

- FileMaker Server 19.5
- FileMaker Pro 19.5からホストファイルを開いて開発
- Windows 10/11上のFileMaker Pro 19.5
- Perform Script on Server
- FileMaker ServerのFileMakerスクリプトスケジュール

ローカル単独ファイル、FileMaker 20以降の機能、レイアウトXML生成は初期対象外です。

## 現在存在する資産と検証境界

凍結されたXML／IRサブシステムの成熟度は **M2 — governed design and compilation** です。これはCopilot knowledge packageの完成や、設計書の実機検証を意味しません。

- Python単体テスト: 実施済み
- Script IR v1/v2のDraft 2020-12検証と意味検証: 実施済み
- v1からv2への決定的移行: 実施済み
- wheelを空の仮想環境へインストールし、同梱スキーマで検証・移行: 実施済み
- 未解決FileMakerオブジェクトIDのXML生成拒否: 実施済み
- XML構造検査: 実施済み
- Windowsペイロードのencode/decode往復: 実施済み
- 出典ID、証拠レベル、カタログとコードの整合検査: 実施済み
- FileMaker Pro 19.5実機での`copy → read → write → paste`: **未実施**
- FileMaker Server 19.5上での実行: **未実施**

実機往復が完了するまではXML関連機能をアルファ版として扱い、生成XMLを本番ファイルへ直接貼り付けないでください。XML／IRサブシステムの成熟度の定義は[こちら](docs/MATURITY_MODEL.md)です。

## 重要な安全方針

1. 社内情報をこの公開リポジトリへ保存しない。
2. SharePoint向け公開知識パッケージへ社内情報を混入させない。
3. AIは未提示のテーブル、フィールド、レイアウト、スクリプトID、権限、業務仕様を推測しない。
4. FileMaker 19.5より後の機能を19.5向け設計へ混入させない。
5. 人間向け設計書をFileMaker担当者がレビューし、Script Workspaceへ手作業で実装してテストする。
6. XMLは検証に合格しない限りクリップボードへ書き込まない。
7. 「設計できた」「XMLを生成できた」「実環境で動作した」を区別する。
8. CI成功をFileMaker実機証拠として扱わない。
9. 互換性・動作上の主張は登録済み出典IDへ紐づける。正規化互換性カタログは専用の`catalog/fm19.5/compatibility/sources.json`を使い、その他は`sources/registry.json`を使う。

## 知識を使うクイックスタート

最初に次を確認します。

1. [Copilot knowledge package v0.1](docs/copilot/README.md)を公開知識の入口として読む。
2. [目的と責任範囲](docs/PURPOSE.md)でGitHub、SharePoint、Copilotの境界を確認する。
3. [AI利用契約](AI_GUIDE.md)で設計書の処理順、出力形式、停止条件を確認する。
4. [FileMaker 19.5互換性カタログ](docs/COMPATIBILITY_CATALOG.md)で実行コンテキスト別の互換性を確認する。
5. [5つの実用パターン](patterns/README.md)を設計の構成要素として利用する。

互換性CLIを使う場合は、次を実行します。

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .

# リポジトリ品質ゲート
python scripts/check_repository.py

# FileMaker 19.5互換性を検索
fms19 compat "Perform Script on Server" --context psos
fms19 compat "Insert File" --context server_schedule

# 互換性カタログを絞り込み
fms19 list-steps --context psos --support available
fms19 list-steps --category control
fms19 list-steps --renderer-status experimental
```

互換性が`available`でもXML生成可能または実機検証済みとは限りません。

## 実験的・実機未検証のXML／IRコマンド

次の既存コマンドは、XML／IRサブシステムを保守または調査するときだけ使用します。生成物はFileMaker Pro／Server 19.5で未検証であり、正式成果物ではありません。

```powershell
# XML検査
fms19 lint examples/server-script-steps.xml

# Script IR v2検証
fms19 validate-ir examples/server-script-ir-v2.json

# v1を、不足情報を明示したdraft/unverifiedのv2へ決定的に移行
fms19 migrate-ir examples/server-script-ir.json migrated-ir-v2.json

# 元入力がv1の場合だけ、限定された後方互換経路でXML生成
fms19 render examples/server-script-ir.json generated.xml

# 完成したv2からXML生成
fms19 render examples/server-script-ir-v2.json generated-v2.xml

# WindowsクリップボードへFileMakerスクリプトステップとして格納
fms19 clipboard-write generated.xml

# FileMakerからコピーした専用形式を確認
fms19 clipboard-detect

# FileMakerからコピーしたスクリプトステップをXMLへ保存
fms19 clipboard-read captured.xml
```

貼り付けを試す場合も、合成テスト環境でFileMaker担当者が問題表示、参照先、互換性、実行結果を別々に確認します。

## FileMaker 19.5互換性CLI

`catalog/fm19.5/compatibility/`には、Issue #7のresearch candidate全59ステップと、それらが参照する64出典を実用参照用に正規化して保存しています。

`fms19 compat <step-name>`はFileMaker Pro 19.5での存在、導入版、Server対応導入版、7つの実行コンテキスト、条件・リスク、出典、renderer状態を表示します。名前は大文字小文字を区別せず完全一致を優先し、完全一致しない場合は候補を表示するだけで自動選択しません。

`fms19 list-steps`はcontext、support、category、renderer statusで絞り込めます。`available`、`unavailable`、`partial`、`unknown`は別状態で、`partial`と`unknown`を利用可能として扱いません。`--json`は決定的な機械可読出力です。

互換性カタログは公開資料に基づく参照で、`catalog/fm19.5/verified-steps.json`のXML renderer／fixture証拠とは別です。renderer statusは後者から実行時に算出し、FileMaker Pro 19.5貼り付け証拠のない実装を`verified`にしません。このPhase AではXML renderer、Script IR、fixtureを拡張していません。

詳細は[FileMaker 19.5互換性カタログ](docs/COMPATIBILITY_CATALOG.md)、設計判断は[ADR 0003](decisions/0003-normalize-compatibility-catalog-and-cli.md)を参照してください。

## 実用スクリプト設計パターン

`patterns/fm19.5/`には、AIと人間が業務スクリプトを設計するためのPhase B成果物として、次の5パターンだけを保存しています。

1. JSONスクリプト引数の受取と検証
2. 主キーによる1件検索
3. レコード新規作成とCommit確認
4. レコード更新、ロック確認、Commit確認
5. Wait for completion OnのPSOS呼出しとJSON結果返却

各ディレクトリの`pattern.json`が機械可読な正本で、READMEは人間向け説明です。対象ファイル固有のレイアウト、TO、フィールド、スクリプト、計算式はプレースホルダーで表し、必須値が未解決なら`block_generation`として完成スクリプトの出力を止めます。内部FileMaker IDを生成・推測しません。

各ステップのcontext別互換性は59件の正規カタログと照合し、renderer statusは`catalog/fm19.5/verified-steps.json`から再計算します。`not_verified`なステップも設計には利用できますが、XML生成可能とは扱いません。全パターンは`design_only`で、FileMaker Pro／Server 19.5実機未検証です。XML renderer、Script IR、verified catalogはPhase Bで変更していません。

パターン集は現時点ではリポジトリ設計資料であり、CLIやruntime APIを提供しないためwheelへ同梱していません。利用手順と証拠境界は[実用スクリプト設計パターン](patterns/README.md)を参照してください。

## 凍結中の実験的レンダラー対応ステップ

初期版では、構造を保守的に確認できる次のステップだけをJSONから生成します。

- `# (comment)`
- `Set Error Capture`
- `Set Variable`
- `If`
- `Else`
- `End If`
- `Exit Script`

これらはすべて`experimental`です。自動テスト済みですが、FileMaker Pro 19.5への貼り付けおよびFileMaker Server 19.5での実行は未検証です。

それ以外は、FileMaker Pro 19.5から取得した実物XMLフィクスチャとテストを追加してから対応します。AIが未知のXMLを推測して生成することは想定していません。

## 凍結中の実験的Script IR v2

Script IR v2は、FileMaker Server / Pro 19.5、実行モード、スクリプト目的、副作用、JSON入出力契約、コンテキスト、変数、FileMakerオブジェクト参照、未解決事項、リスク、設計・証拠状態を明示します。

フィールド、レイアウト、TO、スクリプト、値一覧の内部IDが不明な場合は、名前と`resolution: "unresolved"`だけを保持します。IDを自動生成せず、未解決参照またはblocking事項が残るv2からはXMLを生成しません。`migration`マーカーもこの検査を回避しません。

既存v1を直接`render`した場合だけ、元入力をv1と判定した内部情報に基づいて従来と同じ7ステップXMLを生成します。`migrate-ir`で保存したv2は検証・編集できますが、不足情報を人間が補完するまでrenderできません。`validate-ir`の成功は、設計文書として整合していることを示し、XML生成可能であることは示しません。

IR入力の証拠状態は`unverified`と`design_ready`だけです。XML生成、FileMaker Pro貼り付け、クライアント実行、FMSE実行はIR自身に申告できず、生成manifestまたは`docs/EVIDENCE_MODEL.md`に従う別の検証記録が必要です。

詳細は[Script IR](docs/SCRIPT_IR.md)、完全な合成例は[server-script-ir-v2.json](examples/server-script-ir-v2.json)、設計判断は[ADR 0002](decisions/0002-script-ir-v2.md)を参照してください。

IR、移行、レンダリング、XML lintはWindowsとLinuxのCIで同じコードパスを実行します。Python 3.13のWindows/Linux構成では、`python -m build`でwheelを作り、空の仮想環境へインストールし、リポジトリ外から同梱スキーマを使う検証・移行も行います。ローカルでは`python -m pip install -e ".[ci]"`後に`python scripts/smoke_test_wheel.py`で同じ検査を実行できます。

Win32クリップボードAPIを使う`clipboard-read`、`clipboard-write`、`clipboard-detect`だけはWindows専用で、実機操作はCIおよびIssue #3の対象外です。

## 開発計画と品質基準

- [ロードマップ](ROADMAP.md)
- [品質ゲート](QUALITY_GATES.md)
- [Definition of Done](docs/DEFINITION_OF_DONE.md)
- [証拠モデル](docs/EVIDENCE_MODEL.md)
- [出典ポリシー](docs/SOURCE_POLICY.md)
- [Architecture Decision Records](decisions/README.md)

## 技術ドキュメント

- [Copilot knowledge package v0.1](docs/copilot/README.md)
- [目的と責任範囲](docs/PURPOSE.md)
- [AI利用契約](AI_GUIDE.md)
- [FileMaker 19.5互換性カタログ](docs/COMPATIBILITY_CATALOG.md)
- [実用スクリプト設計パターン](patterns/README.md)
- [スクリプト作法](docs/SCRIPT_STYLE.md)
- [サーバー実行設計](docs/SERVER_EXECUTION.md)
- [FileMaker Server 19.5実行境界](docs/FM_SERVER_19_5.md)
- [既知の制約](docs/KNOWN_LIMITATIONS.md)
- [検証状態](docs/VALIDATION_STATUS.md)
- [参照資料](docs/REFERENCE_SOURCES.md)

### 凍結中の実験領域

- [Script IR](docs/SCRIPT_IR.md)
- [XML・クリップボード](docs/XML_CLIPBOARD.md)

## ライセンスと帰属

Apache License 2.0。

WindowsのFileMaker専用クリップボード形式に関する実装は、Apache-2.0の `petrowsky/agentic-fm` の公開実装を参考に独自に整理しています。詳細は [NOTICE](NOTICE) を参照してください。
