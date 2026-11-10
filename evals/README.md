# Evals: does Telegram Dev improve an agent's answers?

Run on **2026-11-10** with **Codex CLI 0.167.0** (model `gpt-6.1-sol`, reasoning effort `ultra`, service tier `priority`) and **telegram-dev 0.5.0** from PyPI. Claude Code was not measured: its headless login was expired on the test machine.

## Result

| | Telegram Dev + web | Web only | Telegram Dev, no web | Neither |
| --- | --- | --- | --- | --- |
| Rubric facts | **45/47** | **45/47** | **45/47** | **38/47** |
| Tasks fully correct | **9/11** | **9/11** | **9/11** | **8/11** |
| Wrong claims | 0 | 0 | 0 | 1 |

- **With Codex's built-in web access, Telegram Dev made no measurable difference on these 11 tasks.** The baseline agent opened core.telegram.org and docs.ton.org pages itself and wrote answers that were almost word for word the same as the plugin runs.
- **Without web access, Telegram Dev is what kept the answers current.** Plain Codex said it could not confirm the latest Bot API and declined to name it, and it described the pre-rename TON world (Toncoin, Wallet in Telegram, Wallet V5). With Telegram Dev and no web, Codex answered Bot API 10.4 / HTML widgets and Gram / Telegram Money / WalletTg from the MCP server. A second run of those tasks gave the same split.
- **One task went the other way:** on the Tolk contract, plain Codex without web mentioned that FunC is the predecessor (a rubric fact) in both runs; the plugin runs recommended Tolk without mentioning FunC at all. The contract code was current Tolk in every configuration.
- The model already knows most of this material: 8 of 11 tasks were fully correct with no plugin and no web, including `initData` third-party validation with Telegram's published Ed25519 key, the jetton transfer opcode and decimals, and current Tolk syntax.

A qualitative difference not covered by the rubrics: in the `ton_proof` login task, both plugin runs (with and without web) verified WalletTg wallets by checking the trampoline code hash and reading the live `get_public_key`, as the current docs.ton.org page requires. The web-only run mentioned that WalletTg needs this but left it out of the code, and the run without either rejected WalletTg wallets as unknown, which would lock out Telegram Money users.

## Per task (run 1)

| Task | Telegram Dev + web | Web only | Telegram Dev, no web | Neither |
| --- | --- | --- | --- | --- |
| `bot-red-button-emoji` | ✅ 4/4 | ✅ 4/4 | ✅ 4/4 | ✅ 4/4 |
| `bot-video-note` | ✅ 4/4 | ✅ 4/4 | ✅ 4/4 | ✅ 4/4 |
| `miniapp-initdata` | ✅ 6/6 | ✅ 6/6 | ✅ 6/6 | ✅ 6/6 |
| `bot-api-latest` | ✅ 4/4 | ✅ 4/4 | ✅ 4/4 | ⚠️ 0/4 |
| `bot-vs-mtproto-history` | ✅ 4/4 | ✅ 4/4 | ✅ 4/4 | ✅ 4/4 |
| `miniapp-sell-for-ton` | ⚠️ 3/4 | ⚠️ 3/4 | ⚠️ 3/4 | ⚠️ 3/4 |
| `ton-proof-login` | ✅ 6/6 | ✅ 6/6 | ✅ 6/6 | ✅ 6/6 |
| `ton-jetton-transfer` | ✅ 4/4 | ✅ 4/4 | ✅ 4/4 | ✅ 4/4 |
| `ton-tolk-contract` | ⚠️ 3/4 | ⚠️ 3/4 | ⚠️ 3/4 | ✅ 4/4 |
| `ton-telegram-wallet-naming` | ✅ 4/4 | ✅ 4/4 | ✅ 4/4 | ❌ 0/4, 1 wrong |
| `bot-utf16-entities` | ✅ 3/3 | ✅ 3/3 | ✅ 3/3 | ✅ 3/3 |

✅ all required facts and no wrong claims · ⚠️ facts missing, nothing wrong · ❌ a wrong claim.

The two ⚠️ rows shared by every configuration are omissions, not errors: in `miniapp-sell-for-ton` every answer chose Stars (`XTR`) and refused TON for the skin, but none said what TON Connect is still allowed for; in `ton-tolk-contract` the three ⚠️ answers did not mention FunC.

**Repeats (run 2, no-web configurations only, for the three tasks where they differed):** `bot-api-latest` 4/4 vs 0/4, `ton-telegram-wallet-naming` 4/4 vs 0/4 with one wrong claim, `ton-tolk-contract` 3/4 vs 4/4 — the same split as run 1. The tied tasks were not repeated.

Every decision, with a note per answer, is in [runs/2026-11-10/grades.json](runs/2026-11-10/grades.json); scores per fact, tool counts and token use are in [results.json](runs/2026-11-10/results.json); the raw `codex exec --json` transcripts are in [transcripts/](runs/2026-11-10/transcripts).

## Cost and tool use (run 1, 11 tasks each)

| Configuration | Telegram Dev calls | Web calls | Median time | Total time | Input tokens | Output tokens |
| --- | --- | --- | --- | --- | --- | --- |
| Telegram Dev + web | 62 | 25 | 86 s | 18.4 min | 4.5 M (495 K uncached) | 54 K |
| Web only | 0 | 46 | 83 s | 16.3 min | 3.7 M (452 K uncached) | 47 K |
| Telegram Dev, no web | 79 | 0 | 76 s | 16.5 min | 3.0 M (414 K uncached) | 49 K |
| Neither | 0 | 0 | 75 s | 16.7 min | 1.1 M (158 K uncached) | 53 K |

The skill was picked up in all 22 plugin runs and every one of them called the MCP server; no baseline run touched Telegram Dev files. With web access, the plugin replaced about half of the web lookups but added input tokens and roughly 13% wall time.

## How it was run

- **Tasks:** [tasks.json](tasks.json) — 11 requests in Russian, each with a rubric of facts that must appear and claims that must not. Seven Telegram tasks are taken from or close to [tests/behavioral-cases.json](../tests/behavioral-cases.json); four are TON tasks. Every rubric fact was checked against the official page in `sources` on 2026-11-10 before any agent run, and the rubrics were not changed after the runs.
- **Projects:** one fresh git project per task and configuration under `/tmp`, `codex exec --json -s read-only`, the same prompt and model settings everywhere, the project trusted with `-c projects={"<dir>"={trust_level="trusted"}}` (Codex loads project MCP servers only for trusted directories).
  - *Telegram Dev:* `uvx --from telegram-dev==0.5.0 telegram-dev install --agent codex` in the project (skill in `.agents/skills`, MCP server in `.codex/config.toml`).
  - *Baseline:* the same empty project with nothing installed.
  - *Web:* Codex's default web access — its `web_search` tool and built-in connectors that open pages (`search_service.web_run`) and GitHub files (`github.fetch`). *No web:* `-c web_search="disabled" --disable apps`; the read-only sandbox also blocks network for shell commands. The Telegram Dev MCP server runs outside the sandbox and still reaches the documentation.
- **Isolation:** Codex ran from a temporary `CODEX_HOME` with only a copy of `auth.json` and the model settings (`--isolated-home`), so the machine's global `AGENTS.md`, skills and MCP servers were invisible to every configuration. The grader flags any baseline command touching Telegram Dev files; there were none.
- **Documentation cache:** a full `telegram-dev sync --max-pages 0` was started before the runs and took 16 minutes (about 7,100 pages, 463 of them TON). The with-web plugin runs happened while it was still filling, so their MCP server fetched missing pages on demand; the no-web runs had the complete cache.
- **Grading:** [grade.py](grade.py) runs the rubric patterns over the final answer. Then every answer was read; the reading decides `manual` facts and every "must not" claim, and corrects patterns that missed a fact written differently (for example the `ton_proof` digest written as `Buffer.from([0xff, 0xff])`). The patterns never decided a "must not".

## Limitations

- **One model, one agent, small sample.** 11 tasks, one run per task and configuration plus 6 repeats. Every answer was read, but by the same AI agent that wrote the rubrics for the plugin's author, not by an independent reviewer; the transcripts are published so anyone can re-grade them.
- **The model is recent and strong.** `gpt-6.1-sol` already knew most of the facts. A model with an older cutoff, a smaller model or a lower reasoning effort may gain more from the plugin; this was not measured.
- **Codex's web access is unusually good.** It opened core.telegram.org and docs.ton.org directly. Agents without web access, or with search that returns stale snippets, are the case where the measured gain appears.
- **Answers, not running code.** Nothing was executed against Telegram or TON; correctness means agreement with the official documentation on 2026-11-10.
- **Rubrics measure required facts, not overall quality.** Differences such as WalletTg support in `ton_proof` are described above but not scored.
- **Claude Code and Cursor were not measured.**

## Code tasks — 2026-11-10 (telegram-dev 0.7.0 and 0.8.0)

Ten code-writing tasks in [code-tasks.json](code-tasks.json), mostly on recent Bot API features (button `style` and `icon_custom_emoji_id`, ephemeral replies, `sendWidget`, quizzes with several correct answers, `reply_parameters`, `link_preview_options`, albums, Stars invoice links, topics in private chats, copy-text buttons). The agent writes Python with httpx against the raw Bot API and ends with the exact requests its code sends. [grade_code.py](grade_code.py) grades automatically: each task has a `valid` check (every request passes the official Bot API 10.4 schema with no errors) and request checks for the method and key fields — 26 checks in total. Expected values were checked against core.telegram.org/bots/api on the run date, and a reference answer for every task passes the grader. Codex CLI 0.167.0, one run per task and configuration.

| | Telegram Dev 0.8.0 | Telegram Dev 0.7.0 | No plugin |
| --- | --- | --- | --- |
| With Codex web access | 26/26 | 26/26 | 26/26 |
| Without web access | 26/26 | 26/26 | 23/26 |

- **With web access every configuration got every check right.** On these tasks a strong agent with good web search does not need the plugin to be correct. 0.8.0 is not more accurate than 0.7.0 here.
- **Without web access the plugin closed the gap.** Plain Codex said that the Bot API cannot send a message visible to only one group member (ephemeral messages arrived in Bot API 10.3) and that an HTML widget cannot be sent inside a message (`sendWidget`, Bot API 10.4), and offered workarounds.
- **The new tools were used.** 0.8.0 agents called `check_bot_api_call` in most tasks (9 calls with web, 11 without) and `get_bot_api_definition` instead of part of the page reads. Every check they ran passed on the first try: the agents had already read the right definitions, so the checker confirmed requests but never had to correct one. With web access they used about 30% more uncached input tokens than 0.7.0 (360 K against 278 K) and a similar median time (50 s against 47 s).
- The validity check uses the same schema code the 0.8.0 agents can call, so it is not independent of the plugin. It was verified separately (see [docs/validation.md](../docs/validation.md)): aiogram cross-check, a valid payload for every method and 502 broken payloads detected.

Results per run: `runs/2026-11-10-code/<version>/code-results.json`; transcripts next to them.

### Questions rerun with 0.8.0

The 11 questions above were run again with telegram-dev 0.8.0 (configs with and without web, one run each) and graded with the same rubrics and the same strictness ([grades.json](runs/2026-11-10-qa-0.8.0/grades.json)): 45/47 facts and 9/11 fully correct in both configurations, no wrong claims — the same as 0.5.0. One qualitative change not covered by a rubric: in `ton-proof-login` without web, the 0.8.0 answer accepted only V3R1–V5R1 wallet contracts and only mentioned in a sentence that WalletTg needs a separate check, while the earlier plugin runs verified WalletTg in code; the 0.8.0 run with web still did. With one run per configuration this may be run-to-run variation.

## Reproduce

```sh
uv run --frozen python evals/run_codex.py --out evals/runs/<date> --isolated-home
uv run --frozen python evals/run_codex.py --out evals/runs/<date> --isolated-home --configs plugin-noweb baseline-noweb
uv run --frozen python evals/grade.py evals/runs/<date>

# code tasks
uv run --frozen python evals/run_codex.py --tasks evals/code-tasks.json --out evals/runs/<date>-code/<version> --isolated-home --configs plugin baseline --spec telegram-dev==<version>
uv run --frozen python evals/grade_code.py evals/runs/<date>-code/<version>
```

`run_codex.py` needs Python 3.11+ (`uv run` provides it), a logged-in Codex CLI and `uvx`. `grade.py` lists the answers that still need a manual decision; record them in `<run>/grades.json` (see the existing file for the format) and run it again. `--show <task>.<config>.<run>` prints one final answer.
