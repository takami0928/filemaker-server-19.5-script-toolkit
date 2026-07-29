# 人間reviewとtesting

review可能な文書検査と、FileMaker環境がなければ実施できない検証を分離します。

## Public knowledge review

- Source IDsが両registryのいずれかに実在する。
- targetがFileMaker Pro／Server 19.5である。
- candidate stepを選択したcontextで確認している。
- FileMaker 20以降の機能を19.5へ混入していない。
- documented compatibility、design guidance、XML、自動検査、FileMaker evidenceを混同していない。
- 社内object、URL、credential、業務情報が公開packageへ漏れていない。
- relative linkが存在するfileを指している。

## Design review

- requirementとexpected side effectを満たす。
- required／optional／explicit omissionが分離されている。
- file、table、TO、field、layout、existing scriptが解決済みである。
- execution contextとcallerが適切である。
- input／result JSON contractが一致する。
- normal pathと全error pathが共通result contractへ収束する。
- record lockとCommit／Revert failureを扱う。
- retryは有限で、idempotencyまたは重複riskが明示されている。
- privilege、sensitive data、logging、destructive operationをreviewしている。

## Manual FileMaker implementation review

FileMaker Pro 19.5が利用可能になったら、FileMaker担当者が設計書をScript Workspaceへ手作業実装し、次を照合します。

- exact step option
- calculation syntax
- object reference
- privilege
- layout／TO context
- branch nestingと全`Exit Script` result

このreviewはpaste verificationまたはruntime verificationそのものではありません。

## Runtime testing when environment becomes available

対象contextごとに必要なcaseを実施します。

- `client`
- `psos`
- `server_schedule`
- 対象なら`webdirect`、`filemaker_go`、`data_api`、`custom_web_publishing`
- normal case
- malformed input
- record not found
- lock conflict
- privilege error
- Commit failure
- duplicate request
- retry exhaustion

exact FileMaker Pro／Server build、OS、test input、expected／actual result、tester、dateを[証拠モデル](../EVIDENCE_MODEL.md)に従って記録します。

## Completion report

次を省略せず別々に報告します。

```text
Design status: draft_design | implementation_ready
XML output: not_requested | not_generated | generated
Automated checks: not_run | passed | failed
Paste verification: not_run | passed | failed
Client runtime verification: not_run | passed | failed
FMSE verification: not_run | passed | failed
```

FileMakerファイルなしでもpublic knowledge reviewとdesign reviewは可能です。paste、calculation／object参照の実装照合、client runtime、PSOS／schedule runtimeは実機がなければ完了できません。CI成功をその代替にしません。
