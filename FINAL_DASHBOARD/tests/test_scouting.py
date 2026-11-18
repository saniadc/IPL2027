"""Tests for the scouting helpers: death-overs matching, split values, urgency bands and person table.
Run:  python tests/test_scouting.py"""
import sys
from pathlib import Path

DASH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DASH))

from utils import loaders, scouting as S  # noqa: E402


def _si():
    return loaders.load_second_innings()


def test_pressure_states_only_occur_in_death_overs():
    si = _si()
    all_p = S.scope(si, phases=())
    death = S.scope(si, phases=("death",))
    assert S._pressure(S._legal(all_p), True).shape[0] == S._pressure(S._legal(death), True).shape[0]


def test_death_matched_pooled_figures_are_pinned():
    # Values verified when the scouting module was written. A change here means the source data or the definition moved.
    death = S.scope(_si(), phases=("death",))
    pb = S.pooled_bat(death)
    assert abs(pb.sr_p - 151.31) < 0.05 and abs(pb.sr_n - 152.06) < 0.05, (pb.sr_p, pb.sr_n)
    assert abs(pb.out100_p - 9.51) < 0.05 and abs(pb.out100_n - 6.20) < 0.05, (pb.out100_p, pb.out100_n)
    pw = S.pooled_bowl(death)
    assert abs(pw.econ_p - 9.08) < 0.05 and abs(pw.econ_n - 9.12) < 0.05, (pw.econ_p, pw.econ_n)


def test_urgency_bands_return_a_labelled_frame():
    out = S.urgency_bands(S.scope(_si(), phases=("death",)), "bat")
    assert out is not None
    band_df, ylabel = out
    assert {"band", "value"} <= set(band_df.columns) and bool(ylabel)


def test_sample_note_flags_small_samples():
    assert "small" in S.sample_note(5).lower()
    assert "small" not in S.sample_note(500).lower()


def test_people_table_has_61_people_and_ten_on_each_list():
    o = loaders.load_all()
    ppl = S.people(o)
    assert len(ppl) == 61, len(ppl)
    assert ppl.in_bat_shortlist.sum() == 10 and ppl.in_bowl_list.sum() == 10
    assert ppl.pid.is_unique


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
    print(f"\n{len(tests) - failed} of {len(tests)} scouting tests passed")
    return failed


if __name__ == "__main__":
    sys.exit(1 if run_all() else 0)
