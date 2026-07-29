# 検証状態

## 対象の分離

以下の自動検証状態は、既存の互換性データ、パターン、Script IR、XML、clipboard、配布wheelに関するものです。Copilot knowledge packageの完成度や、Copilotが生成する人間向け設計書の正しさを示しません。

`docs/copilot/`、SharePoint配布パッケージ、SharePoint統合運用、M365 Copilot受入試験はまだ存在または実施していません。

## 自動検証済み

- Python 3.10／3.13での構文・単体テスト
- `fmxmlsnippet`ルートとスクリプトステップ形式
- If / Else / End Ifのブロック整合
- 19.5対象外として明示したステップの拒否
- JSON IRからXMLへの決定的レンダリング
- Script IR v1/v2のJSON Schema Draft 2020-12検証
- v2の変数、コンテキスト、参照キー、制御構造の意味検証
- v1からv2への決定的移行とFileMaker内部ID非生成
- 直接v1だけの互換renderと、保存済みmigration v2のrender拒否
- ネイティブv2における移行専用`unspecified`／`unknown`状態の拒否
- 未解決オブジェクト参照が残る場合のXML生成拒否
- IR入力によるXML生成・FileMaker実機証拠の自己申告拒否
- wheelを空の仮想環境へインストールし、同梱スキーマで行うIR検証・移行
- Issue #7の全59スクリプトステップと参照出典64件の決定的な互換性カタログ正規化
- 7実行コンテキスト、4互換性値、partial条件、後続版遡及、source参照、renderer証拠境界の検査
- `compat`／`list-steps`の完全一致、候補、絞り込み、決定的JSON出力
- wheelを空の仮想環境へインストールし、同梱カタログを使う互換性CLI
- Windows用長さプレフィックス付きUTF-8ペイロードのencode/decode往復
- 出典レジストリの必須項目、ID、URL、日付、重複
- ステップカタログの出典IDと証拠レベル
- 実機証拠を示すメタデータがない状態での証拠昇格拒否
- ステップカタログとレンダラーのID・名称一致
- 禁止ステップカタログと静的検査コードの一致

これらは`structure_tested`または`clipboard_payload_tested`に相当する自動証拠です。FileMaker Pro／Serverによる実行証拠ではありません。

IR検証、移行、レンダリング、XML lint、互換性CLIはWindowsとLinuxのCIで同じコードパスを検査する。Python 3.13の両OS構成ではwheel配布形態も検査する。Win32クリップボードAPIの実機操作はWindows上の手動検証として分離する。

## 実機検証が必要

- FileMaker Pro 19.5が登録する実際のクリップボード形式名
- `Mac-XMSS`ペイロードのFileMaker Pro 19.5貼り付け受理
- 各19.5.xパッチでのXML差
- FileMaker Pro 19.5上での実行結果
- FileMaker Server 19.5のFMSE実行
- フィールド、レイアウト、スクリプト等の内部ID参照

## 実機検証の完了条件

1. FileMaker Pro 19.5の正確なビルドとWindowsバージョンを記録する。
2. FileMaker Pro 19.5で各対象ステップをコピーする。
3. `clipboard-detect`と`clipboard-read`で形式とXMLを取得する。
4. 読み出したXMLをそのまま`clipboard-write`して貼り戻す。
5. FileMakerが問題表示を出さず、ステップ内容が一致することを確認する。
6. レンダラー生成XMLを貼り付け、同じ確認を行う。
7. ホストされた合成テストファイルでクライアント実行する。
8. PSOSまたはサーバースケジュールでFMSE実行する。
9. `docs/EVIDENCE_MODEL.md`に従ってテストメタデータと証拠レベルを登録する。
