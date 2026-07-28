# 検証状態

## 自動検証済み

- Python 3.10／3.13での構文・単体テスト
- `fmxmlsnippet`ルートとスクリプトステップ形式
- If / Else / End Ifのブロック整合
- 19.5対象外として明示したステップの拒否
- JSON IRからXMLへの決定的レンダリング
- Script IR v1/v2のJSON Schema Draft 2020-12検証
- v2の変数、コンテキスト、参照キー、制御構造の意味検証
- v1からv2への決定的移行とFileMaker内部ID非生成
- 未解決オブジェクト参照が残る場合のXML生成拒否
- Windows用長さプレフィックス付きUTF-8ペイロードのencode/decode往復
- 出典レジストリの必須項目、ID、URL、日付、重複
- ステップカタログの出典IDと証拠レベル
- 実機証拠を示すメタデータがない状態での証拠昇格拒否
- ステップカタログとレンダラーのID・名称一致
- 禁止ステップカタログと静的検査コードの一致

これらは`structure_tested`または`clipboard_payload_tested`に相当する自動証拠です。FileMaker Pro／Serverによる実行証拠ではありません。

IR検証、移行、レンダリング、XML lintはWindowsとLinuxのCIで同じコードパスを検査する。Win32クリップボードAPIの実機操作はWindows上の手動検証として分離する。

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
