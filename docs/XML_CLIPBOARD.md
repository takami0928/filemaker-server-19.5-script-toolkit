# fmxmlsnippetとWindowsクリップボード

## 目的

FileMaker Proのスクリプトワークスペースへ貼り付けるには、XML文字列を通常のテキストとしてコピーするだけでは不十分である。Windows版FileMakerが認識するカスタムクリップボード形式へ格納する。

## 初期実装

本ツールはスクリプトステップを次の形式として扱う。

- XMLルート: `<fmxmlsnippet type="FMObjectList">`
- 先頭オブジェクト: `<Step ...>`
- Windowsカスタム形式名: 通常 `Mac-XMSS`
- ペイロード: 4バイトのリトルエンディアンXML長 + UTF-8 XML

環境差を検出するため、FileMaker Pro 19.5から任意のステップをコピーした後に`fms19 clipboard-detect`を実行する。

## 安全な拡張方法

1. FileMaker Pro 19.5で対象ステップを作成する。
2. 対象ステップだけをコピーする。
3. `fms19 clipboard-read fixtures/<step>.xml`で取得する。
4. 可変値と固定属性を分離する。
5. レンダラーへテンプレートを追加する。
6. XML構造、ブロック整合、特殊文字、貼り付けをテストする。
7. FileMaker Pro 19.5で貼り付け後の問題表示と参照先を確認する。

## ID参照

フィールド、レイアウト、スクリプト等を参照するXMLには名前だけでなく内部IDが含まれる場合がある。社内文書に名前しかない場合、IDを推測してはならない。対象ファイルからコピーしたXMLまたはSave a Copy as XML等の社内資料から、正しいIDを取得する。

## 検証と実行の区別

- XML well-formed: XMLとして読める
- snippet valid: ルート、種類、ステップ、制御構造が規則に合う
- paste accepted: FileMaker Proが貼り付けを受け入れる
- reference resolved: フィールド、レイアウト、スクリプト参照が正しい
- runtime verified: 実環境で期待どおり動く

これらは別の状態である。
