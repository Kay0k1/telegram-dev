#!/usr/bin/env python3
"""Grade code-writing runs: extract the Bot API requests an answer lists and check them.

Every check is automatic. The final answer must end with a ```json block holding the requests the
code sends ([{"method": ..., "params": {...}}]). Each task gets a `valid` check (every request passes
the official Bot API schema with no errors) plus its own request checks from code-tasks.json.

    python evals/grade_code.py evals/runs/2026-11-10-code/0.7.0 evals/runs/2026-11-10-code/0.8.0
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import bot_api_schema  # noqa: E402
import telegram_knowledge  # noqa: E402
from grade import read_transcript  # noqa: E402

FENCE = re.compile(r"```json\s*\n(.*?)```", re.S)


def extract_requests(answer):
    """Requests from the last parseable ```json block of the answer."""
    for block in reversed(FENCE.findall(answer)):
        try:
            data = json.loads(block)
        except ValueError:
            continue
        items = data if isinstance(data, list) else [data]
        requests = [item for item in items if isinstance(item, dict) and isinstance(item.get("method"), str)]
        if requests:
            return [{"method": item["method"], "params": item.get("params") or {}} for item in requests]
    return []


def resolve(value, path):
    """All values at a dotted path; `[n]` indexes a list, `[*]` matches every element."""
    values = [value]
    for part in re.findall(r"[^.\[\]]+|\[\*\]|\[\d+\]", path):
        found = []
        for current in values:
            if isinstance(current, str) and current[:1] in "[{":
                try:
                    current = json.loads(current)
                except ValueError:
                    pass
            if part == "[*]" and isinstance(current, list):
                found.extend(current)
            elif part.startswith("[") and isinstance(current, list):
                index = int(part[1:-1])
                if index < len(current):
                    found.append(current[index])
            elif isinstance(current, dict) and part in current:
                found.append(current[part])
        values = found
    return values


def satisfied(request, predicate):
    values = resolve(request["params"], predicate["path"])
    if predicate.get("absent"):
        return not values
    if predicate.get("exists"):
        return any(value not in (None, "", [], {}) for value in values)
    return any(value == predicate["equals"] or str(value) == str(predicate["equals"]) for value in values)


def grade_task(task, requests, schema, releases):
    results = {}
    checked = [bot_api_schema.check(schema, request["method"], request["params"], releases) for request in requests]
    results["valid"] = bool(requests) and all(result["valid"] for result in checked)
    for check in task["checks"]:
        results[check["id"]] = any(request["method"] == check["method"]
                                   and all(satisfied(request, predicate) for predicate in check["where"])
                                   for request in requests)
    errors = [f"{request['method']}: {error['path']} {error['message']}" for request, result in zip(requests, checked)
              for error in result["errors"]]
    return results, errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("runs", nargs="+", type=Path, help="Run directories with transcripts/")
    parser.add_argument("--tasks", type=Path, default=HERE / "code-tasks.json")
    args = parser.parse_args(argv)
    tasks = {task["id"]: task for task in json.loads(args.tasks.read_text(encoding="utf-8"))["tasks"]}
    schema, source = telegram_knowledge._bot_api("schema")
    releases, _ = telegram_knowledge._bot_api("changelog")
    print(f"Bot API {schema['version']} schema from {source['source']} checked {source['checked_at']}\n")
    for run_dir in args.runs:
        rows = []
        for transcript in sorted((run_dir / "transcripts").glob("*.jsonl")):
            task_id, config, run = transcript.name[:-len(".jsonl")].split(".")
            data = read_transcript(transcript)
            requests = extract_requests(data["answer"])
            results, errors = grade_task(tasks[task_id], requests, schema, releases)
            rows.append({"task": task_id, "config": config, "run": int(run), "requests": len(requests),
                         "checks": results, "schema_errors": errors, "mcp_calls": data["mcp_calls"],
                         "web_calls": len(data["web_searches"]), "usage": data["usage"]})
        (run_dir / "code-results.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        by_config = {}
        for row in rows:
            total = by_config.setdefault(row["config"], {"passed": 0, "checks": 0, "tasks_ok": 0, "tasks": 0, "valid": 0})
            total["passed"] += sum(row["checks"].values())
            total["checks"] += len(row["checks"])
            total["tasks"] += 1
            total["tasks_ok"] += all(row["checks"].values())
            total["valid"] += row["checks"]["valid"]
        print(f"## {run_dir}")
        for config, total in by_config.items():
            print(f"- {config}: {total['passed']}/{total['checks']} checks, {total['tasks_ok']}/{total['tasks']} tasks fully correct, "
                  f"{total['valid']}/{total['tasks']} with schema-valid requests")
        for row in rows:
            failed = [name for name, ok in row["checks"].items() if not ok]
            if failed:
                print(f"  - {row['task']}.{row['config']}: failed {', '.join(failed)}; {'; '.join(row['schema_errors'][:3])}")
        print()


if __name__ == "__main__":
    main()
