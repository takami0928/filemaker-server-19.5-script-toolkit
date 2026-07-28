# FileMaker Server 19.5 Script Toolkit

[![CI](https://github.com/takami0928/filemaker-server-19.5-script-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/takami0928/filemaker-server-19.5-script-toolkit/actions/workflows/ci.yml)

FileMaker Server 19.5 にホストされたカスタム App を、AIと人間が**シンプル・保守可能・理解可能・安定動作**する形で実装するための、公開技術リファレンス兼スクリプト補助ツールです。

このリポジトリは社内システムの仕様書ではありません。AIは社内文書からテーブル定義、フィールド、テーブルオカレンス、レイアウト、画面遷移、権限、業務要件を取得し、本リポジトリから「FileMaker Server 19.5でどう実装するか」を取得します。

## 提供範囲

- FileMaker Server 19.5向けのスクリプト作法
- クライアント実行とFileMaker Script Engine（FMSE）実行の境界
- 19.5を対象とした互換性・禁止事項の管理方法
- `fmxmlsnippet`の構造検査
- WindowsのFileMaker専用クリップボード形式への読み書き
- JSON中間表現から検証済みXMLを生成する保守的なレンダラー
- AIが実装案を出す際の固定手順と出力契約

## 対象

- FileMaker Server 19.5
- FileMaker Pro 19.5からホストファイルを開いて開発
- Windows 10/11上のFileMaker Pro 19.5
- Perform Script on Server
- FileMaker ServerのFileMakerスクリプトスケジュール

ローカル単独ファイル、FileMaker 20以降の機能、レイアウトXML生成は初期対象外です。

## 検証状態

- Python単体テスト: 実施済み
- XML構造検査: 実施済み
- Windowsペイロードのencode/decode往復: 実施済み
- FileMaker Pro 19.5実機での`copy → read → write → paste`: **未実施**
- FileMaker Server 19.5上での実行: **未実施**

実機往復が完了するまではアルファ版として扱い、生成XMLを本番ファイルへ直接貼り付けないでください。

## 重要な安全方針

1. 社内情報をこの公開リポジトリへ保存しない。
2. AIは未提示のテーブル、フィールド、レイアウト、スクリプトIDを推測しない。
3. FileMaker 19.5で確認されていないXMLテンプレートは生成対象に加えない。
4. XMLは検証に合格しない限りクリップボードへ書き込まない。
5. 貼り付け後はFileMaker Proの問題表示、参照先、互換性表示を確認する。
6. 「XMLを生成できた」と「実環境で動作した」を区別する。

## クイックスタート

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .

# XML検査
fms19 lint examples/server-script-steps.xml

# JSON中間表現からXML生成
fms19 render examples/server-script-ir.json generated.xml

# WindowsクリップボードへFileMakerスクリプトステップとして格納
fms19 clipboard-write generated.xml

# FileMakerからコピーした専用形式を確認
fms19 clipboard-detect

# FileMakerからコピーしたスクリプトステップをXMLへ保存
fms19 clipboard-read captured.xml
```

FileMaker Pro 19.5でホストファイルを開き、スクリプトワークスペースの挿入位置で貼り付けます。

## 現在のレンダラー対応ステップ

初期版では、構造を保守的に確認できる次のステップだけをJSONから生成します。

- `# (comment)`
- `Set Error Capture`
- `Set Variable`
- `If`
- `Else`
- `End If`
- `Exit Script`

それ以外は、FileMaker Pro 19.5から取得した実物のXMLフィクスチャとテストを追加してから対応します。AIが未知のXMLを推測して生成することは想定していません。

## ドキュメント

- [目的と責任範囲](docs/PURPOSE.md)
- [AI利用契約](AI_GUIDE.md)
- [FileMaker Server 19.5実行境界](docs/FM_SERVER_19_5.md)
- [スクリプト作法](docs/SCRIPT_STYLE.md)
- [サーバー実行設計](docs/SERVER_EXECUTION.md)
- [XML・クリップボード](docs/XML_CLIPBOARD.md)
- [既知の制約](docs/KNOWN_LIMITATIONS.md)
- [検証状態](docs/VALIDATION_STATUS.md)
- [参照資料](docs/REFERENCE_SOURCES.md)

## ライセンスと帰属

Apache License 2.0。

WindowsのFileMaker専用クリップボード形式に関する実装は、Apache-2.0の `petrowsky/agentic-fm` の公開実装を参考に独自に整理しています。詳細は [NOTICE](NOTICE) を参照してください。
