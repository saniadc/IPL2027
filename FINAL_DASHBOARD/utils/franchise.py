"""Franchise history logic (pure, no Streamlit).

Three separate concepts, never merged:
1. Historical franchise: the team a player is recorded with in an IPL season (from the supplied squad mapping).
2. Latest verified franchise affiliation: only from rows in data/manual/current_affiliation_verified.csv.
3. IPL 2027 auction status: only from rows in data/manual/ipl2027_status_verified.csv.

Rows in 2 and 3 are accepted only with a pid, an allowed value, an https source URL and a date. Anything else is
rejected and reported. With no accepted row, the answer is NOT_VERIFIED. Historical data is never used to infer 2 or 3."""
import re
from datetime import date

import pandas as pd

NOT_VERIFIED = "Not verified"
AUCTION_STATUSES = ("Retained", "Released", "Traded", "Auction-listed")
MIN_BAT_BALLS = 30   # below this a season's batting figures are shown with a small-sample note
MIN_BOWL_BALLS = 18  # three overs


def validate(df, required, allowed_status=None, known_franchises=None):
    """Return (accepted rows, list of rejection reasons). Each rejection names the row number and the rule broken."""
    if df is None or len(df) == 0:
        return pd.DataFrame(columns=required), []
    missing = [c for c in required if c not in df.columns]
    if missing:
        return pd.DataFrame(columns=required), [f"file is missing columns: {', '.join(missing)}"]
    ok, why = [], []
    for i, r in df.reset_index(drop=True).iterrows():
        reason = None
        if not str(r["source_url"]).startswith("https://"):
            reason = "source_url must start with https://"
        elif not _is_date(r["as_of"]):
            reason = "as_of must be a date (YYYY-MM-DD)"
        elif pd.isna(pd.to_numeric(r["pid"], errors="coerce")):
            reason = "pid must be a number"
        elif allowed_status is not None and r.get("status") not in allowed_status:
            reason = f"status must be one of {', '.join(allowed_status)}"
        elif known_franchises is not None and "franchise" in r and r["franchise"] not in known_franchises:
            reason = "franchise is not one of the IPL franchises in the data"
        if reason:
            why.append(f"row {i + 2}: {reason}")
        else:
            ok.append(r)
    return (pd.DataFrame(ok, columns=required) if ok else pd.DataFrame(columns=required)), why


def _is_date(v):
    try:
        date.fromisoformat(str(v))
        return True
    except ValueError:
        return False


def verified_for(accepted, pid, column):
    """The accepted record for one player, as (value, source_url, as_of), or (NOT_VERIFIED, None, None)."""
    if accepted is None or len(accepted) == 0:
        return NOT_VERIFIED, None, None
    hit = accepted[pd.to_numeric(accepted.pid, errors="coerce") == pid]
    if hit.empty:
        return NOT_VERIFIED, None, None
    r = hit.sort_values("as_of").iloc[-1]  # the most recent dated record wins
    return r[column], r["source_url"], r["as_of"]


def is_small_bat(balls):
    return pd.notna(balls) and balls < MIN_BAT_BALLS


def is_small_bowl(balls):
    return pd.notna(balls) and balls < MIN_BOWL_BALLS


def season_rows(seasons, pid):
    """Season rows for one player, oldest first, with a small-sample note on the batting and bowling figures."""
    d = seasons[seasons.pid == pid].sort_values("season").copy()
    notes = []
    for _, r in d.iterrows():
        n = []
        if is_small_bat(r.balls_faced):
            n.append("small batting sample")
        if is_small_bowl(r.legal_balls):
            n.append("small bowling sample")
        notes.append("; ".join(n))
    d["sample_note"] = notes
    return d


IPL_SEASONS = (2022, 2023, 2024, 2025, 2026)


def seasons_without_record(seasons, pid):
    """IPL seasons from 2022 with no squad record for this player in the supplied data. This is a data gap,
    not a statement that the player did not play."""
    have = set(seasons[seasons.pid == pid].season.astype(int))
    return [y for y in IPL_SEASONS if y not in have]


def benchmark(seasons, kind, season, metric, min_balls):
    """Median of one metric across evaluated batters ('batter') or bowlers ('bowler') in one season, using only
    players above the sample floor. A player evaluated as both counts for both."""
    d = seasons[seasons.evaluated_as.str.contains(kind, na=False) & (seasons.season == season)]
    d = d[d.balls_faced >= min_balls] if kind == "batter" else d[d.legal_balls >= min_balls]
    if d.empty or d[metric].dropna().empty:
        return None, 0
    return float(d[metric].median()), int(d[metric].notna().sum())


def players_for_franchises(seasons, franchises):
    """pids who represented any of the chosen franchises in any season. Empty selection = everyone."""
    if not franchises:
        return set(seasons.pid)
    return set(seasons[seasons.franchise.isin(franchises)].pid)


def load_verified(o):
    """Accepted current-affiliation and 2027-status rows, plus the reasons any row was rejected."""
    known = None
    seasons = o.get("fh_seasons")
    if seasons is not None:
        known = set(seasons.franchise)
    aff, aff_why = validate(o.get("fh_affiliation_verified"),
                            ["pid", "player_name", "franchise", "source_url", "source_title", "as_of"],
                            known_franchises=known)
    stat, stat_why = validate(o.get("fh_status_verified"),
                              ["pid", "player_name", "status", "source_url", "source_title", "as_of"],
                              allowed_status=AUCTION_STATUSES)
    return {"aff": aff, "stat": stat, "why": aff_why + stat_why}


def three_fields(verified, pid):
    """The three separate fields for one person. Affiliation and status are 'Not verified' unless an accepted row exists."""
    aff, aff_url, aff_date = verified_for(verified["aff"], pid, "franchise")
    stat, stat_url, stat_date = verified_for(verified["stat"], pid, "status")
    return {"affiliation": aff, "affiliation_source": aff_url, "affiliation_as_of": aff_date,
            "auction_status": stat, "auction_source": stat_url, "auction_as_of": stat_date}


SQUAD_ONLY = "Squad record; no playing appearance"
LISTED_UNPLAYED = "Listed in playing eleven; not played"


def appearance_note(matches_played, listed):
    """Label for a season with no match played: squad-only, or listed in a playing eleven but not played.
    Empty when the player did play in that season."""
    mp = 0 if pd.isna(matches_played) else int(matches_played)
    if mp > 0:
        return ""
    return LISTED_UNPLAYED if (not pd.isna(listed) and int(listed) > 0) else SQUAD_ONLY
