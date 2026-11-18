import pandas as pd
import streamlit as st

from components import charts, ui
from utils import calc
from utils import scouting as S
from utils.cache import outputs, second_innings

st.title("Executive Dashboard")

o = outputs()
hc = calc.headline_counts(o)
ppl = S.people(o)
si = second_innings()
if not hc or ppl is None or si is None:
    ui.missing("the final player evaluation, match and second-innings files")
    st.stop()

n_role = hc["batters_evaluated"] + hc["bowlers_evaluated"]
ui.kpis([
    ("Matches covered", f"{hc['matches_total']:,}", f"{hc['matches_retained']:,} retained for the research analysis"),
    ("Seasons covered", "2022-2026", "Eight season labels, including split seasons such as 2022/23"),
    ("Strict pressure deliveries", f"{hc['pressure_deliveries']:,}", f"In {hc['pressure_matches']} matches"),
    ("Role-evaluations", f"{n_role}", f"{hc['batters_evaluated']} batters and {hc['bowlers_evaluated']} bowlers "
                                      f"= {len(ppl)} distinct people"),
])

# ---------- scouting overview ----------
death = S.scope(si, phases=("death",))
bsplit = S.bat_split(death).set_index("pid")
wsplit = S.bowl_split(death).set_index("pid")
career = S.ipl_career(o)
career = career.set_index("pid") if career is not None else None

c1, c2 = st.columns(2)
with c1:
    st.subheader("Research Batter Shortlist — Provisional")
    order = o["top10_batters"].pid.astype(int).tolist()
    rows = []
    for pid in order:
        r = ppl[ppl.pid == pid]
        if r.empty:
            continue
        r = r.iloc[0]
        b = bsplit.loc[pid] if pid in bsplit.index else None
        c = career.loc[pid] if career is not None and pid in career.index else None
        rows.append({
            "Player": r["name"], "Research label": r.bat_status,
            "Pressure balls": None if b is None else int(b.balls_p),
            "Raw death-over SR, pressure": None if b is None else b.sr_p,
            "Raw death-over SR, normal": None if b is None else b.sr_n,
            "IPL 2022-26 runs": None if c is None else int(c.ipl_runs),
            "IPL 2022-26 SR": None if c is None else c.ipl_sr,
        })
    ui.table(pd.DataFrame(rows), name="batter shortlist", download_name="batter_shortlist_view.csv", digits=1,
             key="ex_bat")
with c2:
    st.subheader("Bowler Selection (Not Ranked)")
    rows = []
    for pid in sorted(o["top10_bowlers"].pid.astype(int)):
        r = ppl[ppl.pid == pid]
        if r.empty:
            continue
        r = r.iloc[0]
        w = wsplit.loc[pid] if pid in wsplit.index else None
        c = career.loc[pid] if career is not None and pid in career.index else None
        rows.append({
            "Player": r["name"], "Research label": r.bowl_status,
            "Pressure balls": None if w is None else int(w.balls_p),
            "Raw death-over economy, pressure": None if w is None else w.econ_p,
            "Raw death-over economy, normal": None if w is None else w.econ_n,
            "IPL 2022-26 wickets": None if c is None else int(c.ipl_wickets),
            "IPL 2022-26 economy": None if c is None or pd.isna(c.ipl_economy) else c.ipl_economy,
        })
    ui.table(pd.DataFrame(rows), name="bowler selections",
             download_name="bowler_selections_view.csv", digits=2, key="ex_bowl")

# ---------- pressure versus normal ----------
st.subheader("Pressure against normal, death overs")
pb, pw = S.pooled_bat(death), S.pooled_bowl(death)
pair = ["Under pressure", "Normal"]
a, b = st.columns(2)
with a:
    ui.plot(charts.bar(pd.DataFrame({"condition": pair, "value": [pb.sr_p, pb.sr_n]}), "condition", "value",
                       "Batting strike rate", "runs per 100 balls"))
with b:
    ui.plot(charts.bar(pd.DataFrame({"condition": pair, "value": [pb.out100_p, pb.out100_n]}), "condition", "value",
                       "Batters dismissed", "dismissals per 100 balls"))
a, b = st.columns(2)
with a:
    ui.plot(charts.bar(pd.DataFrame({"condition": pair, "value": [pw.econ_p, pw.econ_n]}), "condition", "value",
                       "Bowling economy", "runs per over"))
with b:
    ui.plot(charts.bar(pd.DataFrame({"condition": pair, "value": [pw.wkt100_p, pw.wkt100_n]}), "condition", "value",
                       "Bowlers taking wickets", "wickets per 100 balls"))

# ---------- performance overview and comparison ----------
st.subheader("Batter and bowler performance overview")
bo = bsplit.reset_index().merge(ppl[["pid", "name"]], on="pid")
bo = bo[bo.balls_p >= S.SMALL_SAMPLE_BALLS]
wo = wsplit.reset_index().merge(ppl[["pid", "name"]], on="pid")
wo = wo[wo.balls_p >= S.SMALL_SAMPLE_BALLS]
left, right = st.columns(2)
with left:
    ui.plot(charts.scatter_xy(bo, "sr_n", "sr_p", "name", "Batters: strike rate under pressure against normal",
                              "normal strike rate", "strike rate under pressure"))
with right:
    ui.plot(charts.scatter_xy(wo, "econ_n", "econ_p", "name", "Bowlers: economy under pressure against normal",
                              "normal economy", "economy under pressure"))
st.subheader("Batter shortlist, strike rate under pressure against normal")
bat_cmp = bsplit.reset_index().merge(ppl[["pid", "name", "in_bat_shortlist"]], on="pid")
bat_cmp = bat_cmp[bat_cmp.in_bat_shortlist].rename(columns={"sr_p": "Under pressure", "sr_n": "Normal (same overs)"})
ui.plot(charts.grouped_bars(bat_cmp, "name", ["Under pressure", "Normal (same overs)"],
                            "Shortlisted batters: strike rate, raw", "runs per 100 balls"))

# ---------- pressure distribution ----------
st.subheader("Pressure situation distribution")
dist = [
    ("leverage", "Stakes", "win-probability leverage"),
    ("urgency_rate_gap", "Urgency", "required rate minus resource-implied rate (runs/over)"),
    ("closeness", "Closeness", "distance from 50% win probability"),
    ("scarcity_balls", "Resource scarcity: balls", "balls remaining / 120"),
    ("scarcity_wkts", "Resource scarcity: wickets", "wickets in hand / 10"),
]
for i in range(0, len(dist), 2):
    cols = st.columns(2)
    for slot, (col, title, xl) in zip(cols, dist[i:i + 2]):
        with slot:
            ui.plot(charts.hist(si, col, "pressure_strict", title, xl))

# ---------- season trends ----------
st.subheader("Season-wise trends, death overs")
left, right = st.columns(2)
with left:
    ui.plot(charts.line(S.all_by_year(death, "bat"), "year", "value", "series",
                        "Strike rate by season, under pressure and normal", "runs per 100 balls"))
with right:
    ui.plot(charts.line(S.all_by_year(death, "bowl"), "year", "value", "series",
                        "Economy by season, under pressure and normal", "runs per over"))

