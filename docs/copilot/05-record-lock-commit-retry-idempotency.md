# Record lock、Commit、retry、idempotency

## 用語を分ける

- record lock: sessionがrecordを編集可能な状態にできるか。
- conflict: 別sessionの編集、version不一致、Commit時の同時変更等により、要求した更新を安全に確定できない状態。
- Commit: 現在の変更を確定し、直後のerrorを確認する処理。
- Revert: review済み方針に基づき、current recordの未Commit変更を破棄する処理。
- retry: 明示した対象failureに対して、全contextと意図を再評価して有限回だけ再試行すること。
- idempotency: 同じlogical requestを再実行しても副作用を重複させない性質。
- optimistic version check: callerが確認したversionと更新直前のversionを比較する競合検出。
- duplicate request prevention: request ID等を既存fieldへ記録し、処理済み要求を再適用しない設計。

## 設計規範

1. recordを開けない、またはlockを取得できない結果をsuccessとして扱わない。
2. `Commit Records/Requests`直後のerrorを保存し、zeroを確認するまで更新成功としない。
3. failure時に`Revert Record/Request`が必要かをbranchごとに決める。Revertが破棄する値とcleanup failureも扱う。
4. retry回数は有限とし、最大回数、対象error、各attemptで再取得するcontext、exhaustion resultを記載する。
5. retry前に同じ入力がすでに副作用を起こした可能性を評価する。completion不明のwriteを盲目的に再実行しない。
6. idempotency key／field、version fieldが対象fileに存在すると推測しない。
7. optionalなidempotency、version check、auxiliary layoutを採用しない場合は、省略内容、duplicate／lost-update risk、将来確認事項を記録する。
8. optional機能を採用すると決めた時点で、そのfield、type、rule、calculation、privilegeはrequiredになる。
9. server scheduleは重複起動、前回未完了、手動再実行の可能性を確認し、request単位の重複防止または明示したrisk acceptanceを設計する。
10. destructive operationは、対象範囲、事前backup、compensation／recovery script、運用者への通知を明示する。

このpackageは、FileMaker Pro／Server 19.5実機でのlock、Commit、Revertの結果を保証しません。設計はsource-backedですが、対象fileのprivilege、validation、relationship、同時実行条件で手動testが必要です。

## Source IDs

Source IDs: `claris-fm19-step-open-record-request`, `claris-fm19-step-commit-records-requests`, `claris-fm19-step-revert-record-request`, `claris-fm19-running-scripts-on-server`, `claris-current-error-codes`
