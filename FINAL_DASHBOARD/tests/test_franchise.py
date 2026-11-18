"""Franchise history tests. No Streamlit needed.

Checks the built history against the data, the verification rules that keep 'current affiliation' and
'IPL 2027 status' from being guessed, and the sample-size flags.
Run:  python tests/test_franchise.py   (set SUPERR_RAW_DIR to the raw 'Data Pack' folder to also recount from raw)"""
import os
import sys
from pathlib import Path

import pandas as pd

DASH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DASH))

from utils import franchise as F  # noqa: E402
from utils import loaders  # noqa: E402

RAW = Path(os.environ["SUPERR_RAW_DIR"]) if os.environ.get("SUPERR_RAW_DIR") else None
REQ_STATUS = ["pid", "player_name", "status", "source_url", "source_title", "as_of"]
REQ_AFF = ["pid", "player_name", "franchise", "source_url", "source_title", "as_of"]


def _data():
    o = loaders.load_all()
    return o["fh_seasons"], o["fh_players"]


def _row(**k):
    base = {"pid": 8, "player_name": "Test Player", "status": "Retained",
            "source_url": "https://example.org/official", "source_title": "Mock", "as_of": "2026-11-17"}
    base.update(k)
    return base


def test_history_shape_and_no_duplicates():
    seasons, players = _data()
    assert len(players) == 61, len(players)  # 66 role-evaluations; five people evaluated as both batter and bowler
    assert set(players.evaluated_as.value_counts().index) == {"batter", "bowler", "batter and bowler"}
    assert set(seasons.season) <= {2022, 2023, 2024, 2025, 2026}
    assert not seasons.duplicated(["pid", "season"]).any(), "a player has two franchises in one season"


def test_players_without_ipl_record_are_named_not_blank():
    _, players = _data()
    none = set(players[players.seasons_in_squad == 0].player_name)
    assert none == {"Shaheen Afridi", "Haris Rauf"}, none


def test_recount_from_raw_when_available():
    if RAW is None or not (RAW / "ball_by_ball.csv").is_file():
        print("  (SUPERR_RAW_DIR not set; raw recount skipped)")
        return
    seasons, _ = _data()
    b = pd.read_csv(RAW / "ball_by_ball.csv", usecols=["match_id", "striker_id", "runs", "extras_type"], low_memory=False)
    c = pd.read_csv(RAW / "competitions.csv")
    m = pd.read_csv(RAW / "matches.csv", usecols=["match_id", "comp_id"])
    ipl = set(m[m.comp_id.isin(c[c.comp_name.fillna("").str.startswith("IPL")].comp_id)].match_id)
    sub = b[b.match_id.isin(ipl) & (b.striker_id == 152) & (b.extras_type != "wide")]
    mine = seasons[seasons.pid == 152]
    assert int(mine.runs.sum()) == int(sub.runs.sum()) and int(mine.balls_faced.sum()) == len(sub)


def test_validation_accepts_a_sourced_dated_row():
    acc, why = F.validate(pd.DataFrame([_row()]), REQ_STATUS, allowed_status=F.AUCTION_STATUSES)
    assert len(acc) == 1 and why == []


def test_validation_rejects_each_broken_rule():
    cases = [
        (_row(source_url="http://example.org"), "https"),
        (_row(as_of="17/11/2026"), "date"),
        (_row(status="Likely to be retained"), "status"),
        (_row(pid="abc"), "pid"),
    ]
    for row, word in cases:
        acc, why = F.validate(pd.DataFrame([row]), REQ_STATUS, allowed_status=F.AUCTION_STATUSES)
        assert len(acc) == 0 and len(why) == 1 and word in why[0], (word, why)


def test_affiliation_must_name_a_known_franchise():
    row = {"pid": 8, "player_name": "X", "franchise": "Made Up XI", "source_url": "https://e.org",
           "source_title": "t", "as_of": "2026-11-17"}
    acc, why = F.validate(pd.DataFrame([row]), REQ_AFF, known_franchises={"Chennai Super Kings"})
    assert len(acc) == 0 and "not one of the IPL franchises" in why[0]


def test_no_accepted_record_reads_not_verified():
    acc, _ = F.validate(pd.DataFrame(columns=REQ_STATUS), REQ_STATUS, allowed_status=F.AUCTION_STATUSES)
    assert F.verified_for(acc, 8, "status") == (F.NOT_VERIFIED, None, None)


def test_most_recent_dated_record_wins():
    rows = pd.DataFrame([_row(status="Retained", as_of="2026-11-10"), _row(status="Released", as_of="2026-11-17")])
    acc, _ = F.validate(rows, REQ_STATUS, allowed_status=F.AUCTION_STATUSES)
    assert F.verified_for(acc, 8, "status")[0] == "Released"


def test_shipped_build_reads_not_verified_for_everyone():
    o = loaders.load_all()
    acc, why = F.validate(o["fh_status_verified"], REQ_STATUS, allowed_status=F.AUCTION_STATUSES)
    assert why == [] and len(acc) == 0
    _, players = _data()
    for pid in players.pid:
        assert F.verified_for(acc, int(pid), "status")[0] == F.NOT_VERIFIED


def test_historical_files_do_not_carry_status_or_affiliation_claims():
    seasons, players = _data()
    banned = {"status", "retained", "released", "auction", "current", "affiliation"}
    for df in (seasons, players):
        for col in df.columns:
            assert not any(w in col.lower() for w in banned), col


def test_gap_seasons_are_reported_not_hidden():
    seasons, _ = _data()
    holder = int(seasons[seasons.player_name == "Jason Holder"].pid.iloc[0])
    assert F.seasons_without_record(seasons, holder) == [2024, 2025]
    assert F.seasons_without_record(seasons, int(seasons[seasons.player_name == "Rashid Khan"].pid.iloc[0])) == []


def test_small_sample_flags():
    seasons, _ = _data()
    sr = F.season_rows(seasons, int(seasons.pid.iloc[0]))
    assert "sample_note" in sr.columns
    assert F.is_small_bat(12) and not F.is_small_bat(30) and F.is_small_bowl(17) and not F.is_small_bowl(18)
    assert not F.is_small_bat(float("nan"))  # not applicable is not a small sample


def test_benchmark_uses_only_players_above_the_floor():
    seasons, _ = _data()
    med, n = F.benchmark(seasons, "batter", 2026, "strike_rate", F.MIN_BAT_BALLS)
    eligible = seasons[seasons.evaluated_as.str.contains("batter", na=False) & (seasons.season == 2026)
                       & (seasons.balls_faced >= F.MIN_BAT_BALLS)]
    assert n == int(eligible.strike_rate.notna().sum()) and med == float(eligible.strike_rate.median())


def test_franchise_filter():
    seasons, _ = _data()
    # the page starts from the full player list when no franchise is chosen, so players without a record stay visible
    _, players = _data()
    assert set(players.pid) - set(seasons.pid) == {int(x) for x in players[players.seasons_in_squad == 0].pid}
    everyone = set(players.pid)
    rr = F.players_for_franchises(seasons, ["Rajasthan Royals"])
    assert 0 < len(rr) < len(everyone)
    assert all(seasons[seasons.pid == p].franchise.eq("Rajasthan Royals").any() for p in rr)


def test_appearance_labels_separate_squad_only_from_listed_unplayed():
    import math
    from utils import franchise as F
    assert F.appearance_note(0, 0) == F.SQUAD_ONLY
    assert F.appearance_note(0, 14) == F.LISTED_UNPLAYED
    assert F.appearance_note(math.nan, math.nan) == F.SQUAD_ONLY
    assert F.appearance_note(13, 13) == ""


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
    print(f"\n{len(tests) - failed} of {len(tests)} franchise tests passed")
    return failed


if __name__ == "__main__":
    sys.exit(1 if run_all() else 0)
