# DDD State & Narrative Dump — 2025-09-26 13:31

> フェーズ: Dump（ステート管理 & ナラティブツリー）

## 1. 現状整理
- 直近ログを通じて、最終成果物はコード階層をミラーしたナラティブツリーで確定。
- ステートは「Desire・Decisionログを抽象化した脳内モデル」を狙いとし、Instructionsは含めない。
- 自動クラスタリングとトピック命名により、ユーザー自身が気づけていない状態変化を発見できる仕組みが求められている。

## 2. ステート表現のコンセプト
### 2.1 データソース
- `DESIRE.md`: 欲求サマリ。発生時刻、原文、成熟度タグ（任意）。
- `Dialogue.md`: 解釈・意思決定・自己評価ログ。決定内容や根拠を抽出可能。
- `memo.md`: Dump原文とトピック。欲求文脈の補足として扱う。

### 2.2 正規化ステップ
1. **エントリ抽出**: 各ログをパースし `desires[]`, `decisions[]` の候補を生成。
2. **メタ付与**: 日時、プロンプトID、関連ファイル、成熟度、評価スコアを付与。
3. **埋め込み生成**: Desire/Decisionテキストをベクトル化（例: InstructorXL, OpenAI text-embedding-3-large 等）。
4. **クラスタリング**: 階層的クラスタリング or HDBSCAN で自動クラスタリング。
5. **トピック命名**: クラスタ代表文とメタ情報から LLM で `topic_title` を生成。世界知識を活用し、足りない観点は補完メモに落とす。
6. **ステート構築**: 下記スキーマで `state/latest.json` と `state/latest.md` を生成。

```json
{
  "generated_at": "2025-09-26T13:31:00+09:00",
  "clusters": [
    {
      "cluster_id": "C001",
      "topic_title": "ナラティブ資産をコード階層で同期",
      "focus": "Desire",
      "centroid_terms": ["narrative", "コード", "階層"],
      "desires": [ { "desire_id": "2025-09-26-12:06", "summary": "…" } ],
      "decisions": [ { "dialogue_ref": "Dialogue.md:391", "decision": "…" } ],
      "insights": [
        "ナラティブツリーを自己納得の主軸として定義すべき",
        "コード→ナラティブ変換の自動化パイプラインが未整備"
      ],
      "next_hints": ["シリアライズテンプレート作成", "差分更新方針"]
    }
  ]
}
```

### 2.3 ビュー要件
- `state/viewer/index.html`
  - クラスタ一覧（topic_titleカード表示）。
  - クラスタ毎にDesire/Decisionタイムライン、関連ログリンク。
  - `insights` をハイライトして「気づき」を提示。
  - `next_hints` をShepherd backlog候補として渡せるようにする。

## 3. ナラティブツリー整備（アップデート）
### 3.1 背景
- 既存アウトライン（`ddd_narrative_tree_outline.md`）を踏まえ、ステートと連携するメタ情報を強化する。

### 3.2 生成プロセス（改訂案）
1. **構造同期**: コードツリーをスキャンして `narrative/` にミラー。
2. **ノードテンプレート**: 各ファイルに以下セクションを持つMarkdownを生成。
   - `Concept`: ステートクラスタから抽出した抽象的役割。
   - `Decisions`: 該当クラスタ内のDecisionを引用（リンク付き）。
   - `Rationale`: ステート `insights` を要約し、世界知識を加味した説明を挿入。
   - `Implications`: 他ノードとの依存や未解決課題。
3. **ラベル伝播**: ステートクラスタの `topic_title` をディレクトリREADMEに転写。
4. **スナップショット**: モジュール毎に `narrative/snapshots/<timestamp>/` を保存。

### 3.3 フォルダ構成案
```
startkit/
  state/
    latest.json
    latest.md
    history/
  narrative/
    README.md
    modules/
      api/
        README.md
        handlers.md
      ui/
        ...
    snapshots/
      2025-09-26T13-31/
        ...
```

## 4. スクリプト/モジュール案
| ツール | 役割 | 入力 | 出力 |
| --- | --- | --- | --- |
| `generate_tasks.py` | 既存 | logs → タスク | `startkit/tasks/` |
| `generate_state.py` *(新)* | Desire/Decision正規化・クラスタリング・insight抽出 | `memo/Dialogue/DESIRE` | `startkit/state/latest.*` |
| `generate_narrative.py` *(新)* | コード→ナラティブ変換 + ステートメタ付与 | コードツリー + state | `startkit/narrative/` |
| `state_viewer.html` *(新)* | ステートビュー生成 | `state/latest.json` | `startkit/state/viewer/index.html` |

## 5. オープンポイント
1. **クラスタ粒度**: 日時/テーマ/成熟度など、クラスタリングの閾値設定。
2. **世界知識の適用範囲**: LLMが推測する `insights` の深さと検証プロセス。
3. **ナラティブ差分管理**: 再生成時の手動編集保持。front-matterで手動追記を分離する案が必要。
4. **セキュアログ処理**: ステート生成時にセンシティブ情報が含まれる場合の扱い。

## 6. Dumpフェーズで次に検討したいこと
- `generate_state.py` の具体的入出力スキーマと疑似コード作成。
- クラスタリング閾値・トピック命名プロンプトの試作。
- ナラティブテンプレートの詳細項目と手動追記可能な枠の決定。

---
Dumpメモ: ステートとナラティブを結合する基盤方針を整理。具体的なスキーマ/テンプレート検討は次ステップで進める。
