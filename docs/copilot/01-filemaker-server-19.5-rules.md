# FileMaker Server 19.5規則

以下は、FileMaker Server 19.5向け設計で常に守る規範です。

1. targetをFileMaker Pro 19.5／FileMaker Server 19.5へ固定する。
2. current helpまたは後続版で利用できる機能を19.5へ遡及しない。
3. compatibility catalogのsupportとXML renderer statusを別々に扱う。`available`はXML生成可能または実機検証済みを意味しない。
4. `available`は対象contextで資料上利用可能、`unavailable`は採用禁止、`partial`は記録された条件の解決必須、`unknown`は根拠不足としてfail closedとする。
5. `partial`を単純な`available`へ読み替えない。採用するoptionと解決した条件を設計書へ残す。
6. server処理がclientのlayout、current record、found set、sort order、local/global variable、global fieldを引き継ぐと仮定しない。
7. server側で必要なfile、layout、TO、record、found setを明示的に再構築する。
8. server処理ではUI操作、interactive pause、dialogを前提にしない。dialog optionは対象contextの条件に従う。
9. object name、internal ID、privilege、relationship、business ruleを推測しない。
10. delete、replace、bulk update等の破壊的処理は対象範囲、権限、復旧方法を明示し、曖昧なfound setで実行しない。
11. 候補stepは、全文を複製せず[59-step compatibility catalog](../COMPATIBILITY_CATALOG.md)の正本でcontext別に確認する。
12. evidenceは設計状態、XML処理、paste、client runtime、FMSE runtimeを分離して[正規報告形式](../EVIDENCE_MODEL.md#repository-wide-completion-reporting)で示す。CI成功をFileMaker実機証拠へ昇格しない。

FileMaker Pro／Server 19.5の実機試験を行っていない場合、paste、client runtime、FMSE verificationはそれぞれ`not_run`と明記します。

## Source IDs

Source IDs: `claris-fm19-script-steps-reference`, `claris-fm19-running-scripts-on-server`
