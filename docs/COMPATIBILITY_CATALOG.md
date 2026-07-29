# FileMaker 19.5互換性カタログ

## 目的と範囲

`catalog/fm19.5/compatibility/`は、スクリプトを設計する前に、FileMaker Pro 19.5での存在と実行コンテキスト別の利用可否を確認するための参照カタログです。Issue #7の`research-candidate`から、全59スクリプトステップと、それらが参照する64出典を決定的に正規化しています。

このカタログはFileMaker XMLを生成するためのテンプレートではありません。Phase Aではrenderer、Script IR、clipboard数値ID、fixtureを追加していません。

## 3つのデータ境界

| データ | 役割 | 証拠境界 |
| --- | --- | --- |
| `research/issue-7/candidates/` | Deep Researchの原資料 | `research-candidate` |
| `catalog/fm19.5/compatibility/` | 公開資料に基づく19.5互換性の実用参照 | `documented`を保持した正規化参照 |
| `catalog/fm19.5/verified-steps.json` | XML renderer実装とfixture証拠 | 互換性カタログとは独立 |

正規化は調査内容の意味や証拠レベルを変更しません。`script-steps.json`には互換性情報、`sources.json`にはその59件が実際に参照する出典候補の完全なレコードを保存します。後者は互換性カタログ専用のsource registryです。未登録ID、重複ID、候補からの情報消失、`secondary`から`primary`への昇格を品質ゲートで拒否します。

renderer statusは互換性JSONへ手入力しません。CLIが`verified-steps.json`とその証拠から次のように算出します。

- `verified`: renderer catalogが`supported`で、`fm19_5_paste_verified`証拠がある
- `experimental`: renderer catalogに実装エントリはあるが、上記の実機貼り付け証拠がない
- `not_verified`: renderer catalogに対応エントリがない

コードが存在すること、research candidate、CI成功、XMLの構造検査だけでは`verified`になりません。

## 互換性値

- `available`: 対象コンテキストで利用可能と資料に記録されている
- `unavailable`: 対象コンテキストで利用不可
- `partial`: オプション、条件、制約によって可否が変わる。説明を必須とする
- `unknown`: 根拠が不足している。利用可能とは扱わない

`partial`も単純な利用可能扱いにはしません。設計前に表示された条件を解消してください。`unknown`はfail closedとし、追加調査または実機検証なしに採用しません。

## 実行コンテキスト

正規名は次の7種類です。

- `client`
- `psos`
- `server_schedule`
- `webdirect`
- `filemaker_go`
- `data_api`
- `custom_web_publishing`

入力時だけ、`schedule`と`server`を`server_schedule`、`web_direct`を`webdirect`、`go`を`filemaker_go`、`cwp`を`custom_web_publishing`の別名として受け付けます。ヘルプと出力は正規名を使います。

`introducedIn`はステップ自体の導入版、`serverSupportIntroducedIn`はServer実行対応の導入版です。両者を混同しません。Server対応が19.5より後のステップを、PSOSまたはserver scheduleで19.5対応として扱うことを品質ゲートで拒否します。後続版の現行ヘルプは、19.5への遡及根拠にはしません。

## CLI

完全一致は大文字小文字を区別せず、前後空白を無視します。完全一致しない名前は自動選択せず、最大5件の候補を標準エラーへ表示して非ゼロ終了します。

```text
fms19 compat "Perform Script on Server"
fms19 compat "Perform Script on Server" --context psos
fms19 compat "Insert File" --context server_schedule
fms19 compat "Pause/Resume Script" --json
```

`unavailable`または`unknown`という検索結果も、ステップの検索自体には成功しているため終了コードは0です。不明なステップ名またはcontextは非ゼロ終了します。`--json`は決定的なUTF-8 JSONだけを標準出力へ出し、エラーは標準エラーへ出します。

```text
fms19 list-steps
fms19 list-steps --context psos
fms19 list-steps --context psos --support available
fms19 list-steps --context server_schedule --support unavailable
fms19 list-steps --category control
fms19 list-steps --renderer-status experimental
fms19 list-steps --context psos --support partial --json
```

`--support`は`--context`と組み合わせる必要があります。一覧はカテゴリ、名称の順で決定的に並びます。

## AIが判断する順序

AIは次の順序を崩してはいけません。

1. ステップがFileMaker Pro 19.5に存在するか確認する。
2. 対象実行コンテキストで利用可能か確認する。
3. `partial`または`unknown`の条件や不足情報が残っていないか確認する。
4. ステップまたはServer対応がFileMaker 19.5より後に導入された機能ではないか確認する。
5. renderer対応とprovenance-aware fixture証拠を別に確認する。
6. 対象ファイル固有のレイアウト、TO、フィールド、スクリプト等のオブジェクト参照が解決済みか確認する。

互換性が`available`でもXMLを生成できるとは限りません。rendererが`experimental`または`not_verified`なら、既知のXML生成範囲を拡大してはいけません。逆にrenderer実装があっても、対象コンテキストの互換性を省略してはいけません。

## 更新と検査

正規化ファイルは次で再生成します。

```text
python scripts/build_compatibility_catalog.py
```

`python scripts/check_repository.py`は、JSON構造、必須項目、59件の完全性、重複名、7コンテキスト、列挙値、`partial`の説明、source参照、後続版の遡及、候補データとの差分、renderer証拠の不当昇格を検査します。生成結果に意味上の変更が必要なら、正本であるresearch candidateと出典を先に更新し、独立レビューを受けます。

FileMaker Pro 19.5貼り付け、クライアント実行、FileMaker Server 19.5 FMSE実行は、いずれもこのカタログとCLIでは未検証です。
