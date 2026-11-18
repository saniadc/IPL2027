"""Scouting calculations (pure, no Streamlit).

Pressure and normal figures come from the research's second-innings states (retained matches, IPL and other T20).
They are RAW descriptive rates. They are not adjusted for general ability. The ability-adjusted research results
are read from the saved outputs and shown beside them, never blended into them.

Definitions (from the research pipeline):
- balls faced and balls bowled count legal deliveries only (wides and no-balls excluded).
- batter runs are off-bat runs; bowler runs conceded are the research's bowler_conceded (includes wides and no-balls).
- wickets credited to a bowler are the research's bowler_wkt (caught, bowled, LBW, stumped, hit wicket on legal balls).
- stakes = leverage; urgency = required rate minus resource-implied rate (runs/over);
  resource scarcity = wickets in hand / 10 and balls remaining / 120; closeness = distance from 50% win probability.
"""
import pandas as pd

SMALL_SAMPLE_BALLS = 30  # dashboard convention for flagging a small pressure sample; not a research threshold

PARAMETERS = [
    ("leverage", "Stakes: win-probability leverage"),
    ("urgency_rate_gap", "Urgency: required rate minus resource-implied rate (runs/over)"),
    ("closeness", "Closeness: distance from 50% win probability"),
    ("scarcity_balls", "Resource scarcity: balls remaining / 120"),
    ("scarcity_wkts", "Resource scarcity: wickets in hand / 10"),
]


def scope(si, leagues=(), years=(), phases=()):
    """Filter the second-innings states. Empty selection means no filter."""
    if si is None:
        return None
    d = si
    if leagues:
        d = d[d.league.isin(leagues)]
    if years:
        d = d[d.year.isin(years)]
    if phases:
        d = d[d.phase.isin(phases)]
    return d


def _legal(d):
    return d[d.legal.astype(bool)]


def _pressure(d, flag):
    return d[d.pressure_strict.astype(bool) == flag]


def bat_split(d, by="striker_id"):
    """Per batter: legal balls, runs and dismissals under pressure (p) and normal (n) conditions, with rates."""
    x = _legal(d)
    agg = dict(balls=("runs", "size"), runs=("runs", "sum"), outs=("batter_out", "sum"))
    p = _pressure(x, True).groupby(by).agg(**{k + "_p": v for k, v in agg.items()})
    n = _pressure(x, False).groupby(by).agg(**{k + "_n": v for k, v in agg.items()})
    out = p.join(n, how="outer").fillna(0)
    out["sr_p"] = (out.runs_p / out.balls_p * 100).where(out.balls_p > 0)
    out["sr_n"] = (out.runs_n / out.balls_n * 100).where(out.balls_n > 0)
    out["out100_p"] = (out.outs_p / out.balls_p * 100).where(out.balls_p > 0)
    out["out100_n"] = (out.outs_n / out.balls_n * 100).where(out.balls_n > 0)
    out["sr_diff"] = out.sr_p - out.sr_n
    return out.reset_index().rename(columns={by: "pid"})


def bowl_split(d, by="bowler_id"):
    """Per bowler: legal balls, runs conceded and wickets credited under pressure (p) and normal (n) conditions."""
    x = _legal(d)
    agg = dict(balls=("runs", "size"), conceded=("bowler_conceded", "sum"), wkts=("bowler_wkt", "sum"))
    p = _pressure(x, True).groupby(by).agg(**{k + "_p": v for k, v in agg.items()})
    n = _pressure(x, False).groupby(by).agg(**{k + "_n": v for k, v in agg.items()})
    out = p.join(n, how="outer").fillna(0)
    out["econ_p"] = (out.conceded_p * 6 / out.balls_p).where(out.balls_p > 0)
    out["econ_n"] = (out.conceded_n * 6 / out.balls_n).where(out.balls_n > 0)
    out["wkt100_p"] = (out.wkts_p / out.balls_p * 100).where(out.balls_p > 0)
    out["wkt100_n"] = (out.wkts_n / out.balls_n * 100).where(out.balls_n > 0)
    out["econ_diff"] = out.econ_p - out.econ_n
    return out.reset_index().rename(columns={by: "pid"})


def pooled_bat(d):
    """Pooled batting rates over the whole scope: pressure versus normal."""
    s = bat_split(d.assign(_all=1), by="_all")
    return s.iloc[0] if len(s) else None


def pooled_bowl(d):
    s = bowl_split(d.assign(_all=1), by="_all")
    return s.iloc[0] if len(s) else None


def bat_by_year(d, pid):
    """One batter's pressure and normal strike rate by season (year)."""
    x = _legal(d[d.striker_id == pid])
    rows = []
    for yr, g in x.groupby("year"):
        for flag, lab in [(True, "Under pressure"), (False, "Normal")]:
            h = g[g.pressure_strict.astype(bool) == flag]
            if len(h):
                rows.append({"year": int(yr), "series": lab, "value": h.runs.sum() / len(h) * 100, "balls": len(h)})
    return pd.DataFrame(rows)


def bowl_by_year(d, pid):
    x = _legal(d[d.bowler_id == pid])
    rows = []
    for yr, g in x.groupby("year"):
        for flag, lab in [(True, "Under pressure"), (False, "Normal")]:
            h = g[g.pressure_strict.astype(bool) == flag]
            if len(h):
                rows.append({"year": int(yr), "series": lab, "value": h.bowler_conceded.sum() * 6 / len(h),
                             "balls": len(h)})
    return pd.DataFrame(rows)


def all_by_year(d, role):
    """Pooled season trend over the whole scope, pressure versus normal."""
    rows = []
    x = _legal(d)
    for yr, g in x.groupby("year"):
        for flag, lab in [(True, "Under pressure"), (False, "Normal")]:
            h = g[g.pressure_strict.astype(bool) == flag]
            if len(h):
                v = h.runs.sum() / len(h) * 100 if role == "bat" else h.bowler_conceded.sum() * 6 / len(h)
                rows.append({"year": int(yr), "series": lab, "value": v, "balls": len(h)})
    return pd.DataFrame(rows)


def urgency_bands(d, role):
    """Pressure-state rates by quartile of urgency, pooled over the scope. Shows how rates change with urgency."""
    x = _pressure(_legal(d), True)
    if len(x) < 4:
        return None
    band = pd.qcut(x.urgency_rate_gap, 4, duplicates="drop")
    labels = [f"Q{i + 1}: {iv.left:.1f} to {iv.right:.1f}" for i, iv in enumerate(band.cat.categories)]
    g = x.groupby(band, observed=True)
    if role == "bat":
        out = pd.DataFrame({"balls": g.size(), "value": g.runs.sum() / g.size() * 100})
        ylabel = "strike rate under pressure"
    else:
        out = pd.DataFrame({"balls": g.size(), "value": g.bowler_conceded.sum() * 6 / g.size()})
        ylabel = "economy under pressure (runs/over)"
    out = out.reset_index(drop=True)
    out["band"] = labels[: len(out)]
    return out, ylabel


def sample_note(balls):
    if pd.isna(balls):
        return "no pressure balls"
    return "small sample" if balls < SMALL_SAMPLE_BALLS else "adequate sample"


def people(o):
    """One row per evaluated person: research status per role, shortlist flags, historical franchise fields.
    Status labels are the research labels; franchise fields come from the historical squad data only."""
    from utils import calc
    fe = o.get("final_eval")
    fp = o.get("fh_players")
    if fe is None or fp is None:
        return None
    rows = {}
    for role, key in [("bat", "bat"), ("bowl", "bowl")]:
        f = calc.role_frame(fe, role)
        if f is None:
            continue
        for _, r in f.iterrows():
            d = rows.setdefault(int(r.pid), {"pid": int(r.pid), "name": r["name"]})
            d[f"{key}_status"] = r.dashboard_status
            d[f"{key}_pressure_deliveries"] = r.pressure_deliveries
            d[f"{key}_p_deviation"] = r.P_deviation_from_population_gt0
    out = pd.DataFrame(rows.values())
    fp = fp.assign(pid=fp.pid.astype(int))
    keep = ["pid", "evaluated_as", "seasons_in_squad", "franchises_represented", "latest_historical_franchise",
            "latest_season", "in_research_top10_batters", "in_research_top10_bowlers"]
    out = out.merge(fp[keep], on="pid", how="left")
    out["in_bat_shortlist"] = out.in_research_top10_batters.fillna(False).astype(bool)
    out["in_bowl_list"] = out.in_research_top10_bowlers.fillna(False).astype(bool)
    return out


def ipl_career(o):
    """IPL 2022-2026 totals per person, summed from the season file (historical records only)."""
    s = o.get("fh_seasons")
    if s is None or len(s) == 0:
        return None
    g = s.groupby("pid")
    out = pd.DataFrame({
        "ipl_runs": g.runs.sum(), "ipl_balls_faced": g.balls_faced.sum(), "ipl_dismissals": g.dismissals.sum(),
        "ipl_legal_balls": g.legal_balls.sum(), "ipl_conceded": g.conceded.sum(), "ipl_wickets": g.wickets.sum(),
    }).reset_index()
    out["ipl_sr"] = (out.ipl_runs / out.ipl_balls_faced * 100).where(out.ipl_balls_faced > 0)
    out["ipl_avg"] = (out.ipl_runs / out.ipl_dismissals).where(out.ipl_dismissals > 0)
    out["ipl_economy"] = (out.ipl_conceded * 6 / out.ipl_legal_balls).where(out.ipl_legal_balls > 0)
    out["pid"] = out.pid.astype(int)
    return out
