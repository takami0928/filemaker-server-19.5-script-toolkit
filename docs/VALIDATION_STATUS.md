# 検証状態

## 自動検証済み

- Python 3.10以降での構文
- `fmxmlsnippet`ルートとスクリプトステップ形式
- If / Else / End Ifのブロック整合
- 19.5対象外として明示したステップの拒否
- JSON IRからXMLへの決定的レンダリング
- Windows用長さプレフィックス付きUTF-8ペイロードの往復

## 実機検証が必要

- FileMaker Pro 19.5が登録する実際のクリップボード形式名
- `Mac-XMSS`ペイロードのFileMaker Pro 19.5貼り付け受理
- 各19.5.xパッチでのXML差
- FileMaker Server 19.5のFMSE実行
- フィールド、レイアウト、スクリプト等の内部ID参照

## 実機検証の完了条件

1. FileMaker Pro 19.5で各対象ステップをコピーする。
2. `clipboard-detect`と`clipboard-read`で形式とXMLを取得する。
3. 読み出したXMLをそのまま`clipboard-write`して貼り戻す。
4. FileMakerが問題表示を出さず、ステップ内容が一致することを確認する。
5. レンダラー生成XMLを貼り付け、同じ確認を行う。
6. ホストファイルのテスト用スクリプトでFMSE実行する。
