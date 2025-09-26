# DDD Prompt-Driven Cycle Flow（2025-09-26 13:49）

## コンセプト概要
- **State**: プロンプトを受信するたびに `generate_state.py` を走らせ、欲求・意思決定ログを即時クラスタリングして最新ステートを保持する。Dump/Actionフェーズに依存しない常時更新。
- **Tasks**: Dumpフェーズを締めるタイミングで `generate_tasks.py` により更新し、次アクションの土台を整える。
- **Narrative**: 確定したコードやドキュメントの変更がコミットされ、タスクが完了したタイミングで `generate_narrative.py` を実行し階層テキストを更新する。

```
   (各プロンプト)
        │
        ▼
┌──────────────────────┐
│ State Update (随時)   │  ← Desire / Decision / Evaluation を都度反映
└──────────────────────┘
        │
        ▼
┌─────────────┐ ┌─────────────────┐ ┌──────────────┐
│ Dump Intake │→│ Dump Processing │→│ Tasks Update │
└─────────────┘ └─────────────────┘ └──────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │ Action Planning  │
                        └──────────────────┘
                               │
                               ▼
                        ┌───────────────────────────────┐
                        │ Action Execution (コード/Docs) │
                        └───────────────────────────────┘
                               │  タスク完了 & コミット
                               ▼
                        ┌────────────────────┐
                        │ Narrative Update   │
                        └────────────────────┘
                               │
                               ▼
                        ┌───────────────┐
                        │ Action Review │
                        └───────────────┘
                               │
                               ▼
                          Dump再開
```

## フェーズ詳細
### Promptハンドリング（随時）
1. プロンプト受信→`DESIRE.md` `memo.md` `Dialogue.md` を鏡写し更新。
2. `generate_state.py` を起動し、最新ログからクラスタリング実施。
3. `startkit/state/latest.json` `latest.md` `viewer/` を上書きし、`insights` と `next_hints` を更新。

### Dumpフェーズ（必要に応じて開始）
1. **Dump Intake / Processing**: 論点抽出・意思決定（≤3件）。
2. **Tasks Update**: `python3 <project>/tools/generate_tasks.py --project <project> --output-dir <project>/startkit/tasks --viewer-dir <project>/startkit/viewer --update-viewer`。
3. Dump完了時には再度 `generate_state.py` を走らせ、Dumpの成果がStateにも反映されていることを確認。

### アクションフェーズ
1. **Action Planning**: `state/latest.json` と `tasks/latest.json` を照合して着手タスクを決定。
2. **Action Execution**: コード/ドキュメント編集。途中経過はgitブランチ上で管理。
3. **Gitコミット要件**（各コミット時にテキスト出力）:
   - プロンプト解釈（Why/What/Scope）
   - 実行方法（採用アプローチ）
   - 制約・理由（選択理由や前提条件）
   - 実行結果・評価（テスト状況・所感）
   ※コミットメッセージや付随レポートへ整形して保存。
4. **Narrative Update**: タスク完了で確定したコードを基に `generate_narrative.py` を実行。該当ディレクトリのノードを最新化し、State由来のトピック/insightsを埋め込む。
5. **Action Review**: `Dialogue.md` に実装ログ・評価・残課題を記入し、必要なら `reports/` を更新。次Dumpの種を `memo.md` に追記。

## 更新タイミングまとめ
| 更新対象 | トリガー | 用途 |
| --- | --- | --- |
| State `startkit/state/` | 各プロンプト受信時（追加でDump完了後確認） | 欲求・意思決定の即時クラスタリングと`insights`提示 |
| Tasks `startkit/tasks/` | Dumpフェーズ完了 | 行動計画のリスト化と優先度確認 |
| Narrative `startkit/narrative/` | タスク完了時（確定コードコミット後） | コード階層に紐づく概念・決定・根拠の記録 |

## オープンポイント
1. `generate_state.py` の再実行コスト削減（差分処理やキャッシュ戦略）。
2. `generate_narrative.py` が参照するStateスナップショットの選択（最終コミット時のStateを固定するか）。
3. コミット時の出力項目を自動テンプレ化する仕組み（pre-commitフック等）の設計。

---
次ステップ: `generate_state.py` のスキーマ・疑似コード、`generate_narrative.py` のテンプレート仕様、コミット用プロンプトテンプレートを整理する。
