# Issue #7 — FileMaker Server 19.5 Deep Research

## 調査目的

FileMaker Server 19.5 / FileMaker Pro 19.5 のサーバー実行境界、スクリプトステップ、関数、エラー、バージョン差分、XML provenance を公開情報から整理し、実装候補と未解決事項を機械可読にするための調査成果物です。

このディレクトリの内容はすべて `research-candidate` です。`catalog/fm19.5/verified-steps.json` のverified renderer catalogとは分離されており、FileMaker Pro 19.5 paste evidenceやFileMaker Server 19.5 FMSE runtime evidenceを示しません。

## 正本とmanifest

調査結果の正本は [`candidates/`](candidates/) にある通常のUTF-8ファイルです。GitHub、ChatGPT、Codex、人間が直接検索、diff、レビューできます。

- [`manifest.json`](manifest.json): リポジトリに保存した7ファイルのpath、bytes、SHA-256、件数、evidence境界
- [`candidates/manifest.json`](candidates/manifest.json): 6個の調査内容ファイルに対する候補セット内部のmanifest

外側manifestは `candidates/manifest.json` 自体も検証対象にします。内側manifestは循環参照を避けるため、自身のhashを持ちません。同じ調査内容を別の場所へ正本として複製しません。

## 成果物

- [`candidates/deep-research-report.md`](candidates/deep-research-report.md): 完全なDeep Researchレポートと設計上の結論
- [`candidates/source-registry-candidates.json`](candidates/source-registry-candidates.json): 110件の出典候補
- [`candidates/script-step-catalog-candidates.json`](candidates/script-step-catalog-candidates.json): 59ステップ、24関数、117エラー、15件の後続版除外／遷移
- [`candidates/unresolved-questions.json`](candidates/unresolved-questions.json): 20件の未解決事項と検証計画
- [`candidates/coverage-audit.json`](candidates/coverage-audit.json): 18領域の探索範囲監査
- [`candidates/revision-notes.md`](candidates/revision-notes.md): 改訂内容と検査結果
- [`candidates/manifest.json`](candidates/manifest.json): 候補セット内部の件数とファイル整合性

## 件数

| 項目 | 件数 |
| --- | ---: |
| sources | 110 |
| steps | 59 |
| requested high-priority steps | 51/51 |
| additional audited steps | 8 |
| functions | 24 |
| errors | 117 |
| exclusions/transitions | 15 |
| unresolved questions | 20 |
| coverage domains | 18 |

自動検査では、source ID、step name、unresolved IDの重複、未知source参照、coverage auditからのunresolved参照切れ、clipboard `fmxmlsnippet`数値IDの断定も拒否します。

## Evidence boundary

- 公開文書による互換性調査は、FileMaker実機証拠ではありません。
- public fixtureは `public_fixture_observed` 相当までで、FileMaker Pro 19.5由来fixtureとして扱いません。
- DDR XMLの数値IDをclipboard `fmxmlsnippet` IDへ転用しません。
- `introducedIn` と `serverSupportIntroducedIn` を分離し、後続版で追加されたServer対応を19.5へ遡及しません。
- `partial` はoption-levelの説明または明示的な互換性ルールを必要とし、`unknown` はdeny-by-defaultです。
- CI成功をpaste、runtime、FMSE evidenceへ昇格しません。

## Verifiedへの昇格条件

候補をverified renderer catalogへ昇格するには、少なくとも次が必要です。

1. 対象claimを支える登録済みsourceと19.5境界の確認
2. FileMaker Pro 19.5で取得したprovenance-aware fixture
3. raw fixtureのSHA-256、取得環境、取得日時、取得者、再現手順
4. paste round-tripと、必要な場合はruntime/FMSEの期待値・実測値
5. `docs/EVIDENCE_MODEL.md` の前提証拠を満たすverification record
6. 独立レビューとverified catalog向けの別変更

調査候補をこのPRからverified catalogへ直接コピーしません。

## 最優先の未解決事項

- FileMaker Pro 19.5由来のclipboard `fmxmlsnippet` fixture取得とDDR IDとの比較
- FileMaker Pro/Server 19.5.x公式patch release notesの回収
- PSOS／scheduleのsession state、global値、関連ファイル認証、trigger挙動
- cancellation、timeout、schedule overlap、session capacityの実機確認
- `Get ( LastExternalErrorDetail )` と `Get ( LastErrorDetail )` の正確な版境界
- Execute FileMaker Data API、plug-in、ODBC、OS path／permissionの環境別実証

全20件のID、リスク、検証計画は [`candidates/unresolved-questions.json`](candidates/unresolved-questions.json) にあります。

## 次工程

1. archived primary sourceと公式19.5.x release notesを補完する
2. FileMaker Pro 19.5のprovenance-aware fixtureを最小ステップから取得する
3. unresolved question単位でFileMaker Pro／Server 19.5実機検証を行う
4. 証拠が揃った項目だけを別PRで正規schemaとverified catalogへ昇格する
5. renderer、parser、round-trip testへ段階的に接続する

`python -m fms19_toolkit.research_policy .` または `python scripts/check_repository.py` で、ファイル、manifest、件数、参照、互換性上の安全規則を再検査できます。
