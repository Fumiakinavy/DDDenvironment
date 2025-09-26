# State Synthesizer Specification (Draft)

## Purpose
- Provide an executable spec for `startkit/tools/generate_state.py` that converts Desire/Decision logs into a clustered "state" snapshot.
- Maintain a prompt-synced mirror of the user's mental model, surfacing insights and next action hints.
- Feed downstream modules (Tasks composer, Narrative mirror) with structured, timestamped state artifacts.

## Scope & Triggers
- **Trigger**: Every user prompt (incl. follow-up clarifications) and optional re-run after Dump closure for consistency checks.
- **Inputs**: Mirror logs (`memo.md`, `DESIRE.md`, `Dialogue.md`) under both global root and `<project>/` (REPORT). The script always prefers project-local copies and falls back to global if missing.
- **Non-goals**: Editing source logs, modifying tasks JSON, or generating narrative trees.

## Output Artifacts
1. `startkit/state/latest.json`
   - Single source of truth for current clusters, decisions, and hints.
   - Contains metadata, normalized entries, and derived analytics.
2. `startkit/state/latest.md`
   - Human-readable digest mirroring the JSON content (clusters, highlights, open decisions).
3. `startkit/state/history/state-<timestamp>.json` (optional flag `--snapshot`)
   - Immutable snapshots for audit/backtracking.
4. `startkit/state/viewer/index.html`
   - Lightweight table/accordion view (reuse viewer template pattern) embedding `latest.json` for quick inspection.

## JSON Schema (top-level)
```json
{
  "project": "REPORT",
  "generated_at": "ISO8601",
  "source": {
    "memo": "path",
    "desire": "path",
    "dialogue": "path",
    "window": "2025-09-26T12:00+09:00→2025-09-26T16:41+09:00"
  },
  "entries": [ ... ],
  "clusters": [ ... ],
  "insights": [ ... ],
  "next_hints": [ ... ],
  "open_questions": [ ... ]
}
```
- `entries[]`
  - `id`: Stable hash (SHA1 of timestamp+origin line).
  - `timestamp`, `topic`, `desire_summary`, `decision_summary`, `maturity` (1–5), `origin` (`memo`, `desire`, `dialogue`).
- `clusters[]`
  - `key`: e.g. `state-2025-09-26-a`.
  - `label`: Auto generated topic title.
  - `members`: Entry ids.
  - `centroid_terms`: Top keywords/phrases.
  - `status`: `active` / `stale` (based on last update threshold, e.g. >48h).
  - `related_tasks`: Matching task slugs if overlap (string match or manual mapping table).
- `insights[]`
  - Narrative sentences summarising cluster intent or change since previous snapshot.
- `next_hints[]`
  - Actionable prompts (≤3) referencing cluster keys and suggested follow-up.
- `open_questions[]`
  - Items lacking aligned decisions (derived from entries tagged `maturity <= 2` with no linked task).

## Processing Pipeline
1. **Load & Parse Logs**
   - Read mirror log files with UTF-8.
   - Extract structured blocks via regex matching `[YYYY-MM-DD HH:MM]` headers and trailing metadata lines (`トピック`, `欲求`, etc.).
   - Capture Dialogue blocks for decisions (`解釈`, `成熟度評価`, `実行ログ`, `自己評価`).

2. **Normalize Entries**
   - Map each block to canonical `entry` with fields described above.
   - Detect decisions by keywords (`決定事項`, `Decision`, `実行ログ`).
   - Assign provisional maturity score:
     - `5`: `自己評価` ≥90 or Dialogue `成熟度評価` ≥4.5.
     - `3`: default when explicit rating missing.
     - `1`: explicit uncertainty phrases ("検討", "未決").

3. **Vectorize & Cluster**
   - Use sentence transformer (if offline feasible) or fallback TF-IDF with scikit-learn.
   - Parameters:
     - Max window: last 120 entries; older entries degrade to `stale` cluster but remain for history.
     - Similarity threshold: cosine ≥0.52 to join cluster.
     - Force at least 2 entries per cluster; otherwise treat as standalone `singleton` cluster.
   - Maintain stable cluster keys by hashing earliest member id.

4. **Topic Labeling**
   - Generate candidate keywords by extracting top noun phrases per cluster.
   - Compose label using template: `<primary noun> × <context> (Desire|Decision)`.
   - If cluster is tasks-related (matching existing `startkit/tasks/latest.json` slugs), reuse task title.

5. **Insight Synthesis**
   - For each cluster, compare latest entry timestamp with previous snapshot (if available) to detect new developments.
   - Output bullet sentences (max 2 per cluster) emphasising maturity changes or unresolved questions.

6. **Next Hints Generation**
   - Prioritise clusters with maturity ≤2 and no active task link.
   - Build hints referencing relevant log location, e.g. `"Focus on state-synthesizer-plan: clarify clustering granularity (memo.md:428)."`

7. **Serialization & Output**
   - Write `latest.json` with indentation and `ensure_ascii=False`.
   - Render `latest.md` summarising clusters and hints (Markdown headings, bullet lists, link back to origins).
   - Update `viewer/index.html` by embedding JSON (same approach as tasks viewer) with sections for clusters/insights.
   - Optional `--no-viewer` flag to skip HTML update for automation scenarios.

## CLI & Flags
```
python3 startkit/tools/generate_state.py \
  --project REPORT \
  [--snapshot] [--no-viewer] [--limit 120] [--since "2025-09-25T00:00+09:00"]
```
- `--limit`: cap entries considered (default 120).
- `--since`: ignore logs older than timestamp (useful for large history).
- `--snapshot`: append timestamped JSON to history directory.

## Integration Points
- **Tasks Composer**: `next_hints` feeds backlog choices; clusters with `related_tasks` allow consistency checks when tasks resolve.
- **Narrative Mirror**: Provide cluster labels and insights as annotations for narrative nodes (e.g., embed in commit docs).
- **Self-Improvement Loop**: Expose `open_questions` to highlight areas needing reflection or relabeling.

## Validation & Testing
- Unit tests for parser functions (regex extraction, maturity scoring).
- Snapshot tests comparing generated JSON/MD to fixtures for known log sets.
- Performance target: <2s for typical log size (~200 entries).

## Open Decisions
1. Embedding backend: local sentence-transformer vs. TF-IDF fallback (decide based on runtime constraints).
2. Viewer layout: reuse existing `viewer_template` vs. dedicated component with cluster tabs.
3. Cluster decay policy: define criteria to archive or deprioritise stale clusters.

## Recommended Next Steps
1. Implement parser & schema classes (`state_models.py`) to keep logic testable.
2. Prototype clustering with realistic log sample; iterate on threshold to avoid over/under grouping.
3. Draft viewer layout (cards grouped by cluster) and confirm with user before styling polish.
4. Align Task composer to read `next_hints` and auto-suggest backlog entries.
5. Document runbook in AGENTS after first working version.
