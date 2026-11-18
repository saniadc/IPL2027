import pandas as pd
import streamlit as st

from components import charts, ui
from utils import scouting as S
from utils import visuals
from utils.cache import outputs, second_innings

st.title("Batter Scouting")
o = outputs()
si = second_innings()
ppl = S.people(o)
short = o.get("top10_batters")
if si is None or ppl is None or short is None:
    ui.missing("the research shortlist, evaluation and second-innings files")
    st.stop()

# ---- 1. research shortlist: original file order, research model estimates only
st.subheader("Research Batter Shortlist — Provisional")
status = dict(zip(ppl.pid.astype(int), ppl.bat_status))
sl = pd.DataFrame({
    "Rank (research file)": short["rank"].values,
    "Player": short["name"].values,
    "Research status": [status.get(int(p)) for p in short["pid"]],
    "Research model: posterior mean": short["post_mean"].values,
    "Research model: P(top 10)": short["P_top10"].values,
})
ui.table(sl, digits=3, name="research batter shortlist", download_name="research_batter_shortlist.csv",
         key="bat_short")

# ---- 2. full comparison: raw death-over statistics, newly calculated here
st.subheader("Batter Performance Comparison")
f1, f2, f3 = st.columns([2, 2, 2])
leagues = f1.multiselect("Competition", sorted(si.league.unique()), default=[], key="bat_lg",
                         help="Empty = all competitions in the research dataset")
years = f2.multiselect("Season", sorted(int(y) for y in si.year.unique()), default=[], key="bat_yr")
min_balls = f3.slider("Minimum pressure balls", 0, 60, 0, key="bat_min")

d = S.scope(si, leagues=leagues, years=years, phases=("death",))
base = ppl[ppl.bat_status.notna()][["pid", "name", "bat_status"]]
table = base.merge(S.bat_split(d), on="pid", how="left")
career = S.ipl_career(o)
if career is not None:
    table = table.merge(career[["pid", "ipl_runs", "ipl_sr"]], on="pid", how="left")
table = table[table.balls_p.fillna(0) >= min_balls]
if table.empty:
    st.info("No batter meets these filters.")
    st.stop()

show = pd.DataFrame({
    "Player": table.name,
    "Research status": table.bat_status,
    "Pressure balls (sample)": table.balls_p.fillna(0).astype(int),
    "Raw death-over SR, pressure": table.sr_p,
    "Raw death-over SR, normal": table.sr_n,
    "Raw dismissals per 100 balls, pressure": table.out100_p,
    "Raw dismissals per 100 balls, normal": table.out100_n,
    "Raw IPL 2022-26 runs": table.ipl_runs if "ipl_runs" in table else None,
    "Raw IPL 2022-26 strike rate": table.ipl_sr if "ipl_sr" in table else None,
    "Sample": table.balls_p.map(S.sample_note),
}).sort_values("Pressure balls (sample)", ascending=False)
summary_cols = ["Player", "Pressure balls (sample)", "Raw death-over SR, pressure", "Raw death-over SR, normal", "Sample"]
ui.table(show[summary_cols], digits=1, key="bat_sum")
with st.expander("All batter statistics, with download"):
    ui.table(show, name="batter performance comparison", download_name="batter_performance_comparison.csv",
             digits=1, key="bat_table")

plot_df = table.dropna(subset=["sr_p", "sr_n"])
plot_df = plot_df[plot_df.balls_p >= S.SMALL_SAMPLE_BALLS]
if len(plot_df):
    ui.plot(charts.scatter_xy(plot_df, "sr_n", "sr_p", "name",
                              "Raw death-over strike rate, pressure against normal",
                              "raw normal strike rate", "raw strike rate under pressure"))
else:
    st.info("No batter has enough pressure balls for this view.")

st.subheader("Compare selected batters")
names = table.sort_values("balls_p", ascending=False).name.tolist()
chosen = st.multiselect("Batters", names, default=names[:3], max_selections=4, key="bat_cmp")
sel = table[table.name.isin(chosen)]
if len(sel):
    left, right = st.columns(2)
    with left:
        cmp = sel.rename(columns={"sr_p": "Pressure", "sr_n": "Normal"})
        ui.plot(charts.grouped_bars(cmp, "name", ["Pressure", "Normal"], "Raw death-over strike rate", "runs per 100 balls"))
    with right:
        cmp2 = sel.rename(columns={"out100_p": "Pressure", "out100_n": "Normal"})
        ui.plot(charts.grouped_bars(cmp2, "name", ["Pressure", "Normal"], "Raw dismissals", "dismissed per 100 balls"))
else:
    st.info("Choose one to four batters to compare.")

st.subheader("Season trend for one batter, raw death overs")
pick = st.selectbox("Batter", names, key="bat_trend")
pid = int(table[table.name == pick].pid.iloc[0])
trend = S.bat_by_year(d, pid)
if len(trend):
    ui.plot(charts.line(trend, "year", "value", "series", f"{pick}: raw strike rate by season (death overs)",
                        "runs per 100 balls"))
    ui.table(trend.rename(columns={"year": "Season", "series": "Condition", "value": "Raw strike rate",
                                   "balls": "Legal balls"}), digits=1, key="bat_trend_t")
else:
    st.info("No death-over deliveries recorded for this batter in the chosen scope.")

bands = S.urgency_bands(d, "bat")
if bands is not None:
    band_df, ylabel = bands
    ui.plot(charts.bar(band_df, "band", "value", "Raw death-over strike rate under pressure, by urgency quartile",
                       ylabel))

st.subheader("Recorded shot types")
mat = visuals.shot_mix(o, table[table.name.isin(chosen)].pid.tolist())
if mat is not None:
    ui.plot(charts.heatmap(mat, "Share of each batter's recorded shot labels"))
