# 参照資料

互換性・動作上の主張に使用する正規の出典一覧は、[`sources/registry.json`](../sources/registry.json)で管理する。

この文書は人間向けの案内であり、カタログやコードから参照する場合はURLではなく`sourceId`を使用する。

## 主要な一次資料

- `claris-fm19-running-scripts-on-server`
  - FileMaker Server／CloudでのFMSE実行、コンテキスト、非対応ステップ
- `claris-fm19-script-steps-reference`
  - FileMaker Pro 19のスクリプトステップ
- `claris-fm19-server-script-schedule`
  - FileMaker Server 19のスクリプトスケジュール
- `claris-copy-paste-scripts`
  - FileMaker Proのスクリプトコピー・貼り付け
- `claris-fm19-save-copy-as-xml`
  - FileMaker Pro 19のSave a Copy as XML
- `microsoft-win32-clipboard`
  - Windowsカスタムクリップボード形式とメモリ管理

## 19.5対象外機能の一次資料

- `claris-open-transaction`
- `claris-commit-transaction`
- `claris-revert-transaction`
- `claris-psos-callback`

これらは各ページの`Originated in version`を根拠として、FileMaker 19.5対象では禁止する。

## 二次資料・公開実装

- `agentic-fm-public-implementation`

公開実装は、`fmxmlsnippet`やWindowsクリップボードの構造を観察するための二次資料として扱う。FileMaker Pro 19.5での貼り付けやFileMaker Server 19.5での実行を証明するものではない。

## 運用ルール

- 新しい主張を追加する場合は、先に`sources/registry.json`へ出典を登録する。
- FileMaker 19.5固有の判断では、Clarisの19アーカイブを優先する。
- 現行版ヘルプを使う場合は、19.5へ適用できる根拠を別途確認する。
- 調査メモやDeep Research結果を、そのまま正規仕様として扱わない。
