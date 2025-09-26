# DDD1 — Desire Driven Development Ops Guide

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
- `<project>/startkit/tasks/`: Dump締め時に Extractor/Grouper/Scorer/Shepherd を内部実行し、結果を直接 `tasks-<timestamp>.json` と `latest.json` に書き出す。`viewer/index.html` へも同一JSONをインライン反映する。
- `<project>/startkit/state/`: プロンプト受信毎に `generate_state.py` で更新するステート（`latest.json`, `latest.md`, `viewer/`, `history/`）。
- `<project>/startkit/narrative/`: タスク完了かつ確定コードコミット後に `generate_narrative.py` で更新するナラティブツリーとスナップショット。
- `<project>/startkit/reports/`: モジュールサイクル完了時に `template.md` でレポートを追加し、DecisionとADRをリンク。

## Execution Loop
1. **Prompt Sync**
   - 欲求・指示を受信したら `DESIRE.md`・`memo.md`・`Dialogue.md` を鏡写し更新。
   - `python3 <project>/startkit/tools/generate_state.py --project <project>` を実行し、ステートを最新化。

2. **Dump Phase（必要時）**
   - Dump / Extractor / Grouper / Scorer / Shepherd をプロンプト内で実行し、意思決定は ≤3 件に留める。
   - 合意した論点をもとに `startkit/tasks/latest.json` を手動更新し、同内容を `tasks-<timestamp>.json` と `viewer/index.html` に反映する（フォーマットは「Task JSON Format」を参照）。
   - Dump完了後は必要に応じて `generate_state.py` を再実行し整合チェック。

3. **Action Phase**
   - Stateの `next_hints` と `startkit/tasks/latest.json` を照合し着手タスクを決定。
   - 実装を進め、コミット時には以下4項目を記録: 1. プロンプト解釈（Why/What/Scope） 2. 実行方法（採用アプローチ） 3. 制約・理由（選択理由/前提） 4. 実行結果・評価（テスト状況・所感）。
   - タスク完了かつ確定コードがコミットされたら `python3 <project>/startkit/tools/generate_narrative.py --project <project>` を実行しナラティブツリーを更新。

4. **Review & Next**
   - `Dialogue.md` に実装ログ・評価・残課題を追記し、必要なら `reports/` を更新。
   - 新たな欲求が生まれたら Prompt Sync へ戻る。

## Support Modules（必要時のみ）
- **Dump**: ユーザーの思考を生のまま受け取り、決定と検討の境界を見える化する緩衝帯。
- **Extractor**: Dumpから論点をすくい上げ、議論の足場を整える抽出レイヤー。
- **Grouper**: 抽出した論点をテーマや抽象度で束ね、依存関係を可視化する構造化レイヤー。
- **Scorer**: 価値・確度・コストのバランスを測り、優先順の仮説をつくる評価レイヤー。
- **Shepherd**: 優先順に沿ってタスクを前進させ、状態と決定事項を継続的に同期する運用レイヤー。
- **Task Bundle Composer**: Extractor/Grouper/Scorer/Shepherdの出力を統合し、JSONタスクバンドルへ整形する内部処理。
- **State Synthesizer**: ログを正規化し、クラスタリングとトピック命名でステートを更新。
- **Narrative Mirror**: コード階層をトラバースし、ナラティブノードを生成・更新。

## Task JSON Format
- ルート: `project`, `generated_at`, `generator`, `source_summary`, `tasks`
  - `generator` は `{ "agent": "codex", "version": "1.0" }` など現在の生成主体を記録。
  - `source_summary` は Dumpで参照したログやメモの概要（任意フィールド例: `"dump_window": "2025-09-26T12:00+09:00 → 2025-09-26T16:00+09:00"`）。
- `tasks[]` 各要素:
  - `slug`: 英小文字+ハイフンで構成するユニークID。
  - `title`: 利用者が理解しやすい短いタスク名。
  - `summary`: Extractorで抽出した要約。
  - `status`: `backlog` / `in-progress` / `resolved`。
  - `priority`: `{ "method": "ICE", "impact": int|null, "confidence": int|null, "effort": int|null, "score": float|null, "rank": int|null }`。
  - `cluster`: `{ "key": str|null, "label": str|null }`。
  - `dependencies`: 先行タスクの `slug` 配列。
  - `notes`: スコア理由や補足メモの配列。
  - `links`: `{ "extractor": [ ... ], "grouper": [ ... ], "scorer": [ ... ], "shepherd": [ ... ] }` とし、各要素は `{ "source": "memo.md:542", "excerpt": "..." }` のように出典を記録。

### JSON更新手順
1. `startkit/tasks/latest.json` を編集し、`generated_at` を最新時刻（ISO8601, 秒精度）へ更新。
2. 内容を `startkit/tasks/tasks-<timestamp>.json` に複製（ハイフン区切りのローカルタイムスタンプを推奨）。
3. `startkit/viewer/index.html` の埋め込みJSONも同内容で更新し、ビューから即参照できる状態を保つ。

## Artifacts & Boundaries
- `startkit/context/`: 参照資料や背景メモを集約する読み取り専用ハブ。指示がない限り編集しない。
- `startkit/tools/`: `generate_state.py`・`generate_narrative.py` を配置。`generate_tasks.py` は廃止（参照のみ保存する場合は `deprecated/` へ退避）。
- `startkit/viewer/`: タスク viewer。ステート用 viewer は `startkit/state/viewer/` で管理。
- `startkit/tasks/`: タスクバンドル JSON / ビューを直接管理するディレクトリ。
- `startkit/state/`: ステート JSON / Markdown / Viewer / History。
- `startkit/narrative/`: ナラティブツリーとスナップショット。
- `startkit/reports/`: タスク終了時に目的・実行内容・結果のサマリーを書いたレポートを格納。
- グローバル対応時は「グローバルで作業しています」と明記。

## Communication Norms
- 口調はフレンドリーかつ簡潔。必要十分な説明と質問は最小限。
- 重要なコード・文書変更時はパスと要点を短く報告。
- すべての応答末尾に `DDDに沿って開発を進めています。` を添える。

## Self-Improvement Hooks
- ユーザーのフィードバックや摩擦点を観察し `self_improvement.md` に気づきと方針を追記。
- 必要があれば新しい運用案を提示し、承認後に `AGENTS.md`/関連文書へ反映する。

## 自己改善フロー
1. 観察: ユーザーの指示や反応から改善ポイントを抽出。  
2. 記録: `self_improvement.md` に気づきと方針を追加。  
3. 提案: 必要に応じて新しい `AGENTS.md` 案や運用案を提示。  
4. 更新: ユーザー許可を得てからの編集のみ実施。

