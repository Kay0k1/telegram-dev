"""Check official Telegram sources and retain only attributed change metadata."""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import re
import sys
import time

# Support running this file directly from a source checkout.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from telegram_knowledge import SEEDS, canonical, family, fetch, now

SCHEMA_VERSION = 1


def load_snapshot(path):
    if path is None or not path.exists():
        return {"schema_version": SCHEMA_VERSION, "sources": {}}
    snapshot = json.loads(path.read_text(encoding="utf-8"))
    if snapshot.get("schema_version") != SCHEMA_VERSION or not isinstance(snapshot.get("sources"), dict):
        raise ValueError("Unsupported or invalid source snapshot")
    for url, record in snapshot["sources"].items():
        if canonical(url) != url or not isinstance(record, dict):
            raise ValueError("Invalid source record in snapshot")
        if not re.fullmatch(r"[a-f0-9]{64}", str(record.get("sha256", ""))):
            raise ValueError("Invalid source hash in snapshot")
    return snapshot


def check_sources(urls, previous, *, workers=4, attempts=2, fetcher=None, stamp=None):
    """Return a snapshot and exact change report; failed fetches retain old hashes."""
    if not 1 <= workers <= 4 or not 1 <= attempts <= 3:
        raise ValueError("Use 1–4 workers and 1–3 attempts")
    urls = sorted(set(urls))
    if not urls or any(canonical(url) != url for url in urls):
        raise ValueError("Sources must be canonical URLs within official documentation boundaries")
    fetcher = fetcher or fetch
    stamp = stamp or now()
    old_sources = previous.get("sources", {})
    sources, results = {}, []

    def inspect(url):
        for attempt in range(attempts):
            try:
                return fetcher(url)
            except Exception:
                if attempt + 1 == attempts:
                    raise
                time.sleep(attempt + 1)

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(inspect, url): url for url in urls}
        for future in concurrent.futures.as_completed(futures):
            requested = futures[future]
            old = old_sources.get(requested)
            try:
                resolved, title, body, _links = future.result()
                if canonical(resolved) != resolved or len(body.strip()) < 30:
                    raise ValueError("Empty source or redirect outside documentation boundaries")
                sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
                state = "new" if old is None else "unchanged" if old["sha256"] == sha else "changed"
                record = {
                    "url": resolved, "title": title, "family": family(resolved),
                    "sha256": sha, "checked_at": stamp,
                    "changed_at": old.get("changed_at", stamp) if state == "unchanged" else stamp,
                }
                sources[requested] = record
                results.append({"requested_url": requested, "status": state,
                                "previous_sha256": old["sha256"] if old else None, **record})
            except Exception as exc:
                if old is not None:
                    sources[requested] = dict(old)
                results.append({
                    "requested_url": requested, "family": family(requested), "status": "failed",
                    "error": f"{type(exc).__name__}: {exc}"[:1000],
                    "checked_at": stamp, "last_successful_check": old.get("checked_at") if old else None,
                    "previous_sha256": old["sha256"] if old else None,
                })
    results.sort(key=lambda item: item["requested_url"])
    counts = {state: sum(item["status"] == state for item in results)
              for state in ("new", "changed", "unchanged", "failed")}
    counts["attempted"] = len(urls)
    return (
        {"schema_version": SCHEMA_VERSION, "generated_at": stamp, "sources": dict(sorted(sources.items()))},
        {"schema_version": SCHEMA_VERSION, "checked_at": stamp,
         "healthy": counts["failed"] == 0, "counts": counts, "sources": results,
         "scope": "Configured official documentation entry points and selected repository files; not a complete crawl.",
         "hash_basis": "Extracted document body returned by telegram_knowledge.fetch, encoded as UTF-8."},
    )


def markdown_cell(value):
    text = str(value).replace("\\", "\\\\").replace("<", "&lt;").replace(">", "&gt;")
    for character in ("|", "[", "]", "`", "*"):
        text = text.replace(character, "\\" + character)
    return text.replace("\n", " ").replace("\r", " ")


def render_status(report):
    counts = report["counts"]
    lines = [
        "# Telegram Dev — состояние официальных источников / source status", "",
        f"Проверено / Checked: `{report['checked_at']}`", "",
        f"Источников / Sources: **{counts['attempted']}** · Новых / New: **{counts['new']}** · "
        f"Изменившихся / Changed: **{counts['changed']}** · Без изменений / Unchanged: **{counts['unchanged']}** · "
        f"Ошибок / Failures: **{counts['failed']}**", "",
        "Проверяется извлечённый текст официальных страниц. Хэш показывает изменение текста, "
        "но не описывает его смысл. Ошибка загрузки не считается обновлением или удалением документа.", "",
        "Hashes compare extracted official source text; this report does not infer what a change means. "
        "A fetch failure does not imply a document changed or was deleted.", "",
        "| Источник / Source | Семейство / Family | Статус / Status |", "| --- | --- | --- |",
    ]
    for item in report["sources"]:
        url = item["requested_url"]
        label = markdown_cell(item.get("title", url))
        detail = markdown_cell(item.get("error", ""))
        status = item["status"] + (f": {detail}" if detail else "")
        lines.append(f"| [{label}]({url}) | {markdown_cell(item['family'])} | {status} |")
    lines.extend(["", "Machine-readable: [source-report.json](source-report.json), "
                  "[source-snapshot.json](source-snapshot.json).", "",
                  "[Project / Проект](https://github.com/Kay0k1/telegram-dev) · "
                  "[Maintenance / Обновление](https://github.com/Kay0k1/telegram-dev/blob/main/docs/maintenance.md)", ""])
    return "\n".join(lines)


def write_outputs(output, snapshot, report):
    output.mkdir(parents=True, exist_ok=True)
    files = {
        "source-snapshot.json": json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
        "source-report.json": json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        "README.md": render_status(report),
    }
    for name, content in files.items():
        target = output / name
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(target)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous", type=Path, help="Previous metadata snapshot (missing file starts a baseline)")
    parser.add_argument("--output", type=Path, default=Path(".source-monitor/current"))
    parser.add_argument("--source", action="append", help="Check specific official source(s); default: all configured seeds")
    parser.add_argument("--workers", type=int, choices=range(1, 5), default=4)
    parser.add_argument("--attempts", type=int, choices=range(1, 4), default=2)
    args = parser.parse_args(argv)
    snapshot, report = check_sources(args.source or SEEDS, load_snapshot(args.previous),
                                     workers=args.workers, attempts=args.attempts)
    write_outputs(args.output, snapshot, report)
    print(json.dumps({"checked_at": report["checked_at"], "healthy": report["healthy"], **report["counts"]}))
    for item in report["sources"]:
        if item["status"] == "failed":
            print(f"FAILED {item['requested_url']}: {item['error']}", file=sys.stderr)
    return 0 if report["healthy"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
