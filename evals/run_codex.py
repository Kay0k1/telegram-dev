#!/usr/bin/env python3
"""Run the eval tasks with Codex CLI, with and without Telegram Dev.

Each task runs in a fresh git project under a temporary directory:

- ``plugin``: ``uvx --from <spec> telegram-dev install --agent codex`` was run in the project, so Codex sees
  the skill in ``.agents/skills`` and the MCP server in ``.codex/config.toml``;
- ``baseline``: the same empty project without the install;
- ``plugin-noweb`` / ``baseline-noweb``: the same two with Codex's web access turned off
  (``-c web_search="disabled" --disable apps``; the read-only sandbox already blocks network for shell
  commands). The Telegram Dev MCP server runs outside the sandbox and still reaches the documentation.

All configurations use the same model and the same prompt. The project is
trusted explicitly (``-c projects={...}``) because Codex only loads a project's MCP servers for trusted
directories. With ``--isolated-home`` Codex runs from a temporary ``CODEX_HOME`` that holds only a copy of
``auth.json`` and the model settings, so global AGENTS.md files, skills and MCP servers of the machine do
not leak into either configuration.

Transcripts (``codex exec --json``) go to ``<out>/transcripts/<task>.<config>.<run>.jsonl``.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIGS = ("plugin", "baseline", "plugin-noweb", "baseline-noweb")
NO_WEB = ["-c", 'web_search="disabled"', "--disable", "apps"]


def load_tasks(path: Path, only: list[str]) -> tuple[dict, list[dict]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    tasks = [task for task in data["tasks"] if not only or task["id"] in only]
    missing = set(only) - {task["id"] for task in tasks}
    if missing:
        raise SystemExit(f"unknown task ids: {', '.join(sorted(missing))}")
    return data, tasks


def isolated_home(root: Path, model: str | None, effort: str | None, tier: str | None) -> Path:
    """Create a CODEX_HOME with the user's auth and model settings only."""
    source = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    home = root / "codex-home"
    home.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / "auth.json", home / "auth.json")
    user = {}
    if (source / "config.toml").exists():
        user = tomllib.loads((source / "config.toml").read_text(encoding="utf-8"))
    settings = {
        "model": model or user.get("model"),
        "model_reasoning_effort": effort or user.get("model_reasoning_effort"),
        "service_tier": tier or user.get("service_tier"),
    }
    lines = [f'{key} = {json.dumps(value)}' for key, value in settings.items() if value]
    (home / "config.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return home


def prepare_project(base: Path, task_id: str, config: str, run: int, spec: str) -> Path:
    project = base / f"{config}-{task_id}-{run}"
    project.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    if config.startswith("plugin"):
        subprocess.run(["uvx", "--from", spec, "telegram-dev", "install", "--agent", "codex", "--project", str(project)],
                       check=True, stdout=subprocess.DEVNULL)
    return project


def run_one(task: dict, config: str, run: int, args, base: Path, env: dict, suffix: str) -> dict:
    out = args.out / "transcripts" / f"{task['id']}.{config}.{run}.jsonl"
    if out.exists() and not args.force:
        return {"task": task["id"], "config": config, "run": run, "skipped": True}
    project = prepare_project(base, task["id"], config, run, args.spec)
    trust = f'projects={{"{project}"={{trust_level="trusted"}}}}'
    command = ["codex", "exec", "--json", "--skip-git-repo-check", "-s", "read-only",
               "-C", str(project), "-c", trust]
    if config.endswith("-noweb"):
        command += NO_WEB
    command.append(task["prompt"] + suffix)
    started = time.time()
    with out.open("w", encoding="utf-8") as stdout, (out.with_suffix(".err")).open("w", encoding="utf-8") as stderr:
        try:
            code = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, env=env,
                                  timeout=args.timeout).returncode
        except subprocess.TimeoutExpired:
            code = "timeout"
    seconds = round(time.time() - started, 1)
    meta = {"task": task["id"], "config": config, "run": run, "exit": code, "seconds": seconds,
            "project": str(project), "command": command[:-1] + ["<prompt>"]}
    out.with_suffix(".meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return meta


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tasks", type=Path, default=HERE / "tasks.json")
    parser.add_argument("--out", type=Path, required=True, help="Run directory, e.g. evals/runs/2026-11-10")
    parser.add_argument("--only", nargs="*", default=[], help="Task ids to run (default: all)")
    parser.add_argument("--configs", nargs="*", default=list(CONFIGS[:2]), choices=CONFIGS)
    parser.add_argument("--run", type=int, default=1, help="Run number, for repeated runs of the same task")
    parser.add_argument("--spec", default="telegram-dev==0.5.0", help="Package spec passed to uvx --from")
    parser.add_argument("--isolated-home", action="store_true", help="Run Codex from a temporary CODEX_HOME")
    parser.add_argument("--model")
    parser.add_argument("--effort", help="model_reasoning_effort")
    parser.add_argument("--service-tier")
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=1800, help="Seconds per run")
    parser.add_argument("--force", action="store_true", help="Overwrite existing transcripts")
    args = parser.parse_args(argv)

    data, tasks = load_tasks(args.tasks, args.only)
    (args.out / "transcripts").mkdir(parents=True, exist_ok=True)
    base = Path(tempfile.mkdtemp(prefix="tgdev-evals-"))
    env = dict(os.environ)
    if args.isolated_home:
        env["CODEX_HOME"] = str(isolated_home(base, args.model, args.effort, args.service_tier))
    elif args.model or args.effort or args.service_tier:
        parser.error("--model/--effort/--service-tier need --isolated-home")
    version = subprocess.run(["codex", "--version"], capture_output=True, text=True, env=env).stdout.strip()
    settings = (Path(env["CODEX_HOME"]) / "config.toml").read_text(encoding="utf-8") if args.isolated_home else None
    jobs = [(task, config) for task in tasks for config in args.configs]
    started = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    print(f"{version}; {len(jobs)} runs; projects in {base}", file=sys.stderr)
    results = []
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            futures = [pool.submit(run_one, task, config, args.run, args, base, env, data.get("prompt_suffix", ""))
                       for task, config in jobs]
            for future in concurrent.futures.as_completed(futures):
                meta = future.result()
                results.append(meta)
                print(json.dumps(meta, ensure_ascii=False), file=sys.stderr)
    finally:
        if args.isolated_home:
            # Do not leave a copy of the credentials behind.
            (Path(env["CODEX_HOME"]) / "auth.json").unlink(missing_ok=True)
    manifest = args.out / "manifest.json"
    previous = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else {"batches": []}
    previous["batches"].append({"started": started, "finished": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "codex": version, "spec": args.spec,
                                "isolated_home": args.isolated_home, "codex_settings": settings,
                                "runs": sorted(results, key=lambda r: (r["task"], r["config"]))})
    manifest.write_text(json.dumps(previous, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
