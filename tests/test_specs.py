"""Tests for spec validation, hashing and pre-registration (Principles.md 2.7, 2.8).

Two properties matter more than the rest. `test_hash_*` pin down that formatting
churn cannot orphan a result while a moved threshold always does (1.1), and the
`git_registered` tests pin down that an uncommitted spec is refused rather than
quietly run (2.8). Everything is written under tmp_path; the real specs/ tree is
registry state and tests must never touch it.
"""
from __future__ import annotations

import subprocess

import pytest
import yaml

from optlab.specs import (
    SpecError,
    git_registered,
    load,
    require_registered,
    spec_hash,
    validate,
)


def _spec(**over) -> dict:
    s = {
        "id": "H-2026-999",
        "name": "test_hypothesis",
        "registered_utc": "2026-08-19T12:00:00Z",
        "rationale": "a reason",
        "mechanism": "dealers are forced to hedge; hedgers pay for the gap protection",
        "trigger": {
            "description": "spot within 0.35% of the max-OI strike",
            "computable_pit": True,
            "inputs": ["spot", "oi"],
            "threshold": {"distance_pct": 0.015},
        },
        "estimation_universe": ["SPX"],
        "trading_universe": ["SPX"],
        "subgroup_check": "retains >=60% of magnitude in trading_universe",
        "entry_timing": "15:45 ET",
        "holding_period": "2 sessions",
        "exit_rule": "close Friday 09:30 ET",
        "outcome_variable": "pnl_per_unit_vega",
        "predicted_direction": "negative",
        "prior_effect_size": "-1.5 to -3.0 vol points",
        "falsification": "dead if mean RV-IV >= -0.5 vol points",
        "data_required": ["SPX chains 2016+"],
        "known_confounds": ["OPEX week overlaps FOMC"],
        "expected_decay": "moderate",
        "capacity_estimate": "not capacity constrained",
        "sample_size_expected": {
            "raw_events": 108,
            "independent_clusters": 96,
            "per_year": 12,
            "measured_utc": "2026-08-18",
        },
    }
    s.update(over)
    return s


def _write(tmp_path, spec: dict, name: str = "H-2026-999.yaml"):
    p = tmp_path / name
    p.write_text(yaml.safe_dump(spec, sort_keys=False))
    return p


# ------------------------------------------------------------------- validation


def test_valid_spec_loads(tmp_path):
    p = _write(tmp_path, _spec())
    assert load(p)["id"] == "H-2026-999"


def test_optional_blocks_validate(tmp_path):
    spec = _spec(
        status="REGISTERED",
        slice_plan={"stage1": "STAGE1", "stage2": "HOLDOUT"},
        trials=[{"name": "base", "params": {"z": 1.0}}],
    )
    assert validate(spec) == []


def test_every_missing_field_named_at_once(tmp_path):
    spec = _spec()
    for k in ("mechanism", "falsification", "capacity_estimate"):
        del spec[k]
    p = _write(tmp_path, spec)
    with pytest.raises(SpecError) as e:
        load(p)
    msg = str(e.value)
    # not just the first one -- 2.7 wants the whole list in one pass
    assert "mechanism" in msg and "falsification" in msg and "capacity_estimate" in msg
    assert msg.count("required field is missing") == 3


def test_missing_fields_are_sorted(tmp_path):
    spec = _spec()
    del spec["mechanism"]
    del spec["entry_timing"]
    errs = validate(spec)
    assert errs == sorted(errs)


@pytest.mark.parametrize("bad", ["", "   ", "\n\t ", None])
def test_blank_required_string_fails(tmp_path, bad):
    p = _write(tmp_path, _spec(mechanism=bad))
    with pytest.raises(SpecError, match="mechanism"):
        load(p)


def test_empty_list_fails(tmp_path):
    p = _write(tmp_path, _spec(data_required=[]))
    with pytest.raises(SpecError, match="data_required"):
        load(p)


def test_none_required_field_fails(tmp_path):
    p = _write(tmp_path, _spec(trading_universe=None))
    with pytest.raises(SpecError, match="trading_universe"):
        load(p)


def test_empty_and_missing_reported_together(tmp_path):
    spec = _spec(subgroup_check="   ", known_confounds=[])
    del spec["expected_decay"]
    errs = validate(spec)
    assert len(errs) == 3
    assert any("subgroup_check" in e and "empty" in e for e in errs)
    assert any("known_confounds" in e and "empty" in e for e in errs)
    assert any("expected_decay" in e and "missing" in e for e in errs)


def test_sample_size_missing_independent_clusters(tmp_path):
    sse = _spec()["sample_size_expected"]
    del sse["independent_clusters"]
    p = _write(tmp_path, _spec(sample_size_expected=sse))
    with pytest.raises(SpecError, match=r"sample_size_expected\.independent_clusters"):
        load(p)


def test_sample_size_missing_measured_utc(tmp_path):
    sse = _spec()["sample_size_expected"]
    del sse["measured_utc"]
    with pytest.raises(SpecError, match="measured_utc"):
        load(_write(tmp_path, _spec(sample_size_expected=sse)))


def test_trigger_missing_computable_pit(tmp_path):
    trig = _spec()["trigger"]
    del trig["computable_pit"]
    p = _write(tmp_path, _spec(trigger=trig))
    with pytest.raises(SpecError, match=r"trigger\.computable_pit"):
        load(p)


def test_computable_pit_false_is_not_empty(tmp_path):
    """A stated `false` is a claim on the record, not an unfilled field."""
    trig = _spec()["trigger"] | {"computable_pit": False}
    assert validate(_spec(trigger=trig)) == []


def test_bad_enum_and_pattern_reported(tmp_path):
    errs = validate(_spec(status="MAYBE", registered_utc="last tuesday"))
    assert any("status" in e for e in errs)
    assert any("registered_utc" in e for e in errs)


def test_trial_budget_is_mechanical(tmp_path):
    trials = [{"name": f"t{i}", "params": {"i": i}} for i in range(9)]
    errs = validate(_spec(trials=trials))
    assert any("trials" in e and "at most 8" in e for e in errs)


def test_wrong_type_reported(tmp_path):
    errs = validate(_spec(estimation_universe="SPX"))
    assert any("estimation_universe" in e and "array" in e for e in errs)


def test_unparseable_yaml_raises_specerror(tmp_path):
    p = tmp_path / "broken.yaml"
    p.write_text("id: [unclosed\n")
    with pytest.raises(SpecError):
        load(p)


def test_missing_file_raises_specerror(tmp_path):
    with pytest.raises(SpecError):
        load(tmp_path / "nope.yaml")


# ------------------------------------------------------------------------- hash


def test_hash_ignores_key_order(tmp_path):
    a = _spec()
    b = {k: a[k] for k in reversed(list(a))}
    b["trigger"] = {k: a["trigger"][k] for k in reversed(list(a["trigger"]))}
    assert spec_hash(a) == spec_hash(b)


def test_hash_ignores_comments_and_whitespace(tmp_path):
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    a.write_text(yaml.safe_dump(_spec(), sort_keys=False))
    b.write_text(
        "# a comment nobody should hash\n\n"
        + yaml.safe_dump(_spec(), sort_keys=True, default_flow_style=False, width=40)
        + "\n\n# trailing note\n"
    )
    assert spec_hash(load(a)) == spec_hash(load(b))


@pytest.mark.parametrize("literal", ["0.015", "1.5e-2", ".015", "0.0150"])
def test_hash_normalizes_number_spelling(tmp_path, literal):
    base = spec_hash(_spec())
    p = tmp_path / "n.yaml"
    text = yaml.safe_dump(_spec(), sort_keys=False).replace("distance_pct: 0.015", f"distance_pct: {literal}")
    assert f"distance_pct: {literal}" in text
    p.write_text(text)
    assert spec_hash(load(p)) == base


def test_hash_normalizes_int_and_float(tmp_path):
    a = _spec()
    b = _spec(sample_size_expected=a["sample_size_expected"] | {"per_year": 12.0})
    assert a["sample_size_expected"]["per_year"] == 12
    assert spec_hash(a) == spec_hash(b)


def test_hash_ignores_nested_description(tmp_path):
    a = _spec()
    trig = a["trigger"] | {"description": "reworded entirely, same rule"}
    b = _spec(trigger=trig)
    assert spec_hash(a) == spec_hash(b)


def test_hash_ignores_top_level_description(tmp_path):
    assert spec_hash(_spec()) == spec_hash(_spec(description="added prose"))


def test_hash_ignores_deeply_nested_description(tmp_path):
    a = _spec(trials=[{"name": "base", "params": {"z": 1.0, "description": "x"}}])
    b = _spec(trials=[{"name": "base", "params": {"z": 1.0, "description": "y"}}])
    assert spec_hash(a) == spec_hash(b)


def test_hash_changes_when_threshold_moves(tmp_path):
    a = _spec()
    trig = a["trigger"] | {"threshold": {"distance_pct": 0.016}}
    assert spec_hash(a) != spec_hash(_spec(trigger=trig))


def test_hash_changes_on_any_real_edit(tmp_path):
    base = spec_hash(_spec())
    assert spec_hash(_spec(predicted_direction="positive")) != base
    assert spec_hash(_spec(trading_universe=["SPX", "SPY"])) != base
    sse = _spec()["sample_size_expected"] | {"independent_clusters": 95}
    assert spec_hash(_spec(sample_size_expected=sse)) != base


def test_hash_is_full_sha256_hex(tmp_path):
    h = spec_hash(_spec())
    assert len(h) == 64 and all(c in "0123456789abcdef" for c in h)


def test_hash_does_not_confuse_string_and_number(tmp_path):
    assert spec_hash(_spec(batch="5")) != spec_hash(_spec(batch=5))


# --------------------------------------------------------------- registration


def _repo(tmp_path):
    root = tmp_path / "repo"
    (root / "specs").mkdir(parents=True)
    for args in (
        ["init", "-q", "-b", "main"],
        ["config", "user.email", "t@example.com"],
        ["config", "user.name", "t"],
    ):
        subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)
    return root


def _commit(root, msg="c"):
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-q", "-m", msg], cwd=root, check=True, capture_output=True)


def test_uncommitted_spec_is_not_registered(tmp_path):
    root = _repo(tmp_path)
    p = root / "specs" / "H.yaml"
    p.write_text(yaml.safe_dump(_spec()))
    assert git_registered(p) is False


def test_outside_a_git_repo_is_not_registered(tmp_path):
    p = _write(tmp_path, _spec())
    assert git_registered(p) is False


def test_missing_file_is_not_registered(tmp_path):
    assert git_registered(tmp_path / "gone.yaml") is False


def test_committed_spec_is_registered(tmp_path):
    root = _repo(tmp_path)
    p = root / "specs" / "H.yaml"
    p.write_text(yaml.safe_dump(_spec()))
    _commit(root)
    assert git_registered(p) is True
    require_registered(p, load(p))


def test_reformatting_a_committed_spec_stays_registered(tmp_path):
    """Formatting churn must not invalidate a registration (2.8)."""
    root = _repo(tmp_path)
    p = root / "specs" / "H.yaml"
    p.write_text(yaml.safe_dump(_spec(), sort_keys=False))
    _commit(root)
    p.write_text("# reordered and re-commented\n" + yaml.safe_dump(_spec(), sort_keys=True))
    assert git_registered(p) is True


def test_edited_threshold_is_not_registered(tmp_path):
    root = _repo(tmp_path)
    p = root / "specs" / "H.yaml"
    p.write_text(yaml.safe_dump(_spec()))
    _commit(root)
    trig = _spec()["trigger"] | {"threshold": {"distance_pct": 0.03}}
    p.write_text(yaml.safe_dump(_spec(trigger=trig)))
    assert git_registered(p) is False


def test_registration_survives_a_rename(tmp_path):
    """--follow: the blob may sit at a different path in an older commit."""
    root = _repo(tmp_path)
    old = root / "specs" / "H-old.yaml"
    old.write_text(yaml.safe_dump(_spec()))
    _commit(root, "register")
    new = root / "specs" / "H-new.yaml"
    subprocess.run(["git", "mv", "H-old.yaml", "H-new.yaml"], cwd=root / "specs",
                   check=True, capture_output=True)
    _commit(root, "rename")
    assert new.exists()
    assert git_registered(new) is True


def test_unparseable_committed_blob_is_skipped(tmp_path):
    root = _repo(tmp_path)
    p = root / "specs" / "H.yaml"
    p.write_text("id: [unclosed\n")
    _commit(root, "broken")
    p.write_text(yaml.safe_dump(_spec()))
    _commit(root, "fixed")
    assert git_registered(p) is True


def test_require_registered_raises_actionably(tmp_path):
    root = _repo(tmp_path)
    p = root / "specs" / "H.yaml"
    p.write_text(yaml.safe_dump(_spec()))
    with pytest.raises(SpecError, match="Commit the spec before running it"):
        require_registered(p, load(p))
