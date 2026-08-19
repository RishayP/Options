"""Trial accounting with mechanical budget enforcement (Principles.md 4.2).

The trial log is append-only and records every run, including ones abandoned
seconds later. Under-reporting your own trials is the most common way a solo
researcher self-destructs, and the correction in 4.3 depends on the count being
honest -- so the count is not left to discipline. `guard()` refuses to hand out
run N+1 once the budget registered in PROGRAM.md is spent.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

TRIALS_PATH = Path("results/trials.jsonl")
DEFAULT_BUDGET = 8  # PROGRAM.md, registered 2026-08-19


class TrialBudgetExceeded(RuntimeError):
    """Raised instead of running trial N+1. Not catchable by convention."""


@dataclass
class Trial:
    hypothesis_id: str
    spec_hash: str
    params: dict
    utc: str
    outcome: str = "pending"        # pending | complete | abandoned | error
    headline: dict = field(default_factory=dict)
    note: str = ""

    def key(self) -> str:
        """Identity of the *question asked*, not of the code that asked it."""
        blob = json.dumps(
            {"id": self.hypothesis_id, "params": self.params},
            sort_keys=True, separators=(",", ":"),
        )
        return hashlib.sha256(blob.encode()).hexdigest()[:16]


def _load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def count(hypothesis_id: str, *, path: Path = TRIALS_PATH) -> int:
    """Distinct questions asked of the data for this hypothesis so far.

    Byte-identical repeats (a bug fix, a re-run of the same spec) collapse to
    one trial by design -- 4.2 counts questions, not executions.
    """
    seen = {r["key"] for r in _load(path) if r["hypothesis_id"] == hypothesis_id}
    return len(seen)


def remaining(hypothesis_id: str, *, budget: int = DEFAULT_BUDGET,
              path: Path = TRIALS_PATH) -> int:
    return max(0, budget - count(hypothesis_id, path=path))


def record(trial: Trial, *, path: Path = TRIALS_PATH) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    row = asdict(trial) | {"key": trial.key()}
    with path.open("a") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")
    return row["key"]


def guard(hypothesis_id: str, params: dict, *, spec_hash: str = "",
          budget: int = DEFAULT_BUDGET, path: Path = TRIALS_PATH,
          note: str = "") -> str:
    """Register a trial, or refuse. Call this BEFORE running anything.

    Re-asking a question already in the log is free -- it is the same trial.
    A genuinely new question when the budget is spent raises.
    """
    t = Trial(
        hypothesis_id=hypothesis_id,
        spec_hash=spec_hash,
        params=params,
        utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        note=note,
    )
    prior = {r["key"] for r in _load(path) if r["hypothesis_id"] == hypothesis_id}
    if t.key() not in prior and len(prior) >= budget:
        raise TrialBudgetExceeded(
            f"{hypothesis_id}: budget of {budget} trials is spent "
            f"({len(prior)} distinct questions already asked). "
            f"PROGRAM.md permits no more. Either the hypothesis stands on what "
            f"has been run, or it is retired -- see Principles.md 4.2, 11.6."
        )
    return record(t, path=path)


def finish(key: str, outcome: str, headline: dict | None = None,
           *, path: Path = TRIALS_PATH) -> None:
    """Append the resolution of a trial. The log is append-only; nothing is
    rewritten, so an abandoned run stays visible in the count."""
    t = Trial(
        hypothesis_id="", spec_hash="", params={},
        utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        outcome=outcome, headline=headline or {}, note=f"resolves:{key}",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as fh:
        fh.write(json.dumps(asdict(t) | {"key": key}, sort_keys=True) + "\n")


def program_total(*, path: Path = TRIALS_PATH) -> int:
    """Trials across every hypothesis -- the denominator for 4.3's correction."""
    return len({(r["hypothesis_id"], r["key"]) for r in _load(path)})


def summary(*, path: Path = TRIALS_PATH, budget: int = DEFAULT_BUDGET) -> str:
    rows = _load(path)
    ids = sorted({r["hypothesis_id"] for r in rows if r["hypothesis_id"]})
    out = [f"{'hypothesis':24s} {'used':>5s} {'left':>5s}"]
    for h in ids:
        c = count(h, path=path)
        out.append(f"{h:24s} {c:5d} {max(0, budget - c):5d}")
    out.append(f"\nprogram total: {program_total(path=path)} trials")
    return "\n".join(out)
