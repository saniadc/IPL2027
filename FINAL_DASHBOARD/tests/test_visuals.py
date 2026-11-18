"""Tests for the visual data aggregates and the scouting helpers. No Streamlit needed.
Run:  python tests/test_visuals.py"""
import os
import sys
from pathlib import Path

DASH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DASH))

from utils import loaders, visuals  # noqa: E402

RAW = Path(os.environ["SUPERR_RAW_BALL"]) if os.environ.get("SUPERR_RAW_BALL") else None


def test_visual_aggregates_are_consistent():
    o = loaders.load_all()
    bat = o["vis_batter"]
    assert bat is not None and len(bat) == 25, None if bat is None else len(bat)
    assert bat[["strike_rate", "boundary_pct", "balls_faced"]].notna().all().all()
    assert (bat.dismissals <= bat.balls_faced).all()
    for key in ["vis_shots", "vis_delivery"]:
        sums = o[key].groupby("pid").share_of_classified.sum()
        assert (abs(sums - 1) < 0.01).all(), key


def test_batter_totals_match_raw_file_when_present():
    if RAW is None or not RAW.is_file():
        print("  (raw ball-by-ball file not set via SUPERR_RAW_BALL; recount skipped)")
        return
    import pandas as pd
    b = pd.read_csv(RAW, usecols=["striker_id", "runs", "extras_type"], low_memory=False)
    bat = loaders.load_all()["vis_batter"]
    pid = int(bat.loc[bat.name == "Ravindra Jadeja", "pid"].iloc[0])
    sub = b[(b.striker_id == pid) & (b.extras_type != "wide")]
    row = bat[bat.pid == pid].iloc[0]
    assert int(row.runs) == int(sub.runs.sum()) and int(row.balls_faced) == len(sub)


def test_pressure_by_phase_reflects_the_strict_definition():
    si = loaders.load_second_innings()
    out = visuals.pressure_by_phase(si)
    share = dict(zip(out.phase, out.share_strict_pressure))
    assert share["powerplay"] == 0 and share["middle"] == 0 and share["death"] > 0, share


def test_initials():
    assert visuals.initials("Mahendra Singh Dhoni") == "MD"
    assert visuals.initials("Rashid") == "RA"


def run_all():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except Exception as e:
            failed += 1
            print(f"FAIL  {t.__name__}: {type(e).__name__}: {str(e)[:500]}")
    print(f"\n{len(tests) - failed} of {len(tests)} visual tests passed")
    return failed


if __name__ == "__main__":
    sys.exit(1 if run_all() else 0)
