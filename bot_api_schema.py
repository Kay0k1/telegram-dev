"""Machine-readable Bot API schema built from the cached official page.

The Bot API page (https://core.telegram.org/bots/api) is stored as Markdown by
telegram_knowledge. Every method and type is a level-4 heading followed by a
description and, for most of them, a table of parameters or fields. This module
turns that Markdown into a schema and checks request payloads against it.
Nothing here is hand-written per method: the schema follows the page.
"""
from __future__ import annotations

import difflib
import json
import re

PAGE = "https://core.telegram.org/bots/api"

_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_HEADING = re.compile(r"^#### ([A-Za-z][A-Za-z0-9_]*)\s*$", re.M)
_VERSION = re.compile(r"\*\*Bot API (\d+(?:\.\d+)*)\*\*")
_QUOTED = re.compile(r"[“\"]([^”\"]{1,64})[”\"]")
_RANGE = re.compile(r"\b(\d+)\s*-\s*(\d+)\s+(characters|bytes)\b")
_PRIMITIVES = {"Integer", "Float", "Float number", "String", "Boolean", "True", "InputFile"}


def _plain(text):
    """Markdown cell → plain text: drop links, emphasis and escapes."""
    text = _LINK.sub(r"\1", text)
    text = text.replace("\\_", "_").replace("\\*", "*").replace("\\<", "<").replace("\\>", ">")
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    return re.sub(r"(?<![\w*])\*([^*\n]+?)\*(?![\w*])", r"\1", text).strip()


def _cells(line):
    return [part.strip() for part in line.strip().strip("|").split(" | ")]


def _constraints(description):
    """Constant, enum and length hints stated in a raw Markdown field description."""
    description = _LINK.sub(r"\1", description).replace("\\_", "_")
    found = {}
    constant = re.search(r"\b(?:must be|always)\s+[*“\"]([A-Za-z0-9_]+)[*”\"]", description)
    if constant and not re.search(r"must be one of|one of", description[: constant.end()], re.I):
        found["const"] = constant.group(1)
    enum = re.search(r"(?:[Mm]ust be one of|[Cc]urrently,? (?:must|can) be one of|[Mm]ust be either)\s+(.+?)(?:\.\s|\.$|$)", description)
    if enum:
        values = _QUOTED.findall(enum.group(1))
        if len(values) >= 2:
            found["enum"] = values
    length = _RANGE.search(description)
    if length:
        found["length"] = {"min": int(length.group(1)), "max": int(length.group(2)), "unit": length.group(3)}
    unless = re.search(r"\brequired unless\b[^.;]*", _plain(description), re.I)
    if unless:
        found["required_unless"] = unless.group(0).strip()
    return found


def parse(body):
    """Return {'version', 'methods', 'types'} from the Bot API page Markdown."""
    version = _VERSION.search(body)
    schema = {"version": version.group(1) if version else None, "methods": {}, "types": {}}
    headings = list(_HEADING.finditer(body))
    for index, heading in enumerate(headings):
        name = heading.group(1)
        end = headings[index + 1].start() if index + 1 < len(headings) else len(body)
        # A level-3 heading ends the block (for example "### Updating messages").
        block = body[heading.end():end]
        cut = re.search(r"^#{1,3} ", block, re.M)
        if cut:
            block = block[:cut.start()]
        lines = block.strip().splitlines()
        table_start = next((i for i, line in enumerate(lines) if line.startswith("| ")), None)
        prose = "\n".join(lines[:table_start] if table_start is not None else lines).strip()
        description = _plain(re.sub(r"\s+", " ", prose.split("\n\n")[0]))
        anchor = f"{PAGE}#{name.lower()}"
        rows = []
        header = []
        if table_start is not None:
            header = [_plain(cell) for cell in _cells(lines[table_start])]
            for line in lines[table_start + 2:]:
                if not line.startswith("|"):
                    break
                rows.append(_cells(line))
        if name[0].islower():
            if header[:3] != ["Parameter", "Type", "Required"] and table_start is not None:
                continue
            returns = re.search(r"(?:On success|Returns)[^.]*\.", description)
            params = {}
            for row in rows:
                if len(row) < 4:
                    continue
                params[_plain(row[0])] = {"type": _plain(row[1]), "required": _plain(row[2]) == "Yes",
                                          "description": _plain(row[3]), **_constraints(row[3])}
            schema["methods"][name] = {"name": name, "url": anchor, "description": description,
                                       "returns": returns.group(0) if returns else None, "params": params}
        else:
            members = [_plain(item) for item in re.findall(r"^\* (\[[A-Za-z0-9_]+\]\([^)]*\))\s*$", prose, re.M)]
            fields = {}
            if header[:2] == ["Field", "Type"]:
                for row in rows:
                    if len(row) < 3:
                        continue
                    text = _plain(row[2])
                    fields[_plain(row[0])] = {"type": _plain(row[1]), "required": not text.startswith("Optional."),
                                              "description": text, **_constraints(row[2])}
            entry = {"name": name, "url": anchor, "description": description, "fields": fields}
            if members and not fields:
                entry["one_of"] = members
            schema["types"][name] = entry
    return schema


def _alternatives(expression):
    return [part.strip() for part in re.split(r"\s+or\s+|\s+and\s+|\s*,\s*", expression) if part.strip()]


def _suggest(name, names):
    return difflib.get_close_matches(name, names, n=3, cutoff=0.6)


class _Checker:
    def __init__(self, schema, releases=None):
        self.schema = schema
        self.releases = releases or []
        self.errors = []
        self.warnings = []

    def report(self, level, path, message):
        (self.errors if level == "error" else self.warnings).append({"path": path, "message": message})

    def value(self, value, expression, path, spec=None):
        if expression.startswith("Array of "):
            if isinstance(value, str):
                value = self._json(value, path)
                if value is None:
                    return
            if not isinstance(value, list):
                self.report("error", path, f"expected {expression}, got {type(value).__name__}")
                return
            inner = expression[len("Array of "):]
            for i, item in enumerate(value):
                self.value(item, inner, f"{path}[{i}]")
            return
        options = _alternatives(expression)
        if len(options) > 1:
            self.union(value, options, path, expression)
        else:
            self.single(value, options[0], path, spec)

    def single(self, value, name, path, spec=None):
        spec = spec or {}
        if name in ("Integer",):
            if isinstance(value, bool) or not isinstance(value, int):
                if isinstance(value, str) and re.fullmatch(r"-?\d+", value):
                    self.report("warning", path, "Integer sent as a string; send a number")
                else:
                    self.report("error", path, f"expected Integer, got {type(value).__name__}")
        elif name in ("Float", "Float number"):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                self.report("error", path, f"expected Float, got {type(value).__name__}")
        elif name == "Boolean":
            if not isinstance(value, bool):
                if value in ("true", "false"):
                    self.report("warning", path, "Boolean sent as a string; send true or false")
                else:
                    self.report("error", path, f"expected Boolean, got {type(value).__name__}")
        elif name == "True":
            if value is not True:
                self.report("error", path, "expected true")
        elif name in ("String", "InputFile"):
            if not isinstance(value, str):
                self.report("error", path, f"expected {name}, got {type(value).__name__}")
                return
            if "const" in spec and value != spec["const"]:
                self.report("error", path, f"must be {spec['const']!r}")
            if "enum" in spec and value not in spec["enum"]:
                self.report("error", path, f"must be one of {', '.join(spec['enum'])}")
            if "length" in spec:
                limits = spec["length"]
                size = len(value.encode("utf-8")) if limits["unit"] == "bytes" else len(value)
                if not limits["min"] <= size <= limits["max"]:
                    counted = "" if limits["unit"] == "bytes" else " (counted before entity parsing)"
                    self.report("warning", path, f"length {size} {limits['unit']}{counted} outside {limits['min']}-{limits['max']}")
        elif name in self.schema["types"]:
            self.object(value, self.schema["types"][name], path)
        else:
            self.report("warning", path, f"type {name} is not described on the Bot API page; not checked")

    def _discriminate(self, value, options, path):
        """Pick the member of a union by its constant field (type, status, source)."""
        if not isinstance(value, dict):
            return None
        types = self.schema["types"]
        if not all(option in types and types[option]["fields"] for option in options):
            return None
        for key in ("type", "status", "source"):
            consts = {types[option]["fields"].get(key, {}).get("const"): option for option in options}
            if None in consts or len(consts) != len(options):
                continue
            if value.get(key) in consts:
                return consts[value[key]]
            self.report("error", f"{path}.{key}" if path else key,
                        f"must be one of {', '.join(sorted(consts))}" if key in value else f"required field {key!r} is missing")
            return False
        return None

    def union(self, value, options, path, expression):
        chosen = self._discriminate(value, options, path)
        if chosen is False:
            return
        if chosen:
            self.single(value, chosen, path)
            return
        attempts = []
        for option in options:
            trial = _Checker(self.schema, self.releases)
            trial.single(value, option, path)
            if not trial.errors and not trial.warnings:
                return
            attempts.append(trial)
        clean = [trial for trial in attempts if not trial.errors]
        if clean:
            self.warnings.extend(clean[0].warnings)
            return
        best = min(attempts, key=lambda trial: len(trial.errors))
        if all(len(trial.errors) == 1 and trial.errors[0]["path"] == path for trial in attempts):
            self.report("error", path, f"expected {expression}, got {type(value).__name__}")
        else:
            self.errors.extend(best.errors)
            self.warnings.extend(best.warnings)

    def object(self, value, definition, path):
        if isinstance(value, str):
            value = self._json(value, path)
            if value is None:
                return
        if "one_of" in definition:
            self.union(value, definition["one_of"], path, " or ".join(definition["one_of"]))
            return
        if not isinstance(value, dict):
            self.report("error", path, f"expected {definition['name']} object, got {type(value).__name__}")
            return
        self.fields(value, definition["fields"], path, definition["name"], "field")

    def fields(self, value, specs, path, owner, kind):
        prefix = f"{path}." if path else ""
        for key, item in value.items():
            if key not in specs:
                gone = retired(self.releases, owner, key)
                if gone:
                    self.report("warning", prefix + key, f"{key!r} is no longer in the {owner} docs (Bot API "
                                f"{gone['version'] or gone['date']}): {gone['text']}")
                    continue
                hint = _suggest(key, list(specs))
                more = f"; did you mean {', '.join(hint)}?" if hint else ""
                self.report("error", prefix + key, f"{owner} has no {kind} {key!r}{more}")
                continue
            if item is None:
                continue
            self.value(item, specs[key]["type"], prefix + key, specs[key])
        for key, spec in specs.items():
            if key in value:
                continue
            if spec["required"]:
                self.report("error", prefix + key, f"required {kind} of {owner} is missing")
            elif spec.get("required_unless"):
                self.report("warning", prefix + key, f"not sent; that is fine only if this does not apply: {spec['required_unless']}")

    def _json(self, text, path):
        try:
            return json.loads(text)
        except ValueError:
            self.report("error", path, "expected a JSON-serialized object or array")
            return None


def check(schema, method, params, releases=None):
    """Validate one Bot API call against the schema; the changelog explains retired names."""
    methods = schema["methods"]
    if method not in methods:
        lowered = {name.lower(): name for name in methods}
        if method.lower() in lowered:
            return {"valid": False, "method": method, "errors": [{"path": "", "message":
                    f"method names are case-sensitive; use {lowered[method.lower()]}"}], "warnings": []}
        hint = _suggest(method, list(methods))
        more = f"; did you mean {', '.join(hint)}?" if hint else ""
        return {"valid": False, "method": method, "errors": [{"path": "", "message":
                f"the Bot API has no method {method!r}{more}"}], "warnings": []}
    if not isinstance(params, dict):
        return {"valid": False, "method": method, "errors": [{"path": "", "message": "params must be an object"}], "warnings": []}
    checker = _Checker(schema, releases)
    checker.fields(params, methods[method]["params"], "", method, "parameter")
    return {"valid": not checker.errors, "method": method, "url": methods[method]["url"],
            "errors": checker.errors, "warnings": checker.warnings}


def definition(schema, name):
    """Method or type definition by exact or case-insensitive name, with suggestions otherwise."""
    for kind in ("methods", "types"):
        if name in schema[kind]:
            return {"kind": kind[:-1], **schema[kind][name]}
    everything = {**schema["methods"], **schema["types"]}
    lowered = {key.lower(): key for key in everything}
    if name.lower() in lowered:
        return definition(schema, lowered[name.lower()])
    return {"kind": None, "name": name, "suggestions": _suggest(name, list(everything))}


CHANGELOG = "https://core.telegram.org/bots/api-changelog"
_API_REF = re.compile(r"\[([^\]]+)\]\(https://core\.telegram\.org/bots/api#[^)]*\)")
_ITALIC = re.compile(r"\*([A-Za-z][A-Za-z0-9\\_]*)\*")


def version_key(version):
    try:
        return tuple(int(part) for part in str(version).split("."))
    except ValueError:
        return (0,)


def parse_changelog(body):
    """Releases newest first: date, Bot API version, changelog anchor and changes."""
    releases = []
    blocks = re.split(r"^#### ", body, flags=re.M)[1:]
    for block in blocks:
        title, _, rest = block.partition("\n")
        title = title.strip()
        rest = re.split(r"^#{1,3} ", rest, flags=re.M)[0]
        version = _VERSION.search(rest)
        topic = None
        changes = []
        for line in rest.splitlines():
            stripped = line.strip()
            heading = re.fullmatch(r"\*\*([^*]+)\*\*", stripped)
            if heading and not heading.group(1).startswith("Bot API"):
                topic = heading.group(1)
                continue
            if not stripped.startswith("* "):
                continue
            raw = stripped[2:]
            changes.append({"text": _plain(raw), "topic": topic,
                            "refs": sorted(set(_API_REF.findall(raw))),
                            "terms": sorted({term.replace("\\_", "_") for term in _ITALIC.findall(raw)})})
        anchor = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        releases.append({"date": title, "version": version.group(1) if version else None,
                         "url": f"{CHANGELOG}#{anchor}", "changes": changes})
    return releases


def changes(releases, since="", name="", limit=None):
    """Changelog entries newer than `since`, optionally only those mentioning `name`."""
    wanted = name.lower()
    selected = []
    for release in releases:
        if since and (not release["version"] or version_key(release["version"]) <= version_key(since)):
            continue
        entries = [change for change in release["changes"] if not wanted
                   or wanted in {ref.lower() for ref in change["refs"]}
                   or wanted in {term.lower() for term in change["terms"]}]
        if entries:
            selected.append({**release, "changes": entries})
        if limit and len(selected) >= limit:
            break
    return selected


def retired(releases, owner, name):
    """Latest changelog entry that removed or replaced `name` of method/type `owner`."""
    for release in releases:
        for change in release["changes"]:
            if name in change["terms"] and owner in change["refs"] and re.search(
                    r"\b(?:[Rr]eplac(?:ed|ing)|[Rr]emov(?:ed|ing)|[Rr]enam(?:ed|ing)|[Dd]eprecat(?:ed|ing))\b", change["text"]):
                return {"version": release["version"], "date": release["date"], "url": release["url"], "text": change["text"]}
    return None
