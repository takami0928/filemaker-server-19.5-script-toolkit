# Contributing

1. 対象はFileMaker Server / Pro 19.5に固定する。
2. 新しいステップテンプレートには、FileMaker Pro 19.5から取得した最小XMLフィクスチャを付ける。
3. XMLを手書き推測だけで追加しない。
4. 対応環境、入力、出力、失敗時挙動を文書化する。
5. 社内情報を含めない。
6. `python scripts/check_repository.py`と`python -m unittest discover -s tests -v`を通す。
7. Windowsクリップボード変更は、実機でcopy/read/write/pasteの往復を確認する。
8. Script IR変更ではv1/v2検証、決定的移行、v1/v2レンダリングを確認し、未知のFileMaker内部IDを追加しない。
