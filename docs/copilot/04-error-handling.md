# Error handling

## 基本順序

1. 失敗し得る重要stepを実行する。
2. 直後の`Set Variable`等で`Get ( LastError )`を保存する。
3. error取得前に別stepを挟まない。
4. 保存したFileMaker errorとapplication側の判定を別々に分類する。
5. normal pathとerror pathの双方で共通JSON resultを返す。

未知のerror code、FileMaker 19.5で裏付けられていない番号や意味を捏造しません。numeric errorを設計へ使う場合は、既存patternのsource-backed候補または登録済みsourceへ境界を示します。current error表だけを根拠に19.5固有動作を保証しません。

## Common result contract

正本は[`common-result.schema.json`](../../patterns/fm19.5/common-result.schema.json)です。新しいschemaを作らず、次のfieldをその定義どおり使います。

- `ok`: successかfailureか
- `code`: callerが判定するapplication code
- `message`: user-facingな短いmessage
- `data`: 承認されたresult data
- `error`: `null`または`fileMakerCode`、`step`、`details`
- `meta`: 使用patternとschema version

FileMaker errorは`error.fileMakerCode`へ保持し、業務上のapplication codeは`code`へ置きます。user-facing messageにcredential、raw parameter、機密field値、内部診断を含めません。diagnostic detailは必要最小限とし、access-controlledな記録へ分離します。

## Branch rules

- validation failure、not found、privilege failure、lock／conflict、Commit failure、PSOS call failureを同じcodeへ潰さない。
- error branchは、必要なcleanupとRevert方針を実行・確認してから`Exit Script`で終了する。
- cleanup自体が失敗した場合は、元errorとcleanup failureを区別して人間へ確認を要求する。
- `Commit Records/Requests`の直後でerrorを保存し、nonzeroならsuccess resultを返さない。
- PSOS callerは、`Perform Script on Server`直後のcall errorと`Get ( ScriptResult )`のbusiness resultを分離する。
- PSOS resultが空、malformed、または共通contract外なら、server business successを推測しない。

## Source IDs

Source IDs: `claris-fm19-script-steps-reference`, `claris-fm19-function-get-lasterror`, `claris-fm19-function-jsonsetelement`, `claris-fm19-function-get-scriptresult`, `claris-current-error-codes`
