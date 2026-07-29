# 目的と責任範囲

## 一文での定義

本リポジトリは、Microsoft 365 Copilot等のAIが社内のFileMakerシステム情報と組み合わせ、FileMaker担当者がScript Workspaceへ手作業で実装できる、FileMaker Server 19.5向けの完全な人間向けスクリプト設計書を生成するための公開知識、判断、実用パターンの正本である。

## 正式成果物

正式成果物は、人間向けスクリプト設計書です。

設計書は、使用するFileMakerオブジェクト、実行コンテキスト、入出力、FileMaker形式のステップと設定、エラー分岐、Commit／Revert、ロック、冪等性、セキュリティ、未解決事項、レビュー項目、テスト項目を含みます。FileMaker担当者が内容を確認し、Script Workspaceへ手作業で実装します。

XML、Script IR、clipboardは正式成果物ではありません。既存機能は凍結された実験的な副次機能として保持します。

## 担う役割

- FileMaker Server 19.5の実装知識を提供する。
- client、PSOS、server schedule、WebDirect等から実行コンテキストを選択する基準を示す。
- 実行コンテキストごとの差を示す。
- FileMaker 19.5より後に追加された機能を除外する。
- 安全なエラー処理、Commit、Revert、レコードロック、再試行、冪等性、セキュリティを示す。
- AIが社内文書から必要なオブジェクト、業務、権限、要求を取得する手順を示す。
- 必須情報が不足したときの停止条件と、draft designで残す未解決事項を示す。
- 人間向け設計書の出力形式とimplementation-readyの条件を定義する。
- FileMaker担当者によるレビューとテスト項目を示す。
- FileMaker Pro／Server 19.5実機未検証の状態を明示する。

## 担わない役割

- 社内固有のテーブル、TO、フィールド、レイアウト、スクリプト、業務、権限、命名規則、既存仕様、要求の公開保管
- M365 CopilotからFileMakerへの直接書込み
- FileMakerソリューション全体の自動操作
- `.fmp12`ファイルの管理
- FileMaker Serverの運用監視、バックアップ、アカウント管理
- 220ステップのXML仕様の独自再構築
- FileMaker最新版への継続追従
- 実機テストの代替
- FileMaker Pro／Server 19.5実機未検証XMLの正しさの保証
- XMLを正式成果物とすること

## 情報の分担

### 公開GitHub

このリポジトリを、FileMaker Server 19.5の一般知識、互換性、設計ルール、判断、実用パターンを編集・レビューする正本とします。

後続PRで、M365 Copilotが参照する範囲を短いMarkdownへ限定します。`docs/copilot/`はまだ作成されていません。

### 社内SharePoint

対象システム固有のオブジェクト、業務フロー、権限、命名規則、既存仕様、実装要求を管理します。

公開知識の配布領域とは、別ライブラリまたは明確に分離された領域にします。GitHubの公開知識へ社内情報を逆流させません。

### Microsoft 365 Copilot

後続PRで公開GitHubからSharePointへ限定配置する知識と、社内SharePointの対象システム情報を組み合わせ、人間向けスクリプト設計書を生成する役割です。

Copilotの出力は人間レビューを必須とします。FileMakerへ直接書き込まず、FileMaker担当者がScript Workspaceへ手作業で実装してテストします。
