"""Spec loading, hashing and pre-registration enforcement (Principles.md 2.7, 2.8).

Three rules live here because none of them survives being left to discipline:

  * Validation reports EVERY missing or empty required field in one pass (2.7).
    A validator that stops at the first problem teaches the author to fix a spec
    one field per attempt; the point of 2.7 is that an incomplete spec never
    lands at all, so the author gets the whole list and fixes it once.
  * `spec_hash` is taken over a canonical form -- sorted keys, comments gone,
    every `description` dropped at every depth, numbers normalized -- so
    reformatting a spec cannot orphan its results, while moving a threshold by
    one basis point necessarily does (1.1).
  * `require_registered` is what actually stops a threshold being edited after
    the result is known: the working-tree hash must appear somewhere in this
    file's git history or the runner aborts (2.8). Philosophy does not prevent
    that edit. This does.

Timestamps are coerced to ISO-8601 strings on load, because PyYAML turns an
unquoted `2026-08-18T14:20:00Z` into a datetime and a quoted one into a string.
Quoting is formatting, and formatting must not change either validity or hash.
"""
from __future__ import annotations

import datetime as dt
import functools
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

import yaml

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "specs" / "schema" / "spec.schema.json"

_SEP = "\t"  # commit marker in `git log` output; str.splitlines() ignores it,
#               and a --name-only path is never printed leading-tab


class SpecError(Exception):
    """A spec that must not run. Never caught to 'continue anyway' (2.8)."""


# --------------------------------------------------------------------------- load


@functools.lru_cache(maxsize=4)
def _schema(path_str: str) -> dict:
    return json.loads(Path(path_str).read_text())


def _coerce(obj):
    """dates -> ISO strings, tuples -> lists. Applied before validation AND before
    hashing, so both see the same document whatever the YAML quoting was."""
    if isinstance(obj, dict):
        return {k: _coerce(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_coerce(v) for v in obj]
    if isinstance(obj, dt.datetime):
        return obj.isoformat()
    if isinstance(obj, dt.date):
        return obj.isoformat()
    return obj


def _parse(path: Path) -> dict:
    doc = yaml.safe_load(path.read_text())
    if not isinstance(doc, dict):
        raise SpecError(f"{path}: spec must be a YAML mapping, got {_typename(doc)}")
    return _coerce(doc)


def load(path, *, schema_path: Path | str = SCHEMA_PATH) -> dict:
    """Read and validate a spec. Raises SpecError listing every problem at once."""
    p = Path(path)
    try:
        spec = _parse(p)
    except FileNotFoundError:
        raise SpecError(f"{p}: no such spec") from None
    except yaml.YAMLError as e:
        raise SpecError(f"{p}: YAML will not parse -- {e}") from None
    errs = validate(spec, schema_path=schema_path)
    if errs:
        body = "\n  - ".join(errs)
        raise SpecError(
            f"{p}: {len(errs)} schema problem(s). 2.7 admits no exceptions -- "
            f"fix all of them, then commit:\n  - {body}"
        )
    return spec


def validate(spec: dict, *, schema_path: Path | str = SCHEMA_PATH) -> list[str]:
    """Every violation, sorted and de-duplicated. Empty list means valid."""
    errs: list[str] = []
    _check(spec, _schema(str(schema_path)), "", errs)
    return sorted(set(errs))


# ---------------------------------------------------------------------- validation

_TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
    "integer": int,
    "number": (int, float),
    "null": type(None),
}


def _typename(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "boolean"
    return {dict: "object", list: "array", str: "string", int: "integer",
            float: "number"}.get(type(v), type(v).__name__)


def _is_type(v, name: str) -> bool:
    if name in ("integer", "number") and isinstance(v, bool):
        return False  # a boolean is not a count, whatever Python thinks
    if name == "boolean":
        return isinstance(v, bool)
    return isinstance(v, _TYPES.get(name, ()))


def _empty(v) -> bool:
    """2.7: an absent key, a blank string, an empty list and a null are all the
    same thing -- a field nobody filled in."""
    if v is None:
        return True
    if isinstance(v, str):
        return not v.strip()
    if isinstance(v, (list, tuple, dict, set)):
        return len(v) == 0
    return False


def _at(path: str) -> str:
    return path or "spec"


def _check(node, schema: dict, path: str, errs: list[str]) -> None:
    types = schema.get("type")
    if types is not None:
        names = [types] if isinstance(types, str) else list(types)
        if not any(_is_type(node, t) for t in names):
            errs.append(f"{_at(path)}: expected {' or '.join(names)}, got {_typename(node)}")
            return

    if "enum" in schema and node not in schema["enum"]:
        allowed = ", ".join(str(x) for x in schema["enum"])
        errs.append(f"{_at(path)}: {node!r} is not one of [{allowed}]")

    if isinstance(node, str):
        n = schema.get("minLength")
        if n is not None and len(node.strip()) < n:
            errs.append(f"{_at(path)}: needs at least {n} non-blank character(s)")
        pat = schema.get("pattern")
        if pat is not None and not re.search(pat, node):
            errs.append(f"{_at(path)}: {node!r} does not match {pat}")

    if isinstance(node, (int, float)) and not isinstance(node, bool):
        lo = schema.get("minimum")
        if lo is not None and node < lo:
            errs.append(f"{_at(path)}: {node} is below the minimum of {lo}")

    if isinstance(node, list):
        lo, hi = schema.get("minItems"), schema.get("maxItems")
        if lo is not None and len(node) < lo:
            errs.append(f"{_at(path)}: needs at least {lo} item(s), has {len(node)}")
        if hi is not None and len(node) > hi:
            errs.append(f"{_at(path)}: at most {hi} item(s) allowed, has {len(node)}")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for i, v in enumerate(node):
                _check(v, item_schema, f"{_at(path)}[{i}]", errs)

    if isinstance(node, dict):
        required = list(schema.get("required", []))
        for name in required:
            child = f"{path}.{name}" if path else name
            if name not in node:
                errs.append(f"{child}: required field is missing (2.7)")
            elif _empty(node[name]):
                errs.append(f"{child}: required field is present but empty (2.7)")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for k in node:
                if k not in props:
                    errs.append(f"{_at(path)}: unexpected key {k!r}")
        for k, v in node.items():
            if k not in props:
                continue
            if k in required and _empty(v):
                continue  # already reported; a type complaint on top is noise
            _check(v, props[k], f"{path}.{k}" if path else str(k), errs)


# --------------------------------------------------------------------------- hash


def _number(x) -> str:
    """`5`, `5.0`, `0.015`, `1.5e-2` and `.015` must not be three specs."""
    f = float(x)
    if math.isfinite(f) and f == int(f):
        return str(int(f))
    return repr(f)


def _dump(obj) -> str:
    """Canonical serialization: sorted keys, no whitespace, `description` gone at
    every depth (1.1). Comments never reach here -- the YAML parser drops them."""
    if isinstance(obj, dict):
        items = sorted(
            ((_dump(k), v) for k, v in obj.items() if k != "description"),
            key=lambda kv: kv[0],
        )
        return "{" + ",".join(f"{k}:{_dump(v)}" for k, v in items) + "}"
    if isinstance(obj, (list, tuple)):
        return "[" + ",".join(_dump(v) for v in obj) + "]"
    if obj is None:
        return "null"
    if isinstance(obj, bool):
        return "true" if obj else "false"
    if isinstance(obj, (int, float)):
        return _number(obj)
    if isinstance(obj, str):
        return json.dumps(obj)
    return json.dumps(str(_coerce(obj)))


def canonical(spec: dict) -> bytes:
    return _dump(_coerce(spec)).encode()


def spec_hash(spec: dict) -> str:
    """sha256 over the canonical form. Full digest; callers truncate for paths."""
    return hashlib.sha256(canonical(spec)).hexdigest()


# ---------------------------------------------------------------- git registration


def _git(args: list[str], cwd) -> str | None:
    """None on any failure -- no git, no repo, no such object. 2.8 aborts the run
    in that case, but it aborts by returning False, not by exploding here."""
    try:
        r = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)
    except (OSError, ValueError):
        return None
    return r.stdout if r.returncode == 0 else None


def _history(out: str, rel: str) -> list[tuple[str, list[str]]]:
    """(sha, paths) pairs. --follow means the blob may live at a different path in
    an older commit, so take the names git reports for that commit as well."""
    commits: list[tuple[str, list[str]]] = []
    for line in out.splitlines():
        if line.startswith(_SEP):
            commits.append((line[len(_SEP):].strip(), []))
        elif line.strip() and commits:
            commits[-1][1].append(line.strip())
    return [(sha, [*dict.fromkeys([*paths, rel])]) for sha, paths in commits if sha]


def git_registered(path, spec: dict | None = None) -> bool:
    """True iff this exact spec (by canonical hash) was committed at some point.

    2.8: the runner asks this before testing anything, and aborts on False.
    """
    p = Path(path).resolve()
    if spec is None:
        try:
            spec = _parse(p)
        except (OSError, SpecError, yaml.YAMLError):
            return False
    target = spec_hash(spec)

    root_out = _git(["rev-parse", "--show-toplevel"], cwd=p.parent if p.parent.exists() else Path.cwd())
    if not root_out or not root_out.strip():
        return False
    root = Path(root_out.strip()).resolve()
    try:
        rel = p.relative_to(root).as_posix()
    except ValueError:
        return False

    out = _git(["log", "--follow", "--name-only", f"--format={_SEP}%H", "--", rel], cwd=root)
    if not out:
        return False
    for sha, paths in _history(out, rel):
        for q in paths:
            blob = _git(["show", f"{sha}:{q}"], cwd=root)
            if blob is None:
                continue
            try:
                doc = yaml.safe_load(blob)
            except yaml.YAMLError:
                continue  # a commit where the spec was mid-edit is not a match
            if isinstance(doc, dict) and spec_hash(_coerce(doc)) == target:
                return True
    return False


def require_registered(path, spec: dict | None = None) -> None:
    """Gate every run through this. Raises rather than testing an unregistered spec."""
    if git_registered(path, spec):
        return
    p = Path(path)
    h = spec_hash(spec) if spec is not None else "<unreadable>"
    raise SpecError(
        f"{p}: this spec is not in git history (hash {h[:12]}). Commit the spec "
        f"before running it -- 2.8. A result for an uncommitted spec is not a "
        f"pre-registered result, it is a fitted one."
    )
