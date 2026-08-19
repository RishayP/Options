"""Ingest orchestrator: fetch -> validate -> write parquet -> write manifest.

Implements the reproducibility contract of Principles.md 1.6. Nothing is
written to `curated/` unless its hard checks pass, and every write emits a
manifest recording source, fetch time, row counts and a content hash of the
data itself (independent of where it sits on disk).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import yaml

from optlab.ingest import yf as yf_ingest
from optlab.validate.checks import run_checks, staleness_days

SCHEMA_VERSION = 1


def git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
    except Exception:
        return "unknown"


def content_hash(df: pd.DataFrame) -> str:
    """Hash of the data itself: stable across paths, partitioning and mtimes."""
    buf = df.to_csv(index=False).encode()
    return hashlib.sha256(buf).hexdigest()


def write_curated(df: pd.DataFrame, root: Path, dataset: str, symbol: str) -> Path:
    safe = symbol.replace("^", "_idx_")
    out = root / "curated" / dataset / f"symbol={safe}"
    out.mkdir(parents=True, exist_ok=True)
    path = out / "part.parquet"
    df.to_parquet(path, index=False, compression="snappy")
    return path


def ingest(cfg: dict, root: Path, only: list[str] | None = None) -> dict:
    asof = pd.Timestamp(dt.datetime.now(dt.timezone.utc).date())
    sleep_s = cfg.get("sources", {}).get("yfinance", {}).get("rate_limit_sleep_s", 1.0)
    report: dict = {
        "fetched_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "schema_version": SCHEMA_VERSION,
        "code_git_sha": git_sha(),
        "datasets": {},
    }

    for dataset, dcfg in cfg["datasets"].items():
        if only and dataset not in only:
            continue
        entries, failures = [], []
        for symbol in dcfg["symbols"]:
            try:
                if dataset == "ohlcv_daily":
                    df = yf_ingest.fetch_ohlcv(symbol, dcfg["start"], sleep_s)
                else:
                    df = yf_ingest.fetch_index(symbol, dcfg["start"], sleep_s)
            except Exception as e:
                failures.append({"symbol": symbol, "error": f"{type(e).__name__}: {e}"})
                print(f"  {symbol:8s} FETCH FAILED  {type(e).__name__}: {e}", file=sys.stderr)
                continue

            res = run_checks(df, dataset=dataset, symbol=symbol, cfg=cfg)
            stale = staleness_days(df, asof)
            if not res.passed:
                failures.append({"symbol": symbol, **res.as_dict()})
                print(f"  {symbol:8s} REJECTED      {res.hard}", file=sys.stderr)
                continue

            path = write_curated(df, root, dataset, symbol)
            entries.append(
                {
                    "symbol": symbol,
                    "rows": len(df),
                    "date_min": str(df["date"].min().date()),
                    "date_max": str(df["date"].max().date()),
                    "stale_days": stale,
                    "content_sha256": content_hash(df),
                    "path": str(path.relative_to(root)),
                    "soft_warnings": res.soft,
                }
            )
            flag = "  STALE" if stale > 5 else ""
            warn = f"  ({len(res.soft)} warn)" if res.soft else ""
            print(
                f"  {symbol:8s} ok  rows={len(df):6d}  "
                f"{df['date'].min().date()} -> {df['date'].max().date()}{warn}{flag}"
            )

        report["datasets"][dataset] = {
            "source": dcfg["source"],
            "start": dcfg["start"],
            "symbols_ok": len(entries),
            "symbols_failed": len(failures),
            "entries": entries,
            "failures": failures,
        }

    mdir = root / "manifests"
    mdir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    mpath = mdir / f"ingest_{stamp}.json"
    mpath.write_text(json.dumps(report, indent=1))
    (mdir / "latest.json").write_text(json.dumps(report, indent=1))
    print(f"\nmanifest -> {mpath}")
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="conf/settings.yaml")
    ap.add_argument("--dataset", action="append", help="limit to dataset(s)")
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text())
    root = Path(cfg.get("data_root", "data"))
    rep = ingest(cfg, root, only=args.dataset)

    failed = sum(d["symbols_failed"] for d in rep["datasets"].values())
    ok = sum(d["symbols_ok"] for d in rep["datasets"].values())
    print(f"ingested {ok} series, {failed} failed")
    return 1 if ok == 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
