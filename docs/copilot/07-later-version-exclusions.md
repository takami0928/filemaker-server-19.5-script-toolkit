# Later-version除外

targetはFileMaker Pro 19.5／FileMaker Server 19.5です。この文書はlater-version featureの完全一覧ではなく、混入を防ぐ判断手順です。

## 判断手順

1. candidate stepのexact English nameをcompatibility catalogで検索する。
2. `availableIn19_5`、`introducedIn`、対象contextのsupportを確認する。
3. server処理では、step自体の`introducedIn`とserver対応の`serverSupportIntroducedIn`を分離する。
4. `unavailable`は採用せず、`unknown`はfail closedとする。`partial`は19.5で成立するoptionと条件を解決する。
5. current Claris helpを19.5の根拠として自動使用しない。archived 19 sourceまたはversion transitionを確認する。
6. release noteが後続版でserver対応追加を示す場合、その機能を19.5のPSOS／server scheduleへ遡及しない。
7. external upstreamを参照する場合は、その対象FileMaker version、license、evidence境界を[ADR 0004](../../decisions/0004-adopt-copilot-first-knowledge-package.md)で確認する。
8. FileMaker 21+向けimplementation、FileMaker 2024以降中心のXML情報を19.5設計へコピーしない。
9. XML specification repositoryのpaste実績、current productでの成功、CI成功をFileMaker 19.5 evidenceへ昇格しない。
10. 除外判断に必要なversion事実を既存sourceで解決できない場合、候補を使わず`draft_design`で停止する。

後続版で追加されたtransaction stepsやcallback付きPSOSは、既存registryが19.5対象外と記録しています。これは完全な後続版一覧ではなく、既知の除外例です。

## Source IDs

Source IDs: `claris-fm19-script-steps-reference`, `claris-pro-release-notes`, `claris-server-release-notes-20-1-1`, `claris-open-transaction`, `claris-commit-transaction`, `claris-revert-transaction`, `claris-psos-callback`
