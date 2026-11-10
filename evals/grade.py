#!/usr/bin/env python3
"""Grade Codex transcripts against the task rubrics.

Automatic checks run each rubric pattern over the agent's final answer. Manual decisions from
``grades.json`` (made by reading the answer) override them, and every ``must_not`` and ``manual`` fact
needs one. Writes ``results.json`` next to the transcripts and prints a Markdown summary.

    python evals/grade.py evals/runs/2026-11-10
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read_transcript(path: Path) -> dict:
    messages, mcp, web, commands, usage, errors = [], [], [], [], {}, []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = event.get("item") or {}
        if event.get("type") == "item.completed":
            kind = item.get("type")
            if kind == "agent_message":
                messages.append(item.get("text", ""))
            elif kind == "mcp_tool_call" and item.get("server") == "telegram-knowledge":
                mcp.append(item.get("tool"))
            elif kind == "mcp_tool_call" and item.get("server") == "codex_apps":
                # Codex's built-in connectors (search_service.web_run, github.fetch) are web access.
                web.append(f"{item.get('server')}.{item.get('tool')}")
            elif kind == "web_search":
                web.append(item.get("query") or (item.get("action") or {}).get("url") or "")
            elif kind == "command_execution":
                commands.append(item.get("command", ""))
        elif event.get("type") == "turn.completed":
            usage = event.get("usage") or {}
        elif event.get("type") in ("error", "turn.failed"):
            errors.append(event)
    return {"answer": messages[-1] if messages else "", "messages": messages, "mcp_calls": mcp, "web_searches": web,
            "commands": commands, "usage": usage, "errors": errors}


def matches(patterns: list[str], text: str) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def grade(run_dir: Path, tasks: list[dict], manual: dict) -> list[dict]:
    rows = []
    by_id = {task["id"]: task for task in tasks}
    for path in sorted((run_dir / "transcripts").glob("*.jsonl")):
        task_id, config, run = path.name[:-len(".jsonl")].rsplit(".", 2)
        task = by_id.get(task_id)
        if task is None:
            continue
        key = f"{task_id}.{config}.{run}"
        transcript = read_transcript(path)
        meta_path = path.with_suffix(".meta.json")
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        decisions = manual.get(key, {})
        answer = transcript["answer"]
        must, must_not, pending = {}, {}, []
        for fact in task["must"]:
            auto = matches(fact.get("patterns", []), answer) if fact.get("patterns") else None
            final = decisions.get("must", {}).get(fact["id"], None if fact.get("manual") else auto)
            if final is None:
                pending.append(f"must:{fact['id']}")
            must[fact["id"]] = {"auto": auto, "final": final}
        for fact in task["must_not"]:
            auto = matches(fact.get("patterns", []), answer) if fact.get("patterns") else None
            final = decisions.get("must_not", {}).get(fact["id"])
            if final is None:
                pending.append(f"must_not:{fact['id']}")
            must_not[fact["id"]] = {"auto": auto, "final": final}
        hits = sum(1 for value in must.values() if value["final"])
        violations = sum(1 for value in must_not.values() if value["final"])
        leaks = [command for command in transcript["commands"]
                 if re.search(r"telegram[-_]dev|telegram_knowledge|\.agents/skills", command)] if config.startswith("baseline") else []
        rows.append({
            "task": task_id, "config": config, "run": int(run),
            "must": must, "must_not": must_not,
            "facts": hits, "facts_total": len(must), "violations": violations,
            "correct": hits == len(must) and violations == 0 and not pending,
            "pending": pending, "note": decisions.get("note", ""),
            "mcp_calls": len(transcript["mcp_calls"]), "web_searches": len(transcript["web_searches"]),
            "commands": len(transcript["commands"]), "baseline_plugin_access": leaks,
            "mentions_skill": any("telegram-dev" in message for message in transcript["messages"]),
            "seconds": meta.get("seconds"), "exit": meta.get("exit"), "usage": transcript["usage"],
            "errors": len(transcript["errors"]), "answer_chars": len(answer),
        })
    return rows


def primary(rows: list[dict]) -> list[dict]:
    """The graded run per task and config: run 1 (repeats are reported separately)."""
    return [row for row in rows if row["run"] == 1]


LABELS = {"plugin": "Telegram Dev + web", "baseline": "Web only",
          "plugin-noweb": "Telegram Dev, no web", "baseline-noweb": "Neither"}


def summary(rows: list[dict], tasks: list[dict]) -> str:
    configs = [config for config in LABELS if any(row["config"] == config for row in rows)]
    lines = ["| Task | " + " | ".join(LABELS[c] for c in configs) + " |", "| --- |" + " --- |" * len(configs)]
    totals = {config: [0, 0, 0, 0, 0] for config in configs}
    for task in tasks:
        cells = []
        for config in configs:
            row = next((r for r in primary(rows) if r["task"] == task["id"] and r["config"] == config), None)
            if row is None:
                cells.append("—")
                continue
            mark = "✅" if row["correct"] else ("⚠️" if row["violations"] == 0 else "❌")
            extra = f", {row['violations']} wrong" if row["violations"] else ""
            cells.append(f"{mark} {row['facts']}/{row['facts_total']}{extra}")
            total = totals[config]
            total[0] += row["facts"]; total[1] += row["facts_total"]; total[2] += row["violations"]
            total[3] += row["correct"]; total[4] += 1
        lines.append(f"| `{task['id']}` | " + " | ".join(cells) + " |")
    lines.append("| **Facts** | " + " | ".join(f"**{t[0]}/{t[1]}**" for t in totals.values()) + " |")
    lines.append("| **Fully correct** | " + " | ".join(f"**{t[3]}/{t[4]}**" for t in totals.values()) + " |")
    lines.append("| **Wrong claims** | " + " | ".join(f"**{t[2]}**" for t in totals.values()) + " |")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--tasks", type=Path, default=HERE / "tasks.json")
    parser.add_argument("--grades", type=Path, help="Manual decisions (default: <run_dir>/grades.json)")
    parser.add_argument("--show", help="Print the final answer of <task>.<config>.<run> and exit")
    args = parser.parse_args(argv)
    tasks = json.loads(args.tasks.read_text(encoding="utf-8"))["tasks"]
    if args.show:
        print(read_transcript(args.run_dir / "transcripts" / f"{args.show}.jsonl")["answer"])
        return 0
    grades_path = args.grades or args.run_dir / "grades.json"
    manual = json.loads(grades_path.read_text(encoding="utf-8")) if grades_path.exists() else {}
    rows = grade(args.run_dir, tasks, manual)
    (args.run_dir / "results.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(summary(rows, tasks))
    pending = [f"{r['task']}.{r['config']}.{r['run']}: {', '.join(r['pending'])}" for r in rows if r["pending"]]
    if pending:
        print("\nNeeds a manual decision:\n" + "\n".join(pending), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
