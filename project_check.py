"""Check a bot project's Bot API usage against the current official schema.

Static analysis of Python code (aiogram, python-telegram-bot, pyTelegramBotAPI and raw HTTP calls
to api.telegram.org). One run reads the whole project and returns only findings, so an agent or a
CI job gets a short report instead of reading documentation.

What it reports:
- errors: values outside the documented list (`style="red"`), unknown methods in raw API URLs,
  unknown parameters in raw API requests;
- warnings: parameters and fields that Telegram retired, with the Bot API version and the
  changelog entry that replaced them; keyword arguments that are neither Bot API parameters nor
  known library options; bot methods with no Bot API counterpart.

What it does not do: decide whether a required parameter is missing (libraries fill some in and
positional arguments are not mapped), follow variables, or run any code.
"""
from __future__ import annotations

import ast
import fnmatch
import os
import warnings
from dataclasses import dataclass, asdict
import re
from pathlib import Path

import bot_api_schema

LIBRARY_MARKERS = {
    "aiogram": re.compile(r"^\s*(?:from|import)\s+aiogram\b", re.M),
    "python-telegram-bot": re.compile(r"^\s*(?:from|import)\s+telegram\b", re.M),
    "pyTelegramBotAPI": re.compile(r"^\s*(?:from|import)\s+telebot\b", re.M),
}
RAW_URL = re.compile(r"api\.telegram\.org/bot")
# Keyword arguments that libraries accept on top of Bot API parameters.
LIBRARY_OPTIONS = {
    "read_timeout", "write_timeout", "connect_timeout", "pool_timeout", "api_kwargs", "rate_limit_args",
    "quote", "do_quote", "filename", "request_timeout", "timeout", "self", "kwargs",
    "row_width", "visible_file_name",
}
# Convenience arguments that a library accepts on specific methods (python-telegram-bot).
LIBRARY_METHOD_OPTIONS = {
    "sendLocation": {"location"}, "editMessageLiveLocation": {"location"}, "sendVenue": {"venue"},
    "sendContact": {"contact"}, "answerInlineQuery": {"current_offset", "auto_pagination"},
    "sendMediaGroup": {"caption", "parse_mode", "caption_entities"},
}
TELEGRAM_MODULES = ("aiogram", "telegram", "telebot")
# Modules whose classes are Bot API types (not filters, handlers or the project's own models).
TYPE_MODULES = ("aiogram.types", "aiogram", "telegram", "telebot.types", "telebot")


def _is_type_module(path):
    return path in TYPE_MODULES or path.startswith("aiogram.types.")
# Shortcut methods on Message, CallbackQuery and similar objects, mapped to the Bot API methods
# they may call. A keyword is unknown only if none of the candidates accepts it.
SHORTCUTS = {
    "answer": ("sendMessage", "answerCallbackQuery", "answerInlineQuery", "answerPreCheckoutQuery",
               "answerShippingQuery", "answerWebAppQuery"),
    "reply": ("sendMessage",), "reply_text": ("sendMessage",), "reply_html": ("sendMessage",),
    "reply_markdown": ("sendMessage",), "reply_markdown_v2": ("sendMessage",), "reply_to": ("sendMessage",),
    "edit_text": ("editMessageText",), "edit_caption": ("editMessageCaption",), "edit_media": ("editMessageMedia",),
    "edit_reply_markup": ("editMessageReplyMarkup",), "edit_live_location": ("editMessageLiveLocation",),
    "copy_to": ("copyMessage",), "copy": ("copyMessage",), "forward": ("forwardMessage",),
    "pin": ("pinChatMessage",), "unpin": ("unpinChatMessage",), "react": ("setMessageReaction",),
    "set_reaction": ("setMessageReaction",),
}
SHORTCUT_PREFIXES = ("answer_", "reply_")
BOT_RECEIVER = re.compile(r"(?:^|\.)(?:bot|_bot|telegram_bot|tg_bot)$")
KEYBOARD_RECEIVER = re.compile(r"(?:^|[._])(?:kb|keyboard|markup|builder)\w*$", re.I)
BOT_VERBS = ("send_", "get_", "set_", "edit_", "delete_", "answer_", "ban_", "unban_", "restrict_", "promote_",
             "pin_", "unpin_", "copy_", "forward_", "create_", "export_", "revoke_", "approve_", "decline_",
             "leave_", "upload_", "add_", "replace_", "refund_", "verify_", "remove_", "post_", "gift_",
             "read_", "convert_", "upgrade_", "transfer_", "repost_", "stop_", "hide_", "reopen_", "close_")
SKIP_DIRS = {".git", ".venv", "venv", "env", "node_modules", "site-packages", "__pycache__", "build", "dist", ".tox"}
POETRY = re.compile(r"(?im)^\s*(aiogram|python-telegram-bot|pytelegrambotapi)\s*=\s*(?:\{[^}]*?version\s*=\s*)?[\"']([\^~<>=!]*\s*[\w.*]+)[\"']")
REQUIREMENT = re.compile(r"(?im)(?:^|[\"'\[,]\s*)(aiogram|python-telegram-bot|pytelegrambotapi)\s*(?:\[[^\]]*\])?\s*([<>=!~]=?\s*[\w.*]+)?(?=\s*(?:[\"',;#\]]|$))")


@dataclass
class Finding:
    file: str
    line: int
    severity: str
    call: str
    message: str


def snake(name):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


class _Unknown:
    def __repr__(self):
        return "<unknown>"


UNKNOWN = _Unknown()


def literal(node):
    """AST node → Python value; anything that is not a literal becomes UNKNOWN."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Dict):
        result = {}
        for key, value in zip(node.keys, node.values):
            if key is None:
                return UNKNOWN
            name = literal(key)
            if not isinstance(name, str):
                return UNKNOWN
            result[name] = literal(value)
        return result
    if isinstance(node, (ast.List, ast.Tuple)):
        return [literal(item) for item in node.elts]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub) and isinstance(node.operand, ast.Constant):
        return -node.operand.value if isinstance(node.operand.value, (int, float)) else UNKNOWN
    return UNKNOWN


def _strip_unknown(value):
    """Drop UNKNOWN parts so the schema checker only sees literal values."""
    if isinstance(value, dict):
        return {key: _strip_unknown(item) for key, item in value.items() if item is not UNKNOWN}
    if isinstance(value, list):
        return [_strip_unknown(item) for item in value if item is not UNKNOWN]
    return value


def _call_name(func):
    if isinstance(func, ast.Attribute):
        base = _call_name(func.value)
        return f"{base}.{func.attr}" if base else func.attr
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Call):
        return _call_name(func.func) + "()"
    return ""


def _raw_method(node):
    """Bot API method name from a literal or f-string URL to api.telegram.org."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        text = node.value
    elif isinstance(node, ast.JoinedStr):
        text = "".join(part.value if isinstance(part, ast.Constant) else "{}" for part in node.values)
    else:
        return None
    match = re.search(r"api\.telegram\.org/bot[^/]*/([A-Za-z]+)\s*$", text)
    return match.group(1) if match else None


def telegram_imports(tree):
    """Local names bound to Telegram library modules or objects, e.g. {'types': 'aiogram.types'}."""
    names = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in TELEGRAM_MODULES:
                    if alias.asname:
                        names[alias.asname] = alias.name
                    else:
                        names[alias.name.split(".")[0]] = alias.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] in TELEGRAM_MODULES:
            for alias in node.names:
                names[alias.asname or alias.name] = f"{node.module}.{alias.name}"
    return names


class _Visitor(ast.NodeVisitor):
    def __init__(self, checker, path, raw_enabled, imports, libraries):
        self.checker = checker
        self.path = path
        self.raw_enabled = raw_enabled
        self.imports = imports
        self.libraries = libraries

    def visit_Call(self, node):
        self.checker.check_call(self.path, node, self.raw_enabled, self.imports, self.libraries)
        self.generic_visit(node)


class ProjectChecker:
    def __init__(self, schema, releases):
        self.schema = schema
        self.releases = releases
        self.methods = schema["methods"]
        self.types = schema["types"]
        self.by_snake = {snake(name): name for name in self.methods}
        self.findings = []

    def add(self, path, node, severity, call, message):
        self.findings.append(Finding(str(path), getattr(node, "lineno", 0), severity, call, message))

    # -- parameter checks -------------------------------------------------------------------
    def _params(self, owner):
        if owner in self.methods:
            return self.methods[owner]["params"]
        return self.types[owner]["fields"]

    def check_keywords(self, path, node, call, owners, raw, strict=True):
        """Check keyword arguments of a call against the parameters of the candidate owners."""
        for keyword in node.keywords:
            name = keyword.arg
            if name is None or name in LIBRARY_OPTIONS or any(name in LIBRARY_METHOD_OPTIONS.get(owner, ()) for owner in owners):
                continue
            accepting = [owner for owner in owners if name in self._params(owner)]
            if name == "from_user":
                continue
            if not accepting:
                gone = next((found for found in (bot_api_schema.retired(self.releases, owner, name) for owner in owners) if found), None)
                if gone:
                    self.add(path, keyword, "warning", call,
                             f"`{name}` was retired in Bot API {gone['version'] or gone['date']}: {gone['text']}"
                             + ("" if raw else " Check that your library version still converts it."))
                elif strict:
                    names = sorted({param for owner in owners for param in self._params(owner)})
                    hint = bot_api_schema._suggest(name, names)
                    more = f"; did you mean {', '.join(hint)}?" if hint else ""
                    target = " / ".join(owners)
                    if raw:
                        self.add(path, keyword, "error", call, f"{target} has no parameter `{name}`{more}")
                    else:
                        self.add(path, keyword, "warning", call, f"`{name}` is not a Bot API parameter of {target}{more}; "
                                 "fine if it is an option of your library")
                continue
            self.check_value(path, keyword, call, accepting, name, literal(keyword.value))

    def check_value(self, path, node, call, owners, name, value):
        if value is UNKNOWN or value is None:
            return
        best = None
        for owner in owners:
            spec = self._params(owner)[name]
            checker = bot_api_schema._Checker(self.schema, self.releases)
            checker.value(_strip_unknown(value), spec["type"], name, spec)
            # Library calls accept their own objects and strings for nested types; only literal
            # mismatches with documented values are reported.
            errors = [error for error in checker.errors if "must be" in error["message"] or "has no field" in error["message"]]
            if best is None or len(errors) < len(best):
                best = errors
            if not errors:
                return
        for error in best or []:
            self.add(path, node, "error", call, f"{error['path']}: {error['message']}")

    def check_type_constructor(self, path, node, call, type_name):
        if "one_of" in self.types[type_name]:
            return
        self.check_keywords(path, node, call, [type_name], raw=False)

    # -- call dispatch ------------------------------------------------------------------------
    def check_call(self, path, node, raw_enabled, imports=None, libraries=()):
        imports = imports or {}
        call = _call_name(node.func)
        attr = node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id if isinstance(node.func, ast.Name) else None
        if attr is None:
            return
        if raw_enabled:
            for argument in [*node.args[:1], *[keyword.value for keyword in node.keywords if keyword.arg == "url"]]:
                method = _raw_method(argument)
                if method is not None:
                    self.check_raw(path, node, call, method)
                    return
        receiver = _call_name(node.func.value) if isinstance(node.func, ast.Attribute) else ""
        if attr in self.types and attr[0].isupper():
            # Only classes that come from a Telegram library, not a project's own User or Chat model.
            if receiver:
                source = imports.get(receiver.split(".")[0], "")
                module = ".".join([source, *receiver.split(".")[1:]]) if source else ""
                resolved = _is_type_module(module)
            else:
                source = imports.get(attr, "")
                resolved = bool(source) and _is_type_module(source.rsplit(".", 1)[0])
            if resolved:
                self.check_type_constructor(path, node, call, attr)
            return
        if not isinstance(node.func, ast.Attribute):
            return
        on_bot = bool(BOT_RECEIVER.search(receiver))
        if attr == "button":
            if on_bot or receiver.split(".")[0] in imports or KEYBOARD_RECEIVER.search(receiver):
                self.check_keywords(path, node, call, ["InlineKeyboardButton", "KeyboardButton"], raw=False)
            return
        method = self.by_snake.get(attr) or (attr if attr in self.methods and attr[0].islower() else None)
        if method:
            # Single-word names (close, ...) collide with other libraries; check them only on a bot.
            if on_bot or "_" in attr or any(char.isupper() for char in attr):
                self.check_keywords(path, node, call, [method], raw=False, strict=on_bot)
            return
        if attr in SHORTCUTS:
            owners = [method for method in SHORTCUTS[attr] if method in self.methods]
            if owners:
                self.check_keywords(path, node, call, owners, raw=False, strict=False)
            return
        if attr.startswith(SHORTCUT_PREFIXES):
            target = self.by_snake.get("send_" + attr.split("_", 1)[1])
            if target:
                self.check_keywords(path, node, call, [target], raw=False, strict=False)
            return
        if on_bot and "pyTelegramBotAPI" not in libraries and attr.startswith(BOT_VERBS) and attr not in self.by_snake:
            camel = re.sub(r"_([a-z])", lambda match: match.group(1).upper(), attr)
            hint = bot_api_schema._suggest(camel, list(self.methods))
            more = f"; did you mean {', '.join(hint)}?" if hint else ""
            self.add(path, node, "warning", call, f"the Bot API has no method `{camel}`{more} Fine if it is a helper of your library.")

    def check_raw(self, path, node, call, method):
        # Method names are case-insensitive in the Bot API.
        method = {name.lower(): name for name in self.methods}.get(method.lower(), method)
        if method not in self.methods:
            hint = bot_api_schema._suggest(method, list(self.methods))
            more = f"; did you mean {', '.join(hint)}?" if hint else ""
            self.add(path, node, "error", call, f"the Bot API has no method `{method}`{more}")
            return
        for keyword in node.keywords:
            if keyword.arg in ("json", "data", "params"):
                payload = literal(keyword.value)
                if isinstance(payload, dict):
                    result = bot_api_schema.check(self.schema, method, _strip_unknown(payload), self.releases)
                    # Form data and query strings carry strings, files travel in `files=`, and
                    # parameters may be split across arguments: only unknown names and values outside
                    # the documented list are reliable here.
                    for error in result["errors"]:
                        if "has no " in error["message"] or "must be" in error["message"]:
                            self.add(path, keyword, "error", call, f"{method} {error['path']}: {error['message']}")
                    for warning in result["warnings"]:
                        if "retired" in warning["message"] or "no longer" in warning["message"]:
                            self.add(path, keyword, "warning", call, f"{method} {warning['path']}: {warning['message']}")


def _walk(root, recursive=True):
    """Files under root, never entering virtual environments, VCS or build directories."""
    for directory, folders, files in os.walk(root, followlinks=False):
        folders[:] = sorted(folder for folder in folders if folder not in SKIP_DIRS and not folder.startswith(".")) if recursive else []
        for name in sorted(files):
            yield Path(directory) / name


DEPENDENCY_FILES = re.compile(r"^(requirements.*\.txt|pyproject\.toml|Pipfile|setup\.py|setup\.cfg)$")


def libraries(root, recursive=True):
    """Bot libraries and version constraints declared in dependency files."""
    found = {}
    for file in _walk(root, recursive):
        if DEPENDENCY_FILES.match(file.name):
            try:
                text = file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for name, spec in REQUIREMENT.findall(text) + POETRY.findall(text):
                key = {"pytelegrambotapi": "pyTelegramBotAPI"}.get(name.lower(), name.lower())
                found.setdefault(key, set()).add((spec or "").replace(" ", "") or "unpinned")
    return {name: sorted(specs) for name, specs in found.items()}


def check_project(root, schema, releases, max_files=5000, exclude=()):
    root = Path(root).resolve()
    if not root.exists():
        raise ValueError(f"No such file or directory: {root}")
    files = [root] if root.is_file() else [
        path for path in _walk(root) if path.suffix == ".py"
        and not any(fnmatch.fnmatch(path.relative_to(root).as_posix(), pattern) for pattern in exclude)]
    checker = ProjectChecker(schema, releases)
    scanned, skipped = 0, []
    for path in files[:max_files]:
        try:
            text = path.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        library = [name for name, marker in LIBRARY_MARKERS.items() if marker.search(text)]
        raw = bool(RAW_URL.search(text))
        if not library and not raw:
            continue
        relative = path.name if root.is_file() else path.relative_to(root).as_posix()
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                tree = ast.parse(text, filename=str(path))
            _Visitor(checker, relative, raw, telegram_imports(tree), library).visit(tree)
        except SyntaxError as exc:
            skipped.append({"file": relative, "reason": f"syntax error: {exc.msg}"})
            continue
        except (ValueError, RecursionError, MemoryError) as exc:
            skipped.append({"file": relative, "reason": f"could not be analysed: {type(exc).__name__}"})
            continue
        scanned += 1
    findings = sorted(checker.findings, key=lambda item: (item.severity != "error", item.file, item.line))
    return {
        "bot_api_version": schema["version"],
        "files_scanned": scanned,
        "libraries": libraries(root) if root.is_dir() else libraries(root.parent, recursive=False),
        "errors": sum(item.severity == "error" for item in findings),
        "warnings": sum(item.severity == "warning" for item in findings),
        "findings": [asdict(item) for item in findings],
        "skipped": skipped,
        "truncated": len(files) > max_files,
    }


def _annotation(text, prop=False):
    text = text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    return text.replace(":", "%3A").replace(",", "%2C") if prop else text


def format_report(report, style="text", base=None):
    """Plain `file:line: severity: call: message` lines, or GitHub Actions annotations."""
    if style == "github":
        lines = []
        for item in report["findings"]:
            file = f"{base}/{item['file']}" if base and base != "." else item["file"]
            lines.append(f"::{item['severity']} file={_annotation(file, prop=True)},line={item['line']},title=telegram-dev::"
                         + _annotation(f"{item['call']}: {item['message']}"))
        lines.append(f"Bot API {report['bot_api_version']}: {report['errors']} errors, {report['warnings']} warnings "
                     f"in {report['files_scanned']} files with bot code{_skipped_note(report)}")
        return "\n".join(lines)
    lines = [f"{item['file']}:{item['line']}: {item['severity']}: {item['call']}: {item['message']}" for item in report["findings"]]
    libs = ", ".join(f"{name} {' '.join(specs)}" for name, specs in report["libraries"].items()) or "none declared"
    lines.append(f"Bot API {report['bot_api_version']}; {report['files_scanned']} files with bot code; libraries: {libs}; "
                 f"{report['errors']} errors, {report['warnings']} warnings{_skipped_note(report)}")
    return "\n".join(lines)


def _skipped_note(report):
    notes = []
    if report["skipped"]:
        notes.append(f"{len(report['skipped'])} files not analysed ({', '.join(item['file'] for item in report['skipped'][:3])}"
                     + (", ..." if len(report["skipped"]) > 3 else "") + ")")
    if report["truncated"]:
        notes.append("file limit reached, not every file was checked")
    return "; " + "; ".join(notes) if notes else ""
