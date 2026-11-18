"""Pure helpers for the Cricket Visuals page (no Streamlit). Every number comes from a bundled file or from
second_innings_pressure.csv.gz; nothing is estimated here.

Shot and delivery labels are recorded categories, not locations: they support mix charts only, never a wagon
wheel or a line-and-length grid."""
import pandas as pd

PHASE_ORDER = ["powerplay", "middle", "death"]


def batter_summary(o):
    return o.get("vis_batter")


def shot_mix(o, pids, top_n=12):
    """Share of classified deliveries by stroke for the chosen batters, columns = most common strokes overall."""
    shots = o.get("vis_shots")
    if shots is None or len(shots) == 0 or not pids:
        return None
    sub = shots[shots.pid.isin(pids)]
    if sub.empty:
        return None
    keep = sub.groupby("stroke").balls.sum().sort_values(ascending=False).head(top_n).index
    mat = sub[sub.stroke.isin(keep)].pivot_table(index="name", columns="stroke", values="share_of_classified",
                                                 fill_value=0.0)
    return mat[list(keep)]


def delivery_mix(o, pid):
    d = o.get("vis_delivery")
    if d is None or len(d) == 0:
        return None
    sub = d[d.pid == pid].sort_values("share_of_classified", ascending=False)
    return sub if len(sub) else None


def pressure_by_phase(si):
    """Per phase: states, share meeting the strict pressure definition, mean required run rate (descriptive)."""
    if si is None or len(si) == 0 or "phase" not in si:
        return None
    g = si.groupby("phase")
    out = pd.DataFrame({"states": g.size(), "share_strict_pressure": g.pressure_strict.mean(),
                        "mean_required_run_rate": g.rrr.mean()}).reindex(PHASE_ORDER).dropna(how="all")
    return out.reset_index()


def pressure_by_season(si, leagues=None):
    """Per season (year): states and share meeting the strict pressure definition, for the chosen leagues."""
    if si is None or len(si) == 0 or "year" not in si:
        return None
    d = si if not leagues else si[si.league.isin(leagues)]
    if d.empty:
        return None
    g = d.groupby("year")
    return pd.DataFrame({"states": g.size(), "share_strict_pressure": g.pressure_strict.mean()}).reset_index()


def initials(name):
    parts = [p for p in str(name).replace(".", " ").split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()
