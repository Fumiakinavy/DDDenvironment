#!/usr/bin/env python3
"""Generate prioritized task bundles from workflow modules.

Usage:
    python DDD/tools/generate_tasks.py --project DDD --update-viewer
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ALLOWED_STATUSES = {"backlog", "in-progress", "resolved"}

EXTRACTOR_ITEM = re.compile(r"^- `(?P<slug>[^`]+)`(?::|\s)+(?!$)(?P<body>.+)$")
EXTRACTOR_ITEM_NO_DESC = re.compile(r"^- `(?P<slug>[^`]+)`\s*$")
GROUP_CLUSTER_TITLE = re.compile(r"^#\s+.+?:\s*(?P<label>.+)$")
GROUP_SLUG = re.compile(r"^- `(?P<slug>[^`]+)`")
GROUP_DEP = re.compile(r"^- `(?P<src>[^`]+)`\s*→\s*`(?P<dst>[^`]+)`(?::\s*(?P<note>.+))?$")
BACKLOG_SLUG = re.compile(r"`(?P<slug>[^`]+)`")
TABLE_ROW = re.compile(r"^\|.*")


@dataclass
class Priority:
    method: str
    score: Optional[float]
    impact: Optional[int]
    confidence: Optional[int]
    effort: Optional[int]
    rank: Optional[int] = None


@dataclass
class Cluster:
    key: Optional[str]
    label: Optional[str]


@dataclass
class TaskSources:
    extractor: List[dict]
    groups: List[dict]
    scores: List[dict]
    shepherd: Optional[dict]


@dataclass
class TaskEntry:
    slug: str
    title: str
    summary: Optional[str]
    status: str
    priority: Priority
    cluster: Cluster
    dependencies: List[str]
    notes: List[str]
    links: TaskSources

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["priority"] = asdict(self.priority)
        payload["cluster"] = asdict(self.cluster)
        payload["links"] = {
            "extractor": self.links.extractor,
            "groups": self.links.groups,
            "scores": self.links.scores,
            "shepherd": self.links.shepherd,
        }
        return payload


@dataclass
class Bundle:
    project: str
    generated_at: str
    generator: dict
    source_files: dict
    tasks: List[TaskEntry]

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "generated_at": self.generated_at,
            "generator": self.generator,
            "source_files": self.source_files,
            "tasks": [task.to_dict() for task in self.tasks],
        }


def validate_bundle_payload(payload: dict) -> None:
    required_bundle_keys = {"project", "generated_at", "generator", "source_files", "tasks"}
    missing_bundle = required_bundle_keys - payload.keys()
    if missing_bundle:
        raise ValueError(f"Bundle payload missing keys: {sorted(missing_bundle)}")

    if not isinstance(payload.get("generator"), dict):
        raise ValueError("Bundle payload generator must be a dict")

    source_files = payload.get("source_files")
    if not isinstance(source_files, dict):
        raise ValueError("Bundle payload source_files must be a dict")
    for key in ("extractor", "groups", "scores", "shepherd"):
        if key not in source_files:
            raise ValueError(f"source_files missing key: {key}")

    tasks = payload.get("tasks")
    if not isinstance(tasks, list):
        raise ValueError("Bundle payload tasks must be a list")

    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            raise ValueError(f"Task #{index} must be a dict")
        required_task_keys = {
            "slug",
            "title",
            "summary",
            "status",
            "priority",
            "cluster",
            "dependencies",
            "notes",
            "links",
        }
        missing_task = required_task_keys - task.keys()
        if missing_task:
            raise ValueError(f"Task {task.get('slug', index)} missing keys: {sorted(missing_task)}")

        status = task.get("status")
        if status not in ALLOWED_STATUSES:
            raise ValueError(f"Task {task.get('slug', index)} has invalid status: {status}")

        priority = task.get("priority")
        if not isinstance(priority, dict):
            raise ValueError(f"Task {task.get('slug', index)} priority must be a dict")
        for key in ("method", "score", "impact", "confidence", "effort", "rank"):
            if key not in priority:
                raise ValueError(f"Task {task.get('slug', index)} priority missing key: {key}")

        cluster = task.get("cluster")
        if not isinstance(cluster, dict):
            raise ValueError(f"Task {task.get('slug', index)} cluster must be a dict")
        for key in ("key", "label"):
            if key not in cluster:
                raise ValueError(f"Task {task.get('slug', index)} cluster missing key: {key}")

        dependencies = task.get("dependencies")
        if not isinstance(dependencies, list):
            raise ValueError(f"Task {task.get('slug', index)} dependencies must be a list")

        notes = task.get("notes")
        if not isinstance(notes, list):
            raise ValueError(f"Task {task.get('slug', index)} notes must be a list")

        links = task.get("links")
        if not isinstance(links, dict):
            raise ValueError(f"Task {task.get('slug', index)} links must be a dict")
        for key in ("extractor", "groups", "scores", "shepherd"):
            if key not in links:
                raise ValueError(f"Task {task.get('slug', index)} links missing key: {key}")

def slug_to_title(slug: str) -> str:
    words = re.split(r"[-_]+", slug)
    return " ".join(word.capitalize() for word in words if word)


def parse_extractor(project_root: Path) -> Tuple[Dict[str, dict], List[str]]:
    extractor_dir = project_root / "workflow" / "extractor"
    result: Dict[str, dict] = {}
    files: List[str] = []
    if not extractor_dir.exists():
        return result, files
    for md_path in sorted(extractor_dir.glob("*.md")):
        files.append(str(md_path.relative_to(project_root)))
        lines = md_path.read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped.startswith("-"):
                continue
            match = EXTRACTOR_ITEM.match(stripped)
            if match:
                slug = match.group("slug").strip()
                body = match.group("body").strip()
                entry = result.setdefault(slug, {"summary": None, "sources": []})
                entry["summary"] = body or entry.get("summary")
                entry["sources"].append({
                    "module": "extractor",
                    "path": str(md_path.relative_to(project_root)),
                    "line": idx,
                    "text": body,
                })
                continue
            match2 = EXTRACTOR_ITEM_NO_DESC.match(stripped)
            if match2:
                slug = match2.group("slug").strip()
                entry = result.setdefault(slug, {"summary": None, "sources": []})
                entry["sources"].append({
                    "module": "extractor",
                    "path": str(md_path.relative_to(project_root)),
                    "line": idx,
                    "text": None,
                })
    return result, files


def parse_groups(project_root: Path) -> Tuple[Dict[str, dict], List[str]]:
    groups_dir = project_root / "workflow" / "groups"
    clusters: Dict[str, dict] = {}
    files: List[str] = []
    if not groups_dir.exists():
        return clusters, files
    for md_path in sorted(groups_dir.glob("*.md")):
        files.append(str(md_path.relative_to(project_root)))
        lines = md_path.read_text(encoding="utf-8").splitlines()
        cluster_label: Optional[str] = None
        if lines:
            first = lines[0].strip()
            m = GROUP_CLUSTER_TITLE.match(first)
            if m:
                cluster_label = m.group("label").strip()
        cluster_key = md_path.stem.strip()
        in_slug_section = False
        in_dep_section = False
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("##"):
                in_slug_section = "含まれる" in stripped
                in_dep_section = "依存" in stripped
                continue
            if stripped.startswith("-"):
                if in_slug_section:
                    m = GROUP_SLUG.match(stripped)
                    if not m:
                        continue
                    slug = m.group("slug").strip()
                    entry = clusters.setdefault(slug, {"cluster": None, "sources": [], "dependencies": [], "notes": []})
                    entry["cluster"] = {"key": cluster_key, "label": cluster_label}
                    entry["sources"].append({
                        "module": "groups",
                        "path": str(md_path.relative_to(project_root)),
                        "line": idx,
                        "note": "cluster-membership",
                    })
                elif in_dep_section:
                    m = GROUP_DEP.match(stripped)
                    if not m:
                        continue
                    src = m.group("src").strip()
                    dst = m.group("dst").strip()
                    note = (m.group("note") or "").strip() or None
                    entry = clusters.setdefault(dst, {"cluster": None, "sources": [], "dependencies": [], "notes": []})
                    entry["dependencies"].append(src)
                    entry["sources"].append({
                        "module": "groups",
                        "path": str(md_path.relative_to(project_root)),
                        "line": idx,
                        "note": f"dependency-from:{src}",
                    })
                    if note:
                        entry["notes"].append(note)
    return clusters, files


def parse_scores(project_root: Path) -> Tuple[Dict[str, dict], List[str]]:
    scores_dir = project_root / "workflow" / "scores"
    scores: Dict[str, dict] = {}
    files: List[str] = []
    if not scores_dir.exists():
        return scores, files
    md_paths = sorted(scores_dir.glob("*.md"))
    if not md_paths:
        return scores, files
    for md_path in md_paths:
        files.append(str(md_path.relative_to(project_root)))
        lines = md_path.read_text(encoding="utf-8").splitlines()
        for line in lines:
            if not TABLE_ROW.match(line.strip()):
                continue
            row = [part.strip() for part in line.strip().strip('|').split('|')]
            if len(row) < 6:
                continue
            if row[0] in ("---", "スラッグ"):
                continue
            slug = row[0].strip("`")
            try:
                impact = int(row[1]) if row[1] else None
                confidence = int(row[2]) if row[2] else None
                effort = int(row[3]) if row[3] else None
                score = float(row[4]) if row[4] else None
            except ValueError:
                impact = confidence = effort = None
                try:
                    score = float(row[4]) if row[4] else None
                except ValueError:
                    score = None
            memo = row[5] or None
            scores[slug] = {
                "impact": impact,
                "confidence": confidence,
                "effort": effort,
                "score": score,
                "memo": memo,
                "path": str(md_path.relative_to(project_root)),
            }
    return scores, files


def parse_shepherd(project_root: Path) -> Tuple[Dict[str, dict], Dict[str, List[str]], List[str]]:
    shepherd_dir = project_root / "workflow" / "shepherd"
    statuses: Dict[str, dict] = {}
    source_files: Dict[str, List[str]] = {"resolved": [], "in_progress": [], "backlog": []}
    if not shepherd_dir.exists():
        return statuses, source_files, []

    resolved_dir = shepherd_dir / "resolved"
    if resolved_dir.exists():
        for path in resolved_dir.glob("*.md"):
            slug = path.stem.strip()
            statuses[slug] = {
                "status": "resolved",
                "path": str(path.relative_to(project_root)),
            }
            source_files.setdefault("resolved", []).append(str(path.relative_to(project_root)))

    in_progress_dir = shepherd_dir / "in-progress"
    if in_progress_dir.exists():
        for path in in_progress_dir.glob("*.md"):
            slug = path.stem.strip()
            statuses[slug] = {
                "status": "in-progress",
                "path": str(path.relative_to(project_root)),
            }
            source_files.setdefault("in_progress", []).append(str(path.relative_to(project_root)))

    backlog_path = shepherd_dir / "backlog.md"
    if backlog_path.exists():
        source_files.setdefault("backlog", []).append(str(backlog_path.relative_to(project_root)))
        lines = backlog_path.read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped.startswith("-"):
                continue
            match = BACKLOG_SLUG.search(stripped)
            slug = None
            if match:
                slug = match.group("slug").strip()
            else:
                slug = stripped.lstrip("- ")
                slug = slug.split()[0] if slug else None
            if not slug:
                continue
            statuses.setdefault(slug, {
                "status": "backlog",
                "path": str(backlog_path.relative_to(project_root)),
            })
    all_sources = []
    for paths in source_files.values():
        all_sources.extend(paths)
    return statuses, source_files, all_sources


def collect_tasks(project_root: Path) -> Tuple[Bundle, dict]:
    extractor, extractor_files = parse_extractor(project_root)
    groups, group_files = parse_groups(project_root)
    scores, score_files = parse_scores(project_root)
    shepherd_status, shepherd_files_map, shepherd_files_list = parse_shepherd(project_root)

    slugs = set(extractor.keys()) | set(groups.keys()) | set(scores.keys()) | set(shepherd_status.keys())

    tasks: List[TaskEntry] = []
    score_values: List[Tuple[str, float]] = []

    for slug in sorted(slugs):
        extractor_entry = extractor.get(slug, {})
        group_entry = groups.get(slug, {})
        scores_entry = scores.get(slug, {})
        shepherd_entry = shepherd_status.get(slug)

        summary = extractor_entry.get("summary")
        title = slug_to_title(slug)
        status = (shepherd_entry or {}).get("status", "backlog")

        priority = Priority(
            method="ICE",
            score=scores_entry.get("score"),
            impact=scores_entry.get("impact"),
            confidence=scores_entry.get("confidence"),
            effort=scores_entry.get("effort"),
            rank=None,
        )

        cluster_info = group_entry.get("cluster") or {"key": None, "label": None}
        dependencies = group_entry.get("dependencies", [])
        notes = []
        if group_entry.get("notes"):
            notes.extend(group_entry["notes"])
        if scores_entry.get("memo"):
            notes.append(scores_entry["memo"])

        links = TaskSources(
            extractor=extractor_entry.get("sources", []),
            groups=group_entry.get("sources", []),
            scores=([{
                "module": "scores",
                "path": scores_entry.get("path"),
                "note": "latest"
            }] if scores_entry else []),
            shepherd=shepherd_entry,
        )

        task = TaskEntry(
            slug=slug,
            title=title,
            summary=summary,
            status=status,
            priority=priority,
            cluster=Cluster(**cluster_info),
            dependencies=dependencies,
            notes=notes,
            links=links,
        )
        tasks.append(task)

        if priority.score is not None:
            score_values.append((slug, priority.score))

    # Apply ranking based on score (descending)
    score_values.sort(key=lambda item: item[1], reverse=True)
    for rank, (slug, _) in enumerate(score_values, start=1):
        for task in tasks:
            if task.slug == slug:
                task.priority.rank = rank
                break

    generated_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    source_files = {
        "extractor": extractor_files,
        "groups": group_files,
        "scores": score_files,
        "shepherd": list(dict.fromkeys(shepherd_files_list)),  # dedupe preserving order
    }

    bundle = Bundle(
        project=project_root.name,
        generated_at=generated_at,
        generator={
            "script": "tools/generate_tasks.py",
            "version": "0.1.0",
        },
        source_files=source_files,
        tasks=tasks,
    )
    return bundle, {
        "extractor": extractor,
        "groups": groups,
        "scores": scores,
        "shepherd": shepherd_status,
    }


def write_json(payload: dict, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_at = payload.get("generated_at", "")
    timestamp = generated_at.replace(":", "") if isinstance(generated_at, str) else datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds").replace(":", "")
    json_path = output_dir / f"tasks-{timestamp}.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    latest_path = output_dir / "latest.json"
    with latest_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return json_path


def write_viewer(payload: dict, viewer_dir: Path) -> Path:
    viewer_dir.mkdir(parents=True, exist_ok=True)
    html_path = viewer_dir / 'index.html'
    data_json = json.dumps(payload, ensure_ascii=False)
    template_path = Path(__file__).with_name('viewer_template.html')
    if template_path.exists():
        template = template_path.read_text(encoding='utf-8')
    else:
        raise FileNotFoundError(f'Static viewer template not found: {template_path}')
    html = (template
            .replace('__PROJECT__', str(payload.get('project', '-')))
            .replace('__GENERATED_AT__', str(payload.get('generated_at', '-')))
            .replace('__DATA__', data_json))
    with html_path.open('w', encoding='utf-8') as f:
        f.write(html)
    return html_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate prioritized tasks JSON from workflow modules.")
    parser.add_argument("--project", default="DDD", help="Project directory relative to repository root")
    parser.add_argument("--output-dir", help="Directory to write tasks JSON (default: <project>/workflow/tasks)")
    parser.add_argument("--viewer-dir", help="Directory to write viewer HTML (default: sibling viewer directory)")
    parser.add_argument("--update-viewer", action="store_true", help="Also refresh viewer HTML")
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    if script_path.parent.name == 'tools' and script_path.parent.parent.name == 'startkit':
        repo_root = script_path.parents[3]
    else:
        repo_root = script_path.parents[2]
    project_root = (repo_root / args.project).resolve()
    if not project_root.exists():
        raise SystemExit(f"Project directory not found: {project_root}")

    bundle, _extras = collect_tasks(project_root)
    payload = bundle.to_dict()
    validate_bundle_payload(payload)
    if args.output_dir:
        output_dir = (repo_root / args.output_dir).resolve()
    else:
        output_dir = project_root / "workflow" / "tasks"
    json_path = write_json(payload, output_dir)

    viewer_dir: Optional[Path] = None
    if args.update_viewer:
        if args.viewer_dir:
            viewer_dir = (repo_root / args.viewer_dir).resolve()
        else:
            viewer_dir = output_dir.parent / "viewer"
        write_viewer(payload, viewer_dir)

    print(f"Generated: {json_path.relative_to(repo_root)}")
    print(f"Latest JSON: {(output_dir / 'latest.json').relative_to(repo_root)}")
    if viewer_dir is not None:
        print(f"Viewer: {viewer_dir.joinpath('index.html').relative_to(repo_root)}")


if __name__ == "__main__":
    main()
