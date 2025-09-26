# State Synthesizer Plan (v0)

## Context Snapshot
- DDD1 requires a per-prompt state snapshot that clusters DESIRE / Dialogue signals and surfaces next hints for the action loop.
- `state_synthesizer_spec.md` already defines the target schema and processing expectations for `startkit/tools/generate_state.py`.
- Task tracker (`startkit/tasks/latest.json`) lists `state-synthesizer-plan` as highest priority backlog item, blocking downstream narrative tooling.

## Objectives
1. Deliver a reproducible plan to implement `generate_state.py` with supporting modules, tests, and viewer assets under `startkit/state/`.
2. Ensure the plan maps spec requirements to concrete milestones that can be executed in short cycles (≤1 day per milestone).
3. Define logging, validation, and integration touchpoints so that tasks composer and narrative mirror can consume the artifacts without rework.

## Success Metrics
- `startkit/state/latest.json` and `latest.md` regenerate in <2s for 200 log entries.
- Clusters expose ≤3 actionable `next_hints` per run, backed by source references.
- Viewer HTML mirrors JSON content with zero manual edits (plan includes automation path).

## Deliverables by Phase
### Phase 1 — Parser & Models (Foundations)
- Implement log loaders, block parsers, and canonical entry models.
- Emit `latest.json` with flat `entries[]` and metadata (no clustering yet).
- Unit tests for parsing edge cases and maturity scoring heuristics.

### Phase 2 — Clustering & Insights (Core Intelligence)
- Add vectorization backend (TF-IDF default, pluggable embedding hook).
- Produce `clusters[]`, `insights[]`, `next_hints[]`, `open_questions[]` per spec.
- Introduce snapshot option (`--snapshot`) and stale cluster detection.

### Phase 3 — Viewer & Tooling Integration
- Generate `latest.md` digest and HTML viewer embedding JSON.
- Wire CLI flags (`--limit`, `--since`, `--no-viewer`) and logging output.
- Document runbook + update AGENTS after validation, align with tasks composer contract.

## Implementation Breakdown
- **Module Layout**
  - `startkit/tools/generate_state.py`: thin CLI wrapper orchestrating pipeline.
  - `startkit/state_synthesizer/loader.py`: file IO, mirror resolution, block extraction.
  - `startkit/state_synthesizer/normalizer.py`: entry models, maturity scoring, hashing.
  - `startkit/state_synthesizer/cluster.py`: vectorizer factory, clustering, labeling.
  - `startkit/state_synthesizer/writer.py`: JSON/MD serialization, viewer update helper.
  - `startkit/state_synthesizer/utils.py`: shared helpers (timestamps, path utils).
  - `tests/state_synthesizer/`: parser fixtures, clustering snapshots, CLI smoke test.

- **Data Flow**
  1. Resolve target project path (`REPORT` default) and locate mirror logs.
  2. Parse memo/desire/dialogue into structured entries with source pointers.
  3. Normalize maturity scores, dedupe overlapping entries, assign stable ids.
  4. Vectorize recent entries (limit configurable), cluster, and label.
  5. Derive insights & hints using maturity deltas + missing task links.
  6. Serialize artifacts, update viewer, optionally write history snapshot.

- **Testing & Tooling**
  - Use pytest with fixtures under `tests/fixtures/state_logs/` for deterministic outputs.
  - Provide `make state-synth` alias (optional) to wrap python invocation.
  - Logging via `logging` module with `--verbose` flag for debugging.

## Integration & Dependencies
- Reads task metadata from `startkit/tasks/latest.json` to link clusters to slugs.
- Exposes `next_hints` consumed by Shepherd / Task composer; ensure schema contract documented.
- Emits summary block for `self_improvement.md` when efficiency gains identified (manual step).

## Risks & Mitigations
- **Clustering Accuracy**: start with TF-IDF to avoid external dependencies; design vectorizer interface for later embedding swap.
- **Performance**: cap entries by default and cache parsed blocks (simple JSON cache in `state/cache.json`).
- **Viewer Drift**: centralize JSON embed helper to reuse tasks viewer pipeline.

## Open Decisions (≤3)
1. Embedding backend choice beyond TF-IDF fallback (local model vs. stub).
2. Strategy for linking clusters to tasks (exact slug match vs. fuzzy tags).
3. Snapshot retention policy (how many `history` files to keep by default).

## Next Actions (Sprint 0)
- Spin up module skeletons and tests directory per layout above.
- Prepare sample log fixtures (subset of current memo/dialogue) for parser validation.
- Schedule check-in after Phase 1 implementation to confirm clustering requirements.

