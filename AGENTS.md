# Agent Entry Point

AIはこの順で参照してください。

1. [目的と責任範囲](docs/PURPOSE.md)
2. [AI利用契約](AI_GUIDE.md)
3. [FileMaker Server 19.5実行境界](docs/FM_SERVER_19_5.md)
4. [スクリプト作法](docs/SCRIPT_STYLE.md)
5. [サーバー実行設計](docs/SERVER_EXECUTION.md)
6. [XML・クリップボード](docs/XML_CLIPBOARD.md)
7. [検証状態](docs/VALIDATION_STATUS.md)

対象システム固有の情報は社内文書を事実源とし、この公開リポジトリは実装方法の規範として使用してください。未提示のテーブル、フィールド、TO、レイアウト、スクリプト、内部IDを推測してはいけません。

XML生成では、`catalog/fm19.5/verified-steps.json`に登録されたステップと`schemas/script-ir.schema.json`の中間表現だけを使用してください。未登録ステップが必要な場合は、FileMaker Pro 19.5からコピーした実物XMLを取得してから拡張してください。
