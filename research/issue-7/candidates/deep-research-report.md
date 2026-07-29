# FileMaker Server 19.5 公開技術リファレンス構築
## GitHub Issue #7 Deep Research — 探査漏れ監査・改訂版

- 調査・改訂日: 2026-07-29
- 対象: `takami0928/filemaker-server-19.5-script-toolkit`
- 対象Issue: #7
- 対象製品: FileMaker Server 19.5 / FileMaker Pro 19.5
- 位置づけ: 規約採用前の、出典付き・レビュー可能な候補資料
- 互換性ポリシー: deny-by-default / unknownは推測しない / Partialはoption単位に分解する

---

# 1. エグゼクティブサマリー

## 1.1 監査結論

ユーザーが指定した主要領域について、**未分類のまま残る重要領域はない**。ただし、これは「すべて解決済み」という意味ではない。次の領域は、公式資料の欠落、ベンダー依存、またはFileMaker Pro/Server 19.5実機でしか確定できないため、`unresolved`として明示的に分類した。

- 19.5.1〜19.5.4の公式パッチ差
- PSOS・スケジュールの正確な文字数境界
- グローバルフィールドと`$$`変数の初期値・寿命・分離
- 関連ファイルの再認証・権限
- スクリプトトリガのFMSE発火マトリクス
- 管理者停止・timeout時の原子性
- スケジュール重複・PSOS枯渇
- プラグイン、ODBC/ESSの具体的製品組合せ
- WebDirect desktop/mobile差
- `fmxmlsnippet`のFileMaker Pro 19.5由来fixture
- DDR XML IDとクリップボードXML IDの関係
- PDF出力品質、OSパス、ファイル書込みの環境差

したがって、改訂版は「既知」と「未解決」を混ぜず、**未解決事項を生成ブロッカーとして管理できる状態**にした。

## 1.2 初版からの重要修正

| 項目 | 初版 | 改訂 |
|---|---|---|
| Save Records as Excel | Server partial | Server No in FileMaker 19 archive; skipped with error 3. |
| Insert File | Server partial | Server No in FileMaker 19 archive; skipped with error 3. |
| Export Field Contents | Server partial | Server No for 19.5; later server support must be version-gated. |
| Pause/Resume Script | Server No | Server Yes; unattended indefinite pause is operationally unsafe. |
| Modify Last Find | unknown | Server Yes in FileMaker 19 reference. |
| Set Variable | Originated in 7.0 | Originated in 8.0. |
| Constrain/Extend Found Set | Originated in 7.0 | Originated in 6.0 or earlier. |
| Save Records as Snapshot Link | Server partial | Server Yes; WebDirect/Go remain option-limited. |
| Set Error Logging | not investigated | Step exists in 19.5 Pro, but FMSE support begins in Server 20.1.1. |
| Error code 4 | merged into error 3 | Error 4 is unknown command and has distinct Allow User Abort behavior. |
| ODBC 1401 | connection failure | Failed to allocate ODBC environment. |
| File errors 816/817 | misassigned | 816 conversion failure; 817 solution-membership mismatch. |
| fmxmlsnippet numeric IDs | insufficient separation | DDR IDs and clipboard IDs are separate evidence domains; all candidate clipboard IDs are null. |

特に重要なのは、**ステップの導入版**と**FileMaker Server対応の導入版**を別フィールドにしたことである。たとえば`Set Error Logging`はFileMaker Pro 18.0で導入済みだが、FMSE対応はFileMaker Server 20.1.1からであり、19.5のPSOS・サーバースケジュールでは使用不可である。

## 1.3 FMSEの中心原則

PSOSとサーバースケジュールは、クライアント処理の「場所だけをサーバーへ移す」ものではない。FMSEは独立セッションを作成する。

クライアントから自動継承されない主要状態:

- 現在レイアウト
- 現在レコード
- found set
- sort order
- ローカル変数
- グローバル変数
- クライアントセッションのグローバルフィールド値

必要状態は、バージョン付きJSON引数で渡し、サーバー側でレイアウト、検索、対象レコード、ソートを再構築する。

## 1.4 互換性判断の重要な修正

FileMakerヘルプの互換性は次の意味を持つ。

- `Yes`: その製品で可能な範囲の機能をサポート
- `No`: ステップをスキップし、エラー3を返す
- `Partial`: ステップは実行されるが、一部のoptionが説明どおり動作しない

したがって、`Partial`を`true`へ変換してはならない。また、エラー3「利用不可」とエラー4「未知コマンド」は異なる。未知コマンド時のFMSE停止は`Allow User Abort`の設定と関係する。

---

# 2. FileMaker Server 19.5の実行モデル

## 2.1 PSOS

| 項目 | 判定 |
|---|---|
| セッション | 呼出クライアントとは別のFMSEセッション |
| アカウント | 原則として呼出クライアントと同じアカウント |
| レイアウト・found set等 | 継承しない |
| `$` / `$$`変数 | 継承しない |
| グローバルフィールド値 | クライアント値を継承しない |
| スクリプト引数 | `Get ( ScriptParameter )`で明示取得 |
| スクリプト結果 | Wait for completionがOnの場合に呼出元で取得 |
| クライアントによる中止 | サーバーセッションを直接停止できない |
| 管理者による中止 | Admin Console等からFMSEセッションを停止可能 |
| ダイアログ | ユーザー不在。対話型optionは禁止または無効 |
| ログ | アプリ側構造化ログとServer Event.logを併用 |

## 2.2 サーバースケジュール

| 項目 | 判定 |
|---|---|
| セッション | スケジュールごとの独立FMSEセッション |
| アカウント | スケジュールに登録したアカウント |
| 引数 | スケジュール設定のparameter |
| 結果 | 呼出元クライアントはない。永続表・ファイル・Event.logへ保存 |
| timeout | スケジュール設定により停止可能 |
| 管理者停止 | 可能 |
| 重複実行 | 正確な19.5.4挙動を実機試験対象とする |
| エラー表示 | 対話表示不可。構造化ログ必須 |

## 2.3 推奨パラメータ契約

```json
{
  "schemaVersion": 1,
  "requestId": "UUID",
  "operation": "catalog-operation-id",
  "requestedByAccount": "account-name",
  "context": {
    "layout": "Server_Utility",
    "tableOccurrence": "Orders",
    "recordKey": {
      "field": "Orders::UUID",
      "value": "..."
    }
  },
  "payload": {},
  "idempotencyKey": "UUID"
}
```

FMSE側の標準順序:

1. `Get ( ScriptParameter )`
2. JSON構文・schemaVersion・必須key・型・長さを検証
3. `Get ( ApplicationVersion )` / `Get ( HostApplicationVersion )`でversion guard
4. `Go to Layout`
5. Find Modeでapplication UUIDを検索
6. error 401と複数件を明示判定
7. 必要なら`Open Record/Request`
8. 変更
9. `Commit Records/Requests`
10. 直後に`Get ( LastError )`
11. 構造化resultを`Exit Script`
12. request IDをログへ保存

## 2.4 同時実行・冪等性

FMSEスクリプトは、同じレコード、同じ外部API、同じファイル名へ並行実行される可能性がある。次を最低限要求する。

- request ID
- idempotency key
- 処理状態テーブル
- 取得・実行・完了の状態遷移
- レコード modification IDまたは業務version
- 一意な出力パス
- bounded retry
- uncertain outcomeの照合処理
- schedule overlap guard
- 外部APIの重複送信防止

## 2.5 ファイルアクセス

FMSEが扱えるローカルパスは、Documents、Temporary、およびその子フォルダに制限される。`..`を含むpathを拒否し、OS固有pathを直接組み立てず、`Get ( DocumentsPath )`と`Get ( TemporaryPath )`を起点にする。

ファイル処理では、19.5でServer非対応の`Insert File`や`Save Records as Excel`を無理に使わず、用途に応じて次を優先する。

- `Export Records`
- `Insert from URL`
- `Create/Open/Read/Write/Close Data File`
- `Get File Exists`
- `Delete File`

---

# 3. 互換性判断の原則

1. FileMaker 19アーカイブの個別ステップページを第一根拠にする。
2. 現行ヘルプは`Originated in version`と後続版の変化探索に使う。
3. 現行のServer `Yes`を19.5へ遡及しない。
4. ステップ導入版とServer対応導入版を別管理する。
5. `Partial`はoption ruleが揃うまで生成不可にする。
6. 不明は`null`または`unknown`。
7. Data APIは、外部REST APIと`Execute FileMaker Data API`ステップを区別する。
8. WebDirectはdesktop/mobileを将来別contextに分ける。
9. エラー3、4、1、401を同じ「失敗」に潰さない。
10. `Get ( LastError )`を対象ステップ直後に保存する。
11. ODBC/cURL/plug-inは外部detailも保存する。
12. destructive stepはfound set、権限、対象件数、idempotencyを事前検証する。
13. `Get ( UserName )`を認可に使わない。
14. internal record IDを業務keyにしない。
15. DDR XML、Save a Copy as XML、clipboard `fmxmlsnippet`を別仕様として扱う。
16. 数値step IDを推測しない。
17. public GitHub fixtureは`public_fixture_observed`まで。
18. FileMaker Pro 19.5のcopy/paste証拠がないstepをrendererへ追加しない。
19. FileMaker Server 19.5実行証拠がないstepを`fmse_verified`としない。
20. 19.5.xパッチ差が不明な場合は、最小対応範囲または`unknown`を採用する。

---

# 4. 高優先度ステップ一覧

改訂版は、指定された51ステップに加え、未探査だった`Set Error Logging`と、Server 19.5で安全なファイル処理代替となる7つのdata-fileステップを含む。合計59件。

| ステップ | 導入版 | Client | PSOS | Schedule | WebDirect | Go | Data API | 確度 |
|---|---:|---|---|---|---|---|---|---|
| Allow User Abort | 6.0 or earlier | Yes | Partial | Partial | Yes | Yes | Partial | high |
| Set Error Capture | 6.0 or earlier | Yes | Partial | Partial | Yes | Yes | Partial | high |
| Set Error Logging | 18.0 | Yes | No | No | No | Yes | No | high |
| Set Variable | 8.0 | Yes | Yes | Yes | Yes | Yes | Yes | high |
| If | 6.0 or earlier | Yes | Yes | Yes | Yes | Yes | Yes | high |
| Else If | 6.0 or earlier | Yes | Yes | Yes | Yes | Yes | Yes | high |
| Else | 6.0 or earlier | Yes | Yes | Yes | Yes | Yes | Yes | high |
| End If | 6.0 or earlier | Yes | Yes | Yes | Yes | Yes | Yes | high |
| Loop | 6.0 or earlier | Yes | Yes | Yes | Yes | Yes | Yes | high |
| Exit Loop If | 6.0 or earlier | Yes | Yes | Yes | Yes | Yes | Yes | high |
| End Loop | 6.0 or earlier | Yes | Yes | Yes | Yes | Yes | Yes | high |
| Perform Script | 6.0 or earlier | Yes | Yes | Yes | Yes | Yes | Yes | high |
| Perform Script on Server | 13.0 | Yes | Yes | Yes | Yes | Yes | Yes | high |
| Exit Script | 6.0 or earlier | Yes | Yes | Yes | Yes | Yes | Yes | high |
| Halt Script | 6.0 or earlier | Yes | Yes | Yes | Yes | Yes | Yes | high |
| Pause/Resume Script | 6.0 or earlier | Yes | Yes | Yes | Yes | Yes | Yes | high |
| Go to Layout | 6.0 or earlier | Yes | Partial | Partial | Partial | Yes | Partial | high |
| New Window | 6.0 or earlier | Yes | Yes | Yes | Partial | Partial | Partial | high |
| Close Window | 6.0 or earlier | Yes | Yes | Yes | Yes | Yes | Yes | high |
| Select Window | 6.0 or earlier | Yes | Yes | Yes | Yes | Yes | Yes | high |
| Enter Browse Mode | 6.0 or earlier | Yes | Partial | Partial | Yes | Yes | Partial | high |
| Enter Find Mode | 6.0 or earlier | Yes | Partial | Partial | Yes | Yes | Partial | high |
| Go to Record/Request/Page | 6.0 or earlier | Yes | Partial | Partial | Yes | Yes | Partial | high |
| Go to Related Record | 6.0 or earlier | Partial | Partial | Partial | Partial | Yes | Partial | high |
| Show All Records | 6.0 or earlier | Yes | Yes | Yes | Yes | Yes | Yes | high |
| Omit Record | 6.0 or earlier | Yes | Yes | Yes | Yes | Yes | Yes | high |
| Sort Records | 6.0 or earlier | Yes | Partial | Partial | Yes | Yes | Partial | high |
| Set Field | 6.0 or earlier | Yes | Yes | Yes | Yes | Yes | Yes | high |
| Perform Find | 6.0 or earlier | Yes | Yes | Yes | Yes | Yes | Yes | high |
| Constrain Found Set | 6.0 or earlier | Yes | Yes | Yes | Yes | Yes | Yes | high |
| Extend Found Set | 6.0 or earlier | Yes | Yes | Yes | Yes | Yes | Yes | high |
| Modify Last Find | 6.0 or earlier | Yes | Yes | Yes | Yes | Yes | Yes | high |
| New Record/Request | 6.0 or earlier | Yes | Yes | Yes | Yes | Yes | Yes | high |
| Duplicate Record/Request | 6.0 or earlier | Yes | Yes | Yes | Yes | Yes | Yes | high |
| Open Record/Request | 6.0 or earlier | Yes | Yes | Yes | Yes | Yes | Yes | high |
| Commit Records/Requests | 6.0 or earlier | Yes | Partial | Partial | Yes | Yes | Partial | high |
| Revert Record/Request | 6.0 or earlier | Yes | Partial | Partial | Yes | Yes | Partial | high |
| Delete Record/Request | 6.0 or earlier | Yes | Partial | Partial | Yes | Yes | Partial | high |
| Delete All Records | 6.0 or earlier | Yes | Partial | Partial | Yes | Yes | Partial | high |
| Replace Field Contents | 6.0 or earlier | Yes | Partial | Partial | Yes | Yes | Partial | high |
| Relookup Field Contents | 6.0 or earlier | Yes | Partial | Partial | Yes | Yes | Partial | high |
| Import Records | 6.0 or earlier | Yes | Partial | Partial | Partial | Partial | No | high |
| Export Records | 6.0 or earlier | Yes | Partial | Partial | Partial | Partial | No | high |
| Export Field Contents | 6.0 or earlier | Yes | No | No | Partial | Partial | No | high |
| Insert File | 6.0 or earlier | Yes | No | No | Partial | Partial | No | high |
| Insert from URL | 12.0 | Yes | Yes | Yes | Yes | Yes | Yes | high |
| Execute SQL | 12.0 | Yes | Partial | Partial | Partial | No | Partial | high |
| Execute FileMaker Data API | 19.0 | Yes | Yes | Yes | Yes | Yes | Yes | high |
| Send Mail | 6.0 or earlier | Yes | Partial | Partial | Partial | Partial | Partial | high |
| Save Records as PDF | 8.0 | Yes | Partial | Partial | Partial | Partial | No | high |
| Save Records as Excel | 8.0 | Yes | No | No | No | No | No | high |
| Save Records as Snapshot Link | 11.0 | Yes | Yes | Yes | Partial | Partial | No | high |
| Create Data File | 18.0 | Yes | Yes | Yes | No | Yes | No | high |
| Open Data File | 18.0 | Yes | Yes | Yes | No | Yes | No | high |
| Read from Data File | 18.0 | Yes | Yes | Yes | No | Yes | No | high |
| Write to Data File | 18.0 | Yes | Yes | Yes | No | Yes | No | high |
| Close Data File | 18.0 | Yes | Yes | Yes | No | Yes | No | high |
| Get File Exists | 18.0 | Yes | Yes | Yes | No | Yes | No | high |
| Delete File | 18.0 | Yes | Yes | Yes | No | Yes | No | high |

## 4.1 特に重要な個別判断

### `Set Error Logging`

- FileMaker Pro 19.5には存在する。
- FileMaker Server 19.5のFMSEでは利用不可。
- Server対応は20.1.1から。
- 19.5のPSOS・scheduleで使うと、互換性`No`としてエラー3を想定する。

### `Pause/Resume Script`

初版のServer非対応判定は誤り。Server対応である。ただし、無期限pauseはサーバースクリプトセッションを占有し、timeoutや管理者停止に依存するため、unattended automationでは原則禁止する。

### `Export Field Contents`

FileMaker Server 19.5では非対応。後続版でServer対応が追加されているため、現行ヘルプを見て19.5でも動くと誤認しやすい代表例である。

### `Insert File`

FileMaker Server 19.5では非対応。containerへの入力は、import、URL取得、またはserver-safeな別経路へ置換する。

### `Save Records as Excel`

FileMaker Server 19.5では非対応。`Export Records`の対応形式またはdata-file処理を検討する。

### `Save Records as PDF`

ServerではPartial。ダイアログ、自動open、email添付作成はFMSEで使えない。印刷権限とfound setが必要。FileMaker Data APIからの対応は20.1.1以降であり、19.5 Data APIでは非対応。

### `Execute FileMaker Data API`

FileMaker 19アーカイブに基づく19.5候補は`read`と`metaData`に限定する。create/update/delete/duplicateは後続拡張として除外する。request-level errorはresult JSONの`messages`を確認する。

### data-fileステップ

`Create Data File`、`Open Data File`、`Read from Data File`、`Write to Data File`、`Close Data File`、`Get File Exists`、`Delete File`は18.0導入で、FileMaker Server 19.5に存在する重要なI/O基盤である。初版では未探査だった。

---

# 5. 重要関数一覧

| 関数 | 導入版 | FMSEでの意味 | 注意 |
|---|---:|---|---|
| `Get ( ScriptParameter )` | 7.0 | Returns only the explicitly passed parameter. It does not transport layout, found set, record, variables, globals, or privilege context. | Define a versioned JSON contract and validate it before changing context. |
| `Get ( ScriptResult )` | 8.0 | Returns the last completed subscript result. A PSOS caller requires Wait for completion to obtain the result reliably. | Do not confuse script result text with transport/runtime success. |
| `Get ( LastError )` | 6.0 or earlier | Numeric error from the most recently executed script step. | Read immediately after the step under test.; If, Else, Else If, End If, Loop, Exit Loop If, End Loop, Exit Script, and Halt Script do not clear the previous error.; Pair with Get ( LastExternalErrorDetail ) for ODBC/cURL/external failures. |
| `Get ( LastExternalErrorDetail )` | 6.0 or earlier | 19.5-safe name for detailed ODBC/external errors. | Capture immediately because subsequent external operations may overwrite detail. |
| `Get ( ApplicationVersion )` | 6.0 or earlier | Product and version of the executing FileMaker application. | Use as a runtime guard, but parse defensively; product/version string formats vary. |
| `Get ( HostApplicationVersion )` | 9.0 | Product and version of the host. | Distinguish executing FMSE version from host version; both can matter during mixed-version operation. |
| `Get ( SystemPlatform )` | 6.0 or earlier | Platform on which the calculation is evaluated. | — |
| `Get ( UserName )` | 6.0 or earlier | User preference name; not an authorization identity. | Not an authorization identity. Never use for privilege decisions. |
| `Get ( AccountName )` | 7.0 | Authenticated account name. | Related files may authenticate differently; test cross-file privilege behavior. |
| `Get ( AccountPrivilegeSetName )` | 11.0 | Current privilege-set name. | Related files may authenticate differently; test cross-file privilege behavior. |
| `Get ( LayoutName )` | 6.0 or earlier | Current layout name in the executing session. | Value describes the independent FMSE context, not the initiating client context. |
| `Get ( LayoutTableName )` | 7.0 | Table occurrence associated with current layout. | Value describes the independent FMSE context, not the initiating client context. |
| `Get ( FoundCount )` | 6.0 or earlier | Number of records in current found set. | Value describes the independent FMSE context, not the initiating client context. |
| `Get ( RecordID )` | 6.0 or earlier | Internal FileMaker record ID. | Internal record IDs are not portable business keys; pass and find by a stable application UUID. |
| `Get ( RecordNumber )` | 6.0 or earlier | Position in current found set. | Value describes the independent FMSE context, not the initiating client context. |
| `Get ( RecordOpenState )` | 7.0 | Record open/lock state in current session. | A zero/nonzero state does not replace commit-error and modification-ID handling. |
| `Get ( TemporaryPath )` | 10.0 | Session temporary folder path. | Do not hard-code OS paths; use returned FileMaker-format path.; Reject '..' and control filename collisions. |
| `Get ( DocumentsPath )` | 10.0 | Documents folder path for current product. | Do not hard-code OS paths; use returned FileMaker-format path.; Reject '..' and control filename collisions. |
| `Get ( DocumentsPathListing )` | 10.0 | Listing of the Documents folder; unsupported in WebDirect/Data API/CWP. | Returns empty string in unsupported products.; Listing is not an authorization or atomic existence check. |
| `JSONGetElement` | 16.0 | Reads a JSON element and reports parser errors as text results. | JSON functions do not enforce a business schema; validate required keys, types, length, and allowed values separately. |
| `JSONSetElement` | 16.0 | Creates or updates JSON elements with explicit FileMaker JSON types. | JSON functions do not enforce a business schema; validate required keys, types, length, and allowed values separately. |
| `JSONListKeys` | 16.0 | Lists object keys or array indexes. | JSON functions do not enforce a business schema; validate required keys, types, length, and allowed values separately. |
| `JSONListValues` | 16.0 | Lists values in a JSON object or array. | JSON functions do not enforce a business schema; validate required keys, types, length, and allowed values separately. |
| `JSONFormatElements` | 16.0 | Formats JSON and exposes syntax errors; not a schema validator. | JSON functions do not enforce a business schema; validate required keys, types, length, and allowed values separately. |

## 5.1 `Get ( LastExternalErrorDetail )`の名称

19.5向け候補名として、依頼で指定された`Get ( LastExternalErrorDetail )`を保持する。ただし、公式の旧版アーカイブはこの名称を示す一方、累積FileMaker 19ヘルプは`Get ( LastErrorDetail )`と後続のtransaction関連説明を表示する。したがって、名称変更または置換の正確な19.5/19.6.1境界を公式リリースノートと実機で確定するまで、どちらの名称も無条件生成してはならない。

## 5.2 JSON関数

JSON関数が構文上成功しても、業務schemaが正しいとは限らない。最低限、次を別検証する。

- schemaVersion
- 必須key
- type
- 許可key
- 最大長
- enum
- UUID形式
- path traversal
- script/object IDを外部入力から直接受けない
- privilege-sensitive field名を任意指定させない

---

# 6. 重要エラー一覧

| code | 意味 | 典型箇所 | 推奨処理 |
|---:|---|---|---|
| -1 | Unknown error | Any step | Return a structured unknown failure with step, script, parameter request ID, and environment. |
| 0 | No error | Any step | Continue only if the business postcondition is also satisfied. |
| 1 | User canceled action | Interactive client; abortable operations | In FMSE, distinguish administrator/timeout termination from a client-user cancel. |
| 3 | Command is unavailable | Unsupported platform, mode, or option | Treat as a compatibility defect; fail closed and record the exact step/option. |
| 4 | Command is unknown | Later-version or corrupted/unknown script step | With Allow User Abort On, FMSE may terminate; never conflate with error 3. |
| 5 | Command is invalid | Missing/invalid step parameter or calculation | Treat as generator/design defect. |
| 9 | Insufficient privileges | Record, field, layout, script, print, export | Return authorization failure; do not retry under a different account automatically. |
| 10 | Requested data is missing | Missing object/data required by command | Validate required context and inputs before mutation. |
| 14 | Out of range | Record/page/repetition/parameter index | Validate bounds and return deterministic input error. |
| 16 | Operation failed; retry is required | Transient query/operation failure | Use a bounded retry only when the operation is idempotent. |
| 100 | File is missing | Import/export/insert/data-file/external file | Validate allowed path and existence; distinguish missing file from forbidden path. |
| 101 | Record is missing | Navigation, relation, delete | Handle as explicit empty-context/not-found result. |
| 102 | Field is missing | Set Field, import mapping, calculation | Fail closed as schema drift. |
| 103 | Relationship is missing | Related-record navigation/calculation | Fail closed as relationship-graph drift. |
| 104 | Script is missing | Perform Script/PSOS | Fail closed; catalog/script reference drift. |
| 105 | Layout is missing | Go to Layout/context reconstruction | Fail before data mutation. |
| 106 | Table is missing | Context, import, calculation | Fail closed as schema drift. |
| 112 | Window is missing | Select/Close Window | Recreate expected FMSE window/context or fail. |
| 113 | Function is missing | Calculation evaluation | Likely version or plug-in/function availability defect. |
| 114 | File reference is missing | Related/external FileMaker file | Validate file reference and host access. |
| 116 | Data source is missing | ODBC/ESS/external source | Validate server-side DSN/source configuration. |
| 117 | Calculation is missing | Stored step/calculation reference | Fail as design corruption or schema drift. |
| 200 | Record access is denied | Read/write/delete | Return authorization failure. |
| 201 | Field cannot be modified | Set Field, import, replace | Check calculation/storage/validation/privileges. |
| 202 | Field access is denied | Read/write/find | Return authorization failure and avoid leaking field content. |
| 203 | No records to print, or printing privilege denied | Save Records as PDF/printing | Check found set and printing privilege separately. |
| 204 | No access to fields in sort order | Sort Records | Use an allowed sort specification or fail. |
| 205 | No privilege to create records | New/Duplicate/Import | Return authorization failure. |
| 300 | File is locked or in use | Schema/file operation | Do not spin; report locking owner/context where available. |
| 301 | Record is in use by another user | Open/commit/delete/replace | Use bounded retry with jitter only for idempotent work; otherwise surface conflict. |
| 302 | Table is in use by another user | Bulk/schema operations | Retry later or serialize the job. |
| 303 | Database schema is in use by another user | Schema-dependent operation | Stop automation and retry after schema editing ends. |
| 304 | Layout is in use by another user | Layout operation | Stop/retry; do not mutate context assumptions. |
| 306 | Record modification ID does not match | Optimistic-concurrency conflict | Reload and re-evaluate business intent; never overwrite blindly. |
| 307 | Transaction/record lock failed due to host communication | Commit/locking | Treat as uncertain outcome; verify persisted state before retry. |
| 400 | Find criteria are empty | Perform Find | Handle explicitly; do not accidentally Show All and continue destructive work. |
| 401 | No records match the request | Find/constrain/extend | Usually a valid zero-result business outcome; branch explicitly. |
| 402 | Selected field is not a match field for a lookup | Relookup | Fail as schema/configuration defect. |
| 404 | Sort order is invalid | Sort Records | Treat restored sort specification as stale or inaccessible. |
| 409 | Import order is invalid | Import Records | Fail before import; regenerate verified field mapping. |
| 410 | Export order is invalid | Export Records | Fail before export; regenerate verified field list. |
| 413 | Specified field has an inappropriate field type | Import/export/container operation | Fail input/schema validation. |
| 414 | Layout cannot display the result | Layout-dependent operation | Use a server-safe utility layout. |
| 415 | One or more required related records are not available | Related-record/portal operation | Handle missing relation explicitly. |
| 416 | Primary key is required from the data source table | ESS/external table create | Fix external schema/mapping. |
| 500 | Date value fails validation | Commit/import | Return field-level validation detail. |
| 501 | Time value fails validation | Commit/import | Return field-level validation detail. |
| 502 | Number value fails validation | Commit/import | Return field-level validation detail. |
| 503 | Value is outside validation range | Commit/import | Return field-level validation detail. |
| 504 | Field value is not unique | Create/update/import | Treat as deterministic conflict; use application key/idempotency. |
| 505 | Field value is not an existing value | Commit/import | Return validation detail. |
| 506 | Field value is not in value list | Commit/import | Return validation detail. |
| 507 | Field value fails validation calculation | Commit/import | Return validation detail without exposing secrets. |
| 508 | Invalid value entered in Find mode | Find criteria | Reject malformed criteria before executing find. |
| 509 | Field requires a valid value | Commit/import | Return required-field failure. |
| 511 | Field value exceeds maximum field size | Set/import/JSON payload | Enforce length limits before write. |
| 512 | Record was already modified by another user | Commit | Reload and resolve conflict; do not overwrite automatically. |
| 800 | Unable to create file on disk | Export/PDF/snapshot/data-file | Check permitted path, permissions, collision, and disk. |
| 801 | Unable to create temporary file on system disk | I/O | Check server temp space and permissions. |
| 802 | Unable to open file | Import/export/data-file | Check path, permissions, sharing, and file state. |
| 803 | File is single-user or host cannot be found | External FileMaker file/host | Check hosting, network, and file open state. |
| 804 | File cannot be opened as read-only in its current state | File open | Resolve file state/permissions; do not force. |
| 805 | File is damaged; use Recover | File open | Stop automation and preserve evidence; do not make Recover routine. |
| 806 | File cannot be opened with this version of FileMaker Pro | File open | Version mismatch; do not convert in unattended job. |
| 807 | File is not a FileMaker file or is severely damaged | File open/import | Reject or quarantine input. |
| 809 | Disk or volume is full | Any file output | Stop writes and alert operator. |
| 810 | Disk or volume is locked | Any file output | Stop and fix storage permissions/state. |
| 812 | Server hosting capacity exceeded | Open/host/session | Backpressure/queue; alert administrator. |
| 813 | Record synchronization error on network | Hosted record operation | Treat outcome as uncertain; re-read before retry. |
| 814 | File cannot be opened because maximum number is open | Open related file | Close unused files or reduce dependencies. |
| 815 | Lookup file cannot be opened | Lookup/related file | Validate host/account/file reference. |
| 816 | Unable to convert file | File conversion | Stop; conversion is outside server-script automation. |
| 817 | Unable to open file because it does not belong to this solution | Runtime/authorized solution | Correct solution binding/authorization. |
| 820 | File is being closed | Hosted file operation | Retry only after confirming the file is reopened. |
| 821 | Host forced a disconnect | PSOS/schedule/host communication | Treat in-flight outcome as uncertain and reconcile by request ID. |
| 825 | File is not authorized to reference a protected file | External file reference | Configure authorized-file access; do not weaken security ad hoc. |
| 826 | File path specified is not valid | Import/export/data-file | Reject invalid/unsafe path; rebuild from Get(DocumentsPath/TemporaryPath). |
| 1400 | ODBC client driver initialization failed | Execute SQL/ODBC import/ESS | Verify compatible 64-bit driver and server configuration. |
| 1401 | Failed to allocate ODBC environment | ODBC | Treat as server driver/resource failure. |
| 1404 | Failed to allocate ODBC connection | ODBC | Check driver resources and DSN. |
| 1407 | Failed to allocate ODBC statement | ODBC | Check driver/resource state. |
| 1408 | Extended ODBC error | ODBC | Immediately persist Get ( LastExternalErrorDetail ). |
| 1409 | ODBC error | ODBC | Persist external detail if available; classify retryability. |
| 1413 | ODBC communication link failure | ODBC | Treat as transient/uncertain; verify transaction outcome. |
| 1414 | SQL statement is too long | Execute SQL | Reduce/bind/split statement; do not retry unchanged. |
| 1501 | SMTP authentication failed | Send Mail | Fix credentials/auth method; do not retry repeatedly. |
| 1502 | Connection refused by SMTP server | Send Mail | Check host/port/network and bounded retry. |
| 1503 | SSL error | Send Mail | Fix TLS/certificate configuration. |
| 1504 | SMTP server requires encrypted connection | Send Mail | Enable supported encryption. |
| 1505 | Specified authentication is not supported by SMTP server | Send Mail | Change configured auth method. |
| 1506 | Email messages could not be sent successfully | Send Mail | Persist recipient/request IDs and avoid duplicate resend. |
| 1507 | Unable to log in to SMTP server | Send Mail | Fix credentials/server policy. |
| 1550 | Cannot load the plug-in, or plug-in is invalid | Plug-in step/function | Disable dependent workflow; verify server-compatible plug-in build. |
| 1551 | Cannot install plug-in; cannot replace/write file | Install Plug-In File | Check server plug-in folder permissions and deployment policy. |
| 1552 | Plug-in-defined error range begins | Plug-in | Interpret only with vendor documentation; preserve vendor detail. |
| 1626 | Protocol is not supported | Insert from URL/cURL | Reject URL/protocol. |
| 1627 | Authentication failed | Insert from URL/cURL | Fix auth; do not leak credentials. |
| 1628 | SSL error | Insert from URL/cURL | Fix TLS/certificate policy. |
| 1629 | Connection timed out | Insert from URL/cURL | Use bounded retry only for idempotent request. |
| 1630 | URL format is incorrect | Insert from URL/cURL | Validate/encode URL. |
| 1631 | Connection failed | Insert from URL/cURL | Classify DNS/network/refusal and retry only when safe. |
| 1632 | Certificate has expired | Insert from URL/cURL | Reject until certificate is replaced. |
| 1633 | Certificate is self-signed | Insert from URL/cURL | Do not bypass verification without explicit policy. |
| 1634 | Certificate verification error | Insert from URL/cURL | Fix trust chain/hostname/time. |
| 1635 | Connection is unencrypted | Insert from URL/cURL | Reject for sensitive data. |
| 1638 | Host is not allowing new connections | Insert from URL/cURL | Back off and retry later if idempotent. |
| 1700 | Resource does not exist | Data API/REST | Return not-found and verify endpoint/resource. |
| 1701 | Host is unable to receive requests | Data API/REST | Back off; preserve request ID. |
| 1702 | Authorization header format is invalid | Data API/REST | Fix request authentication format. |
| 1703 | Invalid credentials or token | Data API/REST | Refresh/fix identity; do not retry unchanged. |
| 1704 | Resource does not support HTTP verb | Data API/REST | Correct method; in 19.5 do not use later write actions. |
| 1705 | Required HTTP header is missing | Data API/REST | Validate request contract. |
| 1706 | Parameter is unsupported | Data API/REST | Remove/version-gate parameter. |
| 1707 | Required parameter is missing | Data API/REST | Validate request contract. |
| 1708 | Parameter value is invalid | Data API/REST | Reject input. |
| 1709 | Operation invalid for resource state | Data API/REST | Re-read state; do not retry blindly. |
| 1710 | JSON input is syntactically invalid | Data API/REST/JSON | Validate JSON before execution. |

## 6.1 エラー3と4

- 3: 現在のproduct、mode、OS、optionではコマンドを利用できない。
- 4: コマンド自体を認識できない。
- 後続版stepを含むscriptを19.5で扱う場合、4はversion contaminationまたは未知XMLの重要信号になる。
- `Allow User Abort`の状態によって、FMSEが未知stepで停止するか継続するかが変わり得る。

## 6.2 401

検索0件は、多くの業務では正常な分岐である。ただし削除、replace、export前の検索では、安全停止条件として扱う。

## 6.3 301・306・512

レコード競合は、単純retryだけでは解決しない。業務version、modification ID、request IDで意図を再評価する。

## 6.4 外部エラー

ODBC、SMTP、plug-in、cURL、Data APIは、FileMaker codeだけでなく外部detail、endpoint、driver/plugin version、request ID、retry countを記録する。

---

# 7. 19.5対象外機能一覧

| 機能 | 種別 | 導入・対応追加版 | 除外理由 |
|---|---|---:|---|
| Open Transaction | scriptStep | 19.6.1 | Introduced after target. |
| Commit Transaction | scriptStep | 19.6.1 | Introduced after target. |
| Revert Transaction | scriptStep | 19.6.1 | Introduced after target. |
| Set Revert Transaction on Error | scriptStep | 21.1.1 | Introduced after target. |
| Perform Script On Server with Callback | scriptStep | 20.1 | Introduced after target. |
| Get ( LastErrorLocation ) | function | 19.6.1 | Introduced after target even though a cumulative FileMaker 19 archive may list it. |
| Get ( RevertTransactionOnErrorState ) | function | 21.1.1 | Paired with later transaction behavior. |
| Execute FileMaker Data API write actions: create, update, delete, duplicate | scriptStepExpansion | 21.0.1 (release-note verification required before normative use) | FileMaker 19 archive documents read and metaData only. |
| Set Error Logging in FMSE | serverCompatibilityExpansion | 20.1.1 | The step exists in 19.5 Pro, but server support was added later. |
| Save Records as PDF via FileMaker Data API | dataApiCompatibilityExpansion | 20.1.1 | Data API support was added later. |
| Export Field Contents in FileMaker Server | serverCompatibilityExpansion | 26.0.1 | Later server support must not be backported. |
| Configure AI Account | scriptStep | 21.0 | AI feature introduced after target. |
| Insert Embedding in Found Set | scriptStep | 21.0 | AI feature introduced after target. |
| Perform Semantic Find and related semantic-search steps | scriptStep | 21.0 or later | AI feature introduced after target; verify each exact step independently. |
| Perform SQL Query by Natural Language | scriptStep | 22.0 | AI feature introduced after target. |

この一覧は、単に「FileMaker 20以降のstep名」を並べたものではない。19.5に存在するstepでも、Server対応だけが後で追加された場合を除外対象として含める。

---

# 8. 出典レジストリ候補

合計110件。個別ステップ・関数にFileMaker 19アーカイブのsource IDを付与し、後続版のtransitionは現行helpまたはrelease notesへ分離した。

| source ID | 種別 | 対象版 | タイトル |
|---|---|---|---|
| `claris-fm19-script-steps-reference` | primary | FileMaker Pro 19 archive | Script steps reference |
| `claris-fm19-running-scripts-on-server` | primary | FileMaker Pro/Server 19 archive | About running scripts on FileMaker Server and FileMaker Cloud |
| `claris-fm19-server-running-filemaker-scripts` | primary | FileMaker Server 19 archive | Running FileMaker scripts |
| `claris-fm19-server-schedule-details` | primary | FileMaker Server 19 archive | Specifying script schedule details |
| `claris-fm19-server-side-paths` | primary | FileMaker Pro/Server 19 archive | Paths in server-side scripts |
| `claris-fm19-functions-reference` | primary | FileMaker Pro 19 archive | Functions reference |
| `claris-current-error-codes` | primary | Current help; code meanings must be checked for 19.5-era applicability | FileMaker error codes |
| `claris-fm19-save-copy-as-xml` | primary | FileMaker Pro 19 archive | Save a Copy as XML |
| `claris-ddrxml-18` | primary | FileMaker Pro 18 DDR XML | FileMaker Pro 18 Advanced Database Design Report XML Output Grammar |
| `microsoft-win32-clipboard-formats` | primary | Windows Win32 API | Clipboard Formats |
| `agentic-fm-public-implementation` | secondary | Version provenance not independently proven as FileMaker Pro 19.5 | agentic-fm public FileMaker XML and clipboard implementation |
| `github-issue-7` | secondary | Project requirement | Build source-backed FileMaker Server 19.5 compatibility catalog |
| `claris-current-open-transaction` | primary | Current help; originated in 19.6.1 | Open Transaction |
| `claris-current-commit-transaction` | primary | Current help; originated in 19.6.1 | Commit Transaction |
| `claris-current-revert-transaction` | primary | Current help; originated in 19.6.1 | Revert Transaction |
| `claris-current-set-revert-transaction-on-error` | primary | Current help; originated in 21.1.1 | Set Revert Transaction on Error |
| `claris-current-psos-callback` | primary | Current help; originated in 20.1 | Perform Script On Server with Callback |
| `claris-current-get-last-error-location` | primary | Current help; originated in 19.6.1 | Get(LastErrorLocation) |
| `claris-current-configure-ai-account` | primary | Current help; originated in 21.0 | Configure AI Account |
| `claris-current-insert-embedding-found-set` | primary | Current help; originated in 21.0 | Insert Embedding in Found Set |
| `claris-current-perform-semantic-find` | primary | Current help; originated in 21.0 or later | Perform Semantic Find |
| `claris-current-perform-sql-query-natural-language` | primary | Current help; originated in 22.0 | Perform SQL Query by Natural Language |
| `claris-server-release-notes-20-1-1` | primary | FileMaker Server 20.1.1 and later release notes | Claris FileMaker Server 20.1.1 Release Notes |
| `claris-pro-release-notes` | primary | Current cumulative release notes | Claris FileMaker Pro Release Notes |
| `secondary-fms-19-5-3-release-notes-mirror` | secondary | FileMaker Server 19.5.3 | FileMaker Server 19.5.3 Release Notes mirror |
| `secondary-fms-19-5-4-release-notes-mirror` | secondary | FileMaker Server 19.5.4 | FileMaker Server 19.5.4 Release Notes mirror |
| `claris-fm19-step-allow-user-abort` | primary | FileMaker Pro 19 archive | Allow User Abort |
| `claris-fm19-step-set-error-capture` | primary | FileMaker Pro 19 archive | Set Error Capture |
| `claris-fm19-step-set-error-logging` | primary | FileMaker Pro 19 archive | Set Error Logging |
| `claris-fm19-step-set-variable` | primary | FileMaker Pro 19 archive | Set Variable |
| `claris-fm19-step-if-script-step` | primary | FileMaker Pro 19 archive | If |
| `claris-fm19-step-else-if` | primary | FileMaker Pro 19 archive | Else If |
| `claris-fm19-step-else` | primary | FileMaker Pro 19 archive | Else |
| `claris-fm19-step-end-if` | primary | FileMaker Pro 19 archive | End If |
| `claris-fm19-step-loop` | primary | FileMaker Pro 19 archive | Loop |
| `claris-fm19-step-exit-loop-if` | primary | FileMaker Pro 19 archive | Exit Loop If |
| `claris-fm19-step-end-loop` | primary | FileMaker Pro 19 archive | End Loop |
| `claris-fm19-step-perform-script` | primary | FileMaker Pro 19 archive | Perform Script |
| `claris-fm19-step-perform-script-on-server` | primary | FileMaker Pro 19 archive | Perform Script on Server |
| `claris-fm19-step-exit-script` | primary | FileMaker Pro 19 archive | Exit Script |
| `claris-fm19-step-halt-script` | primary | FileMaker Pro 19 archive | Halt Script |
| `claris-fm19-step-pause-resume-script` | primary | FileMaker Pro 19 archive | Pause/Resume Script |
| `claris-fm19-step-go-to-layout` | primary | FileMaker Pro 19 archive | Go to Layout |
| `claris-fm19-step-new-window` | primary | FileMaker Pro 19 archive | New Window |
| `claris-fm19-step-close-window` | primary | FileMaker Pro 19 archive | Close Window |
| `claris-fm19-step-select-window` | primary | FileMaker Pro 19 archive | Select Window |
| `claris-fm19-step-enter-browse-mode` | primary | FileMaker Pro 19 archive | Enter Browse Mode |
| `claris-fm19-step-enter-find-mode` | primary | FileMaker Pro 19 archive | Enter Find Mode |
| `claris-fm19-step-go-to-record-request-page` | primary | FileMaker Pro 19 archive | Go to Record/Request/Page |
| `claris-fm19-step-go-to-related-record` | primary | FileMaker Pro 19 archive | Go to Related Record |
| `claris-fm19-step-show-all-records` | primary | FileMaker Pro 19 archive | Show All Records |
| `claris-fm19-step-omit-record` | primary | FileMaker Pro 19 archive | Omit Record |
| `claris-fm19-step-sort-records` | primary | FileMaker Pro 19 archive | Sort Records |
| `claris-fm19-step-set-field` | primary | FileMaker Pro 19 archive | Set Field |
| `claris-fm19-step-perform-find` | primary | FileMaker Pro 19 archive | Perform Find |
| `claris-fm19-step-constrain-found-set` | primary | FileMaker Pro 19 archive | Constrain Found Set |
| `claris-fm19-step-extend-found-set` | primary | FileMaker Pro 19 archive | Extend Found Set |
| `claris-fm19-step-modify-last-find` | primary | FileMaker Pro 19 archive | Modify Last Find |
| `claris-fm19-step-new-record-request` | primary | FileMaker Pro 19 archive | New Record/Request |
| `claris-fm19-step-duplicate-record-request` | primary | FileMaker Pro 19 archive | Duplicate Record/Request |
| `claris-fm19-step-open-record-request` | primary | FileMaker Pro 19 archive | Open Record/Request |
| `claris-fm19-step-commit-records-requests` | primary | FileMaker Pro 19 archive | Commit Records/Requests |
| `claris-fm19-step-revert-record-request` | primary | FileMaker Pro 19 archive | Revert Record/Request |
| `claris-fm19-step-delete-record-request` | primary | FileMaker Pro 19 archive | Delete Record/Request |
| `claris-fm19-step-delete-all-records` | primary | FileMaker Pro 19 archive | Delete All Records |
| `claris-fm19-step-replace-field-contents` | primary | FileMaker Pro 19 archive | Replace Field Contents |
| `claris-fm19-step-relookup-field-contents` | primary | FileMaker Pro 19 archive | Relookup Field Contents |
| `claris-fm19-step-import-records` | primary | FileMaker Pro 19 archive | Import Records |
| `claris-fm19-step-export-records` | primary | FileMaker Pro 19 archive | Export Records |
| `claris-fm19-step-export-field-contents` | primary | FileMaker Pro 19 archive | Export Field Contents |
| `claris-fm19-step-insert-file` | primary | FileMaker Pro 19 archive | Insert File |
| `claris-fm19-step-insert-from-url` | primary | FileMaker Pro 19 archive | Insert from URL |
| `claris-fm19-step-execute-sql` | primary | FileMaker Pro 19 archive | Execute SQL |
| `claris-fm19-step-execute-filemaker-data-api` | primary | FileMaker Pro 19 archive | Execute FileMaker Data API |
| `claris-fm19-step-send-mail` | primary | FileMaker Pro 19 archive | Send Mail |
| `claris-fm19-step-save-records-as-pdf` | primary | FileMaker Pro 19 archive | Save Records as PDF |
| `claris-fm19-step-save-records-as-excel` | primary | FileMaker Pro 19 archive | Save Records as Excel |
| `claris-fm19-step-save-records-as-snapshot-link` | primary | FileMaker Pro 19 archive | Save Records as Snapshot Link |
| `claris-fm19-step-create-data-file` | primary | FileMaker Pro 19 archive | Create Data File |
| `claris-fm19-step-open-data-file` | primary | FileMaker Pro 19 archive | Open Data File |
| `claris-fm19-step-read-from-data-file` | primary | FileMaker Pro 19 archive | Read from Data File |
| `claris-fm19-step-write-to-data-file` | primary | FileMaker Pro 19 archive | Write to Data File |
| `claris-fm19-step-close-data-file` | primary | FileMaker Pro 19 archive | Close Data File |
| `claris-fm19-step-get-file-exists` | primary | FileMaker Pro 19 archive | Get File Exists |
| `claris-fm19-step-delete-file` | primary | FileMaker Pro 19 archive | Delete File |
| `claris-fm19-function-get-scriptparameter` | primary | FileMaker Pro 19 archive | Get ( ScriptParameter ) |
| `claris-fm19-function-get-scriptresult` | primary | FileMaker Pro 19 archive | Get ( ScriptResult ) |
| `claris-fm19-function-get-lasterror` | primary | FileMaker Pro 19 archive | Get ( LastError ) |
| `claris-fm19-function-get-lastexternalerrordetail` | primary | FileMaker Pro 19 archive | Get ( LastExternalErrorDetail ) |
| `claris-fm19-function-get-applicationversion` | primary | FileMaker Pro 19 archive | Get ( ApplicationVersion ) |
| `claris-fm19-function-get-hostapplicationversion` | primary | FileMaker Pro 19 archive | Get ( HostApplicationVersion ) |
| `claris-fm19-function-get-systemplatform` | primary | FileMaker Pro 19 archive | Get ( SystemPlatform ) |
| `claris-fm19-function-get-username` | primary | FileMaker Pro 19 archive | Get ( UserName ) |
| `claris-fm19-function-get-accountname` | primary | FileMaker Pro 19 archive | Get ( AccountName ) |
| `claris-fm19-function-get-accountprivilegesetname` | primary | FileMaker Pro 19 archive | Get ( AccountPrivilegeSetName ) |
| `claris-fm19-function-get-layoutname` | primary | FileMaker Pro 19 archive | Get ( LayoutName ) |
| `claris-fm19-function-get-layouttablename` | primary | FileMaker Pro 19 archive | Get ( LayoutTableName ) |
| `claris-fm19-function-get-foundcount` | primary | FileMaker Pro 19 archive | Get ( FoundCount ) |
| `claris-fm19-function-get-recordid` | primary | FileMaker Pro 19 archive | Get ( RecordID ) |
| `claris-fm19-function-get-recordnumber` | primary | FileMaker Pro 19 archive | Get ( RecordNumber ) |
| `claris-fm19-function-get-recordopenstate` | primary | FileMaker Pro 19 archive | Get ( RecordOpenState ) |
| `claris-fm19-function-get-temporarypath` | primary | FileMaker Pro 19 archive | Get ( TemporaryPath ) |
| `claris-fm19-function-get-documentspath` | primary | FileMaker Pro 19 archive | Get ( DocumentsPath ) |
| `claris-fm19-function-get-documentspathlisting` | primary | FileMaker Pro 19 archive | Get ( DocumentsPathListing ) |
| `claris-fm19-function-jsongetelement` | primary | FileMaker Pro 19 archive | JSONGetElement |
| `claris-fm19-function-jsonsetelement` | primary | FileMaker Pro 19 archive | JSONSetElement |
| `claris-fm19-function-jsonlistkeys` | primary | FileMaker Pro 19 archive | JSONListKeys |
| `claris-fm19-function-jsonlistvalues` | primary | FileMaker Pro 19 archive | JSONListValues |
| `claris-fm19-function-jsonformatelements` | primary | FileMaker Pro 19 archive | JSONFormatElements |

| `claris-fm19-cumulative-function-get-lasterrordetail` | primary | Cumulative FileMaker 19 help, including post-19.5 additions | Get(LastErrorDetail) |

## 8.1 出典の信頼区分

- `primary + archived`: 19.5判断の第一候補
- `primary + active`: originated version、後続版transition、現行code意味の確認
- `secondary`: 探索、patch候補、public fixture observationのみ
- `device evidence`: source registryとは別のverification recordに保存

---

# 9. 機械可読カタログ候補

## 9.1 改訂したデータモデル

初版の単一`execution.server`では不十分だった。改訂版は次を分離した。

- `introducedIn`
- `serverSupportIntroducedIn`
- context別compatibility
- `options`
- `versionTransitions`
- `compatibilityBasis`
- `fmxmlsnippet.stepId = null`
- `confidence`
- `evidence`
- `sourceIds`

## 9.2 生成器の推奨ルール

```text
availableIn19_5 != true       -> reject
execution[target] == false    -> reject
execution[target] == null     -> reject
execution[target] == partial  -> require matching option rule
sourceIds empty               -> reject
later-version transition only -> reject
fmxmlsnippet stepId null      -> XML renderer reject
missing 19.5 fixture          -> XML renderer reject
destructive step              -> require target-count/idempotency guard
```

## 9.3 既存リポジトリカタログとの関係

既存`catalog/fm19.5/verified-steps.json`はrendererと数値IDを同期する用途であり、今回のresearch candidate catalogとは役割が異なる。

- research catalog: 互換性、出典、option、risk、unknownを保持
- verified renderer catalog: 19.5 fixtureから得た数値IDと構造だけを登録
- research上の`documented`だけではrenderer登録不可
- DDR XMLのIDをrenderer IDへ転記不可

---

# 10. 不明・矛盾・追加確認事項

| ID | 領域 | 優先度 | 状態 | 問い |
|---|---|---|---|---|
| `uq-official-19-5-patch-release-notes` | versioning | critical | secondary-evidence-only | Recover the official Claris release notes for FileMaker Pro/Server 19.5.1, 19.5.2, 19.5.3, and 19.5.4 and freeze patch-level deltas. |
| `uq-psos-parameter-result-limit` | execution-model | high | device-test-required | Confirm the exact FileMaker Server 19.5.x limit for PSOS script parameters and script results, including multibyte-character counting. |
| `uq-schedule-2048-vs-runtime-limit` | execution-model | high | document-reconciliation-and-device-test | Reconcile the Admin Console limit for script name plus parameters with the larger script parameter/result limit. |
| `uq-global-field-initial-values` | session-state | critical | device-test-required | What exact values do global fields expose at the start of PSOS and server-schedule sessions in 19.5.4, including multi-file solutions? |
| `uq-global-variable-lifetime-isolation` | session-state | critical | device-test-required | Confirm $$variable lifetime and isolation across Perform Script, PSOS, nested PSOS, schedule, file open/close, and server process restart. |
| `uq-related-file-authentication` | security | critical | device-test-required | Map account/privilege behavior when PSOS or a schedule accesses related FileMaker files with different account sets, external authentication, or authorized-file restrictions. |
| `uq-script-triggers-fmse-matrix` | execution-model | critical | document-and-device-test | Which file, layout, record, and object script triggers fire—or do not fire—during PSOS and server schedules in 19.5.4? |
| `uq-admin-cancel-timeout-atomicity` | cancellation | critical | device-test-required | What state remains when an administrator stops FMSE or a schedule timeout occurs during record edits, file writes, imports, or outbound requests? |
| `uq-schedule-overlap-and-queueing` | concurrency | critical | device-test-required | Confirm 19.5.4 behavior when a schedule's next run begins before the previous run completes and when PSOS session capacity is exhausted. |
| `uq-plugin-server-compatibility` | plugins | critical | vendor-and-device-test | For each intended plug-in, which exact version/OS build is server-enabled, FMSE-compatible, thread-safe, and licensed for Server 19.5? |
| `uq-odbc-driver-dsn-matrix` | odbc | critical | vendor-and-device-test | Freeze the supported 64-bit ODBC driver, version, DSN type, authentication, Unicode behavior, and transaction behavior for each external source. |
| `uq-webdirect-desktop-mobile-matrix` | webdirect | high | document-and-device-test | Complete desktop-browser versus mobile-browser option-level compatibility for every high-priority step. |
| `uq-fmxmlsnippet-19-5-fixtures` | fmxmlsnippet | critical | fm19-5-device-only | Capture FileMaker Pro 19.5-origin clipboard XML for all admitted steps and option combinations. |
| `uq-ddr-id-versus-clipboard-id` | fmxmlsnippet | critical | comparative-device-test | Determine whether any DDR XML step IDs coincide with clipboard fmxmlsnippet IDs for 19.5 without assuming equivalence. |
| `uq-data-file-handle-limits-cleanup` | data-file | high | device-test-required | Confirm open-handle limits, cleanup on Exit Script/Halt/error/timeout, and concurrent access semantics for data-file steps in 19.5.4. |
| `uq-path-os-permission-atomicity` | paths | high | environment-test-required | Record exact Windows/Linux/macOS server path forms, service-account permissions, Unicode filenames, overwrite behavior, and rename/replace atomicity. |
| `uq-pdf-font-rendering` | output | high | environment-test-required | Verify fonts, print setup, page geometry, container rendering, locale, and concurrent PDF filename behavior on the target Server 19.5 OS. |
| `uq-execute-data-api-19-5-inner-context` | data-api | critical | device-test-required | Confirm 19.5.4 request envelope limits, hidden-window layout context, privilege behavior, and result/error semantics for read/metaData actions. |
| `uq-error-code-freeze-19-5` | errors | high | archival-source-required | Freeze an exact FileMaker 19.5-era error-code table rather than relying on the cumulative current table for every code. |

| `uq-last-error-detail-name-boundary` | functions-versioning | critical | official-release-note-required | Confirm from official Claris 19.5/19.6.1 release documentation when Get ( LastExternalErrorDetail ) was renamed or replaced by Get ( LastErrorDetail ), and whether both names coexist in any 19.x patch. |

## 10.1 探査範囲監査

| 領域 | 状態 | 判定 |
|---|---|---|
| FMSE session and state inheritance | covered | Primary archived help plus unresolved edge-case tests. |
| PSOS invocation/result/cancellation | covered-with-open-tests | Core behavior documented; size and cancellation atomicity unresolved. |
| Server schedules/account/timeout/logging | covered-with-open-tests | Core behavior documented; overlap and exact limits require tests. |
| Client/PSOS/schedule/WebDirect/Go/Data API/CWP matrix | covered-conservatively | All requested steps classified; Partial remains option-sensitive. |
| High-priority 51 requested steps | covered | Every requested step has a specific archived source candidate. |
| Additional server-safe data-file steps | newly-covered | Seven FileMaker 18+ data-file steps added as important alternatives. |
| Functions requested | covered | All requested Get/JSON functions cataloged. |
| Error codes | corrected-and-expanded | Error 3/4 separated; ODBC/file/API codes corrected and expanded. |
| 19.5-excluded later features | expanded | Transactions, callback, AI, Data API expansions, Get function, server compatibility transitions. |
| 19.5.x patch differences | partially-covered | Secondary evidence found; official Claris originals remain unresolved. |
| fmxmlsnippet | classified-not-resolved | DDR XML, public observations, and 19.5 clipboard evidence are separated. |
| Plug-ins | classified-not-resolved | Vendor and device matrix required. |
| ODBC/ESS | covered-with-environment-tests | Generic rules covered; specific drivers/sources unresolved. |
| Related files and privilege propagation | classified-not-resolved | Device fixture required. |
| Script triggers | newly-identified-unresolved | Material hidden side-effect domain absent from initial report. |
| Concurrency/idempotency/overlap | newly-expanded | Operational risks classified; exact 19.5 behavior requires tests. |
| Output fidelity/PDF/fonts | newly-identified-unresolved | Compatibility alone is insufficient. |

| LastExternalErrorDetail / LastErrorDetail naming boundary | newly-identified-critical-version-boundary | Older official help and cumulative FileMaker 19 help use different names; exact 19.5/19.6.1 boundary is now an explicit blocker. |

この監査により、初版で未探査だった重要領域として、data-file step、script trigger、Server対応追加版、error 3/4差、DDRとclipboard XMLの分離、schedule overlap、停止時atomicity、PDF fidelityを追加した。

---

# 11. FileMaker実機でしか確認できない事項

1. FileMaker Pro 19.5でcopyした生のclipboard formatと`fmxmlsnippet`
2. Pro 19.5へのpaste roundtrip
3. step optionを変更した際のXML差分
4. DDR XMLとclipboard XMLの同一step比較
5. PSOS/scheduleのglobal field初期値
6. `$`・`$$`変数のnested session分離
7. related fileのaccount/privilege
8. script triggerの発火
9. unknown stepと`Allow User Abort`
10. administrator stop、timeout、host disconnect時のcommit状態
11. schedule overlapとsession capacity
12. plug-inのload・並列・restart
13. ODBC driver/DSN/Unicode/transaction
14. WebDirect desktop/mobile
15. Data API read/metaDataの権限・layout・result
16. Japanese filename/path
17. interrupted file write
18. PDF font/layout fidelity
19. 19.5.1〜19.5.4の差
20. Server OS別の挙動

実機記録に必要なmetadata:

```json
{
  "fileMakerProVersion": "19.5.x",
  "fileMakerServerVersion": "19.5.x",
  "clientOs": "",
  "serverOs": "",
  "executionMode": "client | psos | server_schedule | webdirect",
  "fixtureSha256": "",
  "databaseSha256": "",
  "testedAt": "YYYY-MM-DD",
  "tester": "",
  "account": "",
  "privilegeSet": "",
  "testCase": "",
  "expected": "",
  "actual": "",
  "eventLogExcerpt": "",
  "evidenceFiles": []
}
```

---

# 12. 推奨するリポジトリへの反映順序

1. `research/issue-7/`へ今回の4成果物とcoverage auditを保存
2. source registry schemaを`relevantSections`対応へ拡張するか、候補から既存schemaへ正規化
3. research catalog用schemaを新設
4. `introducedIn`と`serverSupportIntroducedIn`を分離
5. contextをclient/psos/serverSchedule/WebDirect/Go/Data API/CWPに分離
6. WebDirect desktop/mobile拡張点を予約
7. `Partial`のoption rule必須化
8. error catalogを追加
9. function catalogを追加
10. later-version exclusion catalogを追加
11. `Set Error Logging`、PDF/Data API、Export Field Contentsのcompatibility transition testをCIへ追加
12. `fmxmlsnippet.stepId` nullを許すresearch schemaと、nullを拒否するrenderer schemaを分離
13. DDR sourceをclipboard evidenceとして使用した場合にCI failure
14. public fixtureだけで`fm19_5_paste_verified`を付与した場合にCI failure
15. 19.5実機fixture取得
16. 最小stepからrenderer catalogへ昇格
17. FMSE実行fixture取得
18. Markdown生成
19. source URL availability、duplicate ID、orphan source、later-version contaminationをCI検査
20. Issue #7のacceptance criteriaに対応するcoverage reportをCI生成

---

# 暫定結論

改訂後の成果物は、初版より明確に厳格になった。重要なのは「全項目を埋めた」ことではなく、**資料で確定できる項目、後続版transition、環境依存、19.5実機だけで確定できる項目を分離したこと**である。

現時点でIssue #7のresearch seedとして採用可能だが、rendererのverified catalogへ直接転記してよいのは、FileMaker Pro 19.5 fixtureと必要なruntime evidenceを得た項目だけである。

---

---

## 機械可読成果物

- `source-registry-candidates.json`
- `script-step-catalog-candidates.json`
- `unresolved-questions.json`
- `coverage-audit.json`
- `manifest.json`

これらはresearch candidateであり、既存のverified renderer catalogへ直接転記しない。
