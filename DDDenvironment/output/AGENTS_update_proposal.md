# AGENTS.md Update Proposal — DDD Prompt-Driven Cycle (2025-09-26)

## Intent
- 欲求→テキスト→コード→アプリのループを軽量に回し、欲求の言語化と意思決定へ集中する。
- 欲求ログと意思決定ログをプロジェクト/グローバル双方で鏡写し管理し、いつでも遡及できる状態を保つ。
- プロンプト毎にステートを抽象化・構造化し、ユーザーの脳内モデルを随時可視化する。
- 確定した実装をナラティブツリーへ反映し、コード階層と概念・根拠を同期させる。

## Operating Principles
- **欲求同期を最優先**: 各プロンプトで欲求の成熟度・意図を推定し、解釈を共有してOK/修正を得る。
- **意思決定は最大3件**: 1プロンプト内で扱う判断は3件以内に絞り、根拠を残す。超えそうなら確認を挟む。
- **過剰実装禁止**: 合意済みの欲求・意思決定を越える案や実装は行わない。ズレ感があれば即質問。
- **ログは鏡写し**: `memo.md` / `Dialogue.md` / `DESIRE.md` はグローバルと `<project>//` 配下を同内容で更新し、時系列を崩さない。
- **自己改善を循環**: `self_improvement.md` の気づきを踏まえ、記録フォーマットと応答の簡潔さを常に点検する。

## Log System (必要最低限の更新項目)
- `memo.md` / `<project>/memo.md`: 日時・原文・トピック・欲求要約を記録。抜けがないか二重チェック。
- `DESIRE.md` / `<project>/DESIRE.md`: 欲求サマリーのみ。DesireIDや成熟度ラベルがある場合は併記。
- `Dialogue.md` / `<project>/Dialogue.md`: 解釈、実行計画、自己評価、必要に応じ質問。実装後は0–100評価と根拠を追記。
- `<project>/startkit/tasks/`: Dump締め時に `generate_tasks.py` で更新するタスクバンドル（`tasks-*.json`, `latest.json`）。
- `<project>/startkit/state/`: プロンプト受信毎に `generate_state.py` で更新するステート（`latest.json`, `latest.md`, `viewer/`, `history/`）。
- `<project>/startkit/narrative/`: タスク完了＆確定コードコミット後に `generate_narrative.py` で更新するナラティブツリーとスナップショット。
- `<project>/startkit/reports/`: モジュールサイクル完了時に `template.md` でレポートを追加し、DecisionとADRをリンク。

## Execution Loop
1. **Prompt Sync**
   - 欲求・指示を受信したら `DESIRE/memo/Dialogue` を鏡写し更新。
   - `python3 <project>/startkit/tools/generate_state.py --project <project>` を実行し、ステートを最新化。

2. **Dump Phase（必要時）**
   - Dump/Extractor/Grouper/Scorer/Shepherd で論点整理（意思決定は≤3件）。
   - `python3 <project>/tools/generate_tasks.py --project <project> --output-dir <project>/startkit/tasks --viewer-dir <project>/startkit/viewer --update-viewer` を実行し、タスクを更新。
   - Dump完了後、必要に応じて再度 `generate_state.py` を走らせ整合チェック。

3. **Action Phase**
   - Stateの `next_hints` と `startkit/tasks/latest.json` を照合し、着手タスクを決定。
   - 実装を進め、**コミット時には以下4項目を記録**:
     1. プロンプト解釈（Why/What/Scope）
     2. 実行方法（採用アプローチ）
     3. 制約・理由（選択理由/前提）
     4. 実行結果・評価（テスト状況・所感）
   - タスク完了かつ確定コードがコミットされたら `python3 <project>/startkit/tools/generate_narrative.py --project <project>` を実行し、ナラティブツリーを更新。

4. **Review & Next**
   - `Dialogue.md` に実装ログ・評価・残課題を追記し、必要なら `reports/` を追加。
   - 新たな欲求が生まれたら再び **Prompt Sync** へ戻る。

## Support Modules（必要時のみ）
- **Dump**: ユーザーの思考を生のまま受け取り、決定と検討の境界を見える化する緩衝帯。
- **Extractor / Grouper / Scorer / Shepherd**: 既存モジュール（記述は維持）。
- **Task Bundle Generator**: Dump結果をタスクビューへ射影する連結レイヤー。
- **State Synthesizer**: ログを正規化し、クラスタリングとトピック命名でステートを更新。
- **Narrative Mirror**: コード階層をトラバースし、ナラティブノードを生成・更新。

## Task Bundle Schema
（既存記述を維持）

## Artifacts & Boundaries
- `startkit/context/`: 参照資料ハブ（既存記述）。
- `startkit/tools/`: `generate_tasks.py`, `generate_state.py`, `generate_narrative.py` などの支援スクリプト。
- `startkit/viewer/`: タスク viewer。ステート用 viewer は `startkit/state/viewer/` として管理。
- `startkit/tasks/`: タスクバンドルJSON/ビュー。
- `startkit/state/`: ステートJSON/Markdown/Viewer/History。
- `startkit/narrative/`: ナラティブツリーとスナップショット。
- `startkit/reports/`: モジュールレポート。
- グローバル対応時は「グローバルで作業しています」と明記。

## Communication Norms
（既存記述を維持）

## Self-Improvement Hooks
（既存記述を維持）

## 自己改善フロー
（既存記述を維持）

---
※本ドキュメントは反映案であり、ユーザー承認後に `AGENTS.md` へ適用する。
