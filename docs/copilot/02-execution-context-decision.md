# Execution context判断

## 判断フロー

1. caller、trigger、実行時刻、同期結果の要否、UI対話の要否を確認する。
2. 対象処理がhosted fileで実行されるか、独立server sessionが必要かを確認する。
3. 次の7つからcontextを1つ選び、別名を作らない。
4. 使用候補stepを選択したcontextでcompatibility catalogへ照会する。
5. `partial`のoption／条件を設計へ固定する。`unknown`または`unavailable`なら候補を採用せず停止する。
6. 対象fileのobject、privilege、authentication、session contextを解決する。

## 正規context

| Context | 主な設計上の意味 |
| --- | --- |
| `client` | FileMaker Proの利用者session。UIが必要か、現在contextを明示的に再構築するかを決める。 |
| `psos` | `Perform Script on Server`で開始する独立FMSE session。parameterとresult、wait、再実行を設計する。 |
| `server_schedule` | FileMaker Serverのscheduleで開始する独立FMSE session。実行account、時刻、重複実行、timeoutを設計する。 |
| `webdirect` | WebDirect session。PSOSの別名ではなく、candidate stepを`webdirect`として照会する。 |
| `filemaker_go` | FileMaker Go session。desktop clientまたはPSOSと同一視しない。 |
| `data_api` | Data API経由で起動するscript context。candidate stepを`data_api`として照会する。 |
| `custom_web_publishing` | Custom Web Publishingから起動するcontext。`data_api`やPSOSと同一視しない。 |

`client`、`psos`、`server_schedule`は別contextです。WebDirect、FileMaker Go、Data API、Custom Web PublishingもPSOSの別名ではありません。

## Catalog確認

```text
fms19 compat "Perform Script on Server" --context client --json
fms19 compat "Perform Script on Server" --context psos --json
fms19 list-steps --context server_schedule --support unavailable
```

`fms19 compat`のstep名はcatalogのexact English nameを使います。`partial`なら表示された条件を採用optionへ反映し、解決内容を設計書へ記録します。`unknown`と`unavailable`は、別stepまたは別contextを選べない限りblockingです。

## 必要なinternal context

- callerとtrigger
- synchronous resultの要否
- target fileのhosting状態
- target layout／TOと再構築方法
- 実行accountとprivilege
- related file authentication
- schedule、timeout、同時実行、retry要件
- UI対話の要否
- client固有状態へ依存する入力の有無

contextが確定していない設計は`draft_design`です。contextを推測して`implementation_ready`へ進めません。

## Source IDs

Source IDs: `claris-fm19-script-steps-reference`, `claris-fm19-running-scripts-on-server`, `claris-fm19-server-script-schedule`, `claris-fm19-step-perform-script-on-server`
