# 目的とscope

## Formal output

formal outputは、FileMaker担当者がFileMaker Pro 19.5のScript Workspaceへ上から順に手作業実装できる、人間向けスクリプト設計書です。設計書の正規構造は[output contract](09-output-contract.md)で定義します。

## Public knowledge responsibilities

このpackageは次を担当します。

- FileMaker Server 19.5の一般知識
- execution contextの選択基準
- 安全でreviewしやすいscript style
- error、record lock、Commit、Revert、retry、idempotencyの設計基準
- FileMaker 19.5より後の機能を除外する手順
- 人間向け設計書のoutput contract
- 人間によるreviewとtestの手順

## Internal context responsibilities

対象システム側は、少なくとも次の確定情報を別管理します。

- table
- table occurrence（TO）
- field
- layout
- existing script
- privilege
- naming rule
- workflow
- implementation requirement

必要情報の分類と停止条件は[required internal context](08-required-internal-context.md)を使用します。公開packageへ実データを転記しません。

## Non-goals

- XMLをformal outputとすること
- Copilotまたは本packageからFileMakerへ直接書き込むこと
- FileMakerソリューション全体を自動生成すること
- 実機未検証状態を隠すこと
- 社内情報を公開repositoryへ保管すること
- FileMaker 20以降へ対応すること
- SharePoint接続、配布package、pilot、受入試験を実装すること
- Copilot出力の正しさを無条件に保証すること

## 境界

このpackageは、repository-wideの[目的と責任範囲](../PURPOSE.md)、[AI利用契約](../../AI_GUIDE.md)、[証拠モデル](../EVIDENCE_MODEL.md)を、Copilotが読む範囲へ圧縮したものです。矛盾が疑われる場合はこれらの正本へ戻り、推測で埋めません。
