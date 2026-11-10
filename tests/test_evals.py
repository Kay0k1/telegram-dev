import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path

EVALS = Path(__file__).resolve().parents[1] / "evals"


def load_grader():
    spec = importlib.util.spec_from_file_location("eval_grade", EVALS / "grade.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless((EVALS / "tasks.json").exists(), "evals/ is not part of the source distribution")
class EvalTests(unittest.TestCase):
    def test_tasks_are_well_formed(self):
        tasks = json.loads((EVALS / "tasks.json").read_text(encoding="utf-8"))["tasks"]
        self.assertEqual(len({task["id"] for task in tasks}), len(tasks))
        for task in tasks:
            self.assertTrue(task["prompt"] and task["sources"] and task["must"], task["id"])
            facts = task["must"] + task["must_not"]
            self.assertEqual(len({fact["id"] for fact in facts}), len(facts), task["id"])
            for fact in facts:
                self.assertTrue(fact.get("patterns") or fact.get("manual") or fact in task["must_not"], fact["id"])
                for pattern in fact.get("patterns", []):
                    re.compile(pattern)

    def test_grading_uses_answer_patterns_and_manual_decisions(self):
        grade = load_grader()
        task = {"id": "t", "must": [{"id": "a", "patterns": ["10\\.4"]}, {"id": "b", "manual": True}],
                "must_not": [{"id": "x"}]}
        events = [
            {"type": "item.completed", "item": {"type": "agent_message", "text": "checking"}},
            {"type": "item.completed", "item": {"type": "mcp_tool_call", "server": "telegram-knowledge",
                                                "tool": "search_telegram_docs"}},
            {"type": "item.completed", "item": {"type": "mcp_tool_call", "server": "codex_apps",
                                                "tool": "search_service.web_run"}},
            {"type": "item.completed", "item": {"type": "mcp_tool_call", "server": "codex",
                                                "tool": "list_mcp_resources"}},
            {"type": "item.completed", "item": {"type": "agent_message", "text": "Bot API 10.4"}},
            {"type": "turn.completed", "usage": {"input_tokens": 5, "output_tokens": 2}},
        ]
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            (run / "transcripts").mkdir()
            (run / "transcripts" / "t.plugin.1.jsonl").write_text(
                "\n".join(json.dumps(event) for event in events), encoding="utf-8")
            pending = grade.grade(run, [task], {})[0]
            self.assertTrue(pending["must"]["a"]["final"])
            self.assertEqual(pending["pending"], ["must:b", "must_not:x"])
            self.assertFalse(pending["correct"])
            self.assertEqual((pending["mcp_calls"], pending["web_searches"]), (1, 1))
            done = grade.grade(run, [task], {"t.plugin.1": {"must": {"b": True}, "must_not": {"x": False}}})[0]
            self.assertTrue(done["correct"])
            self.assertEqual((done["facts"], done["facts_total"], done["violations"]), (2, 2, 0))


if __name__ == "__main__":
    unittest.main()
