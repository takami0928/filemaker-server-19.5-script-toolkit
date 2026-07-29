# Script style

Copilotは、FileMaker担当者がScript Workspaceで実装・reviewできるよう、次の規範で設計書を作ります。

## Header contract

各scriptについて次を先に固定します。

- script name
- purposeとprimary responsibility
- caller
- execution context
- parameter JSON contract
- result JSON contract
- required privilege
- side effect
- precondition

1 scriptは1つのprimary responsibilityへ限定します。UI、入力検証、server業務処理、永続化、表示を理由なく巨大な1 scriptへ混在させません。

## Step design

1. 使用variableを一覧化し、用途、初期値、scopeを示す。
2. server処理では、明示したparameterからcontextを再構築する。
3. field参照、find、create、updateの前に、対象layoutとbase TOへ明示的に移動する。
4. 対象recordは確認済みprimary keyで再検索し、0件／1件／複数件を分ける。
5. 失敗し得る重要stepの直後で`Get ( LastError )`を保存し、その前に別stepを挟まない。
6. success／errorの全経路で[共通result contract](../../patterns/fm19.5/common-result.schema.json)を使用する。
7. `If`／`Else`／`End If`の条件と終了結果を読み取れる粒度で書く。
8. delete、replace、bulk update等はdestructive operationとして対象範囲と復旧方法を明記する。
9. commentには、stepの言い換えではなくcontext再構築、error capture、retry停止条件等の理由を残す。
10. FileMaker internal IDをhard-codeまたは推測しない。設計書では確認済みobject nameを使う。

## Optional feature

optional featureは採用または省略を明記します。省略時は機能、影響、将来追加時の確認事項を記録します。採用したidempotency、version check、auxiliary layout等に必要な情報はrequiredへ変わり、未解決のまま`implementation_ready`にはできません。

既存の詳細規約は[FileMakerスクリプト作法](../SCRIPT_STYLE.md)を正本とし、この文書は設計書生成用の短い規範だけを示します。

## Source IDs

Source IDs: `claris-fm19-script-steps-reference`, `claris-fm19-running-scripts-on-server`, `claris-fm19-function-get-lasterror`
