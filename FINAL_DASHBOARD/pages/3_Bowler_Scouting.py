import pandas as pd
import streamlit as st

from components import charts, ui
from utils import scouting as S
from utils import visuals
from utils.cache import outputs, second_innings

st.title("Bowler Scouting")
o = outputs()
si = second_innings()
ppl = S.people(o)
sel_file = o.get("top10_bowlers")
if si is None or ppl is None or sel_file is None:
    ui.missing("the research selection, evaluation and second-innings files")
    st.stop()

# ---- 1. research selection: original file order, not a ranking
st.subheader("Exploratory Bowler Selection — Not a Ranking")
status = dict(zip(ppl.pid.astype(int), ppl.bowl_status))
bl = pd.DataFrame({
    "Player": sel_file["name"].values,
    "Research status": [status.get(int(p)) for p in sel_file["pid"]],
    "Research model: posterior mean": sel_file["post_mean"].values,
    "Research model: P(top 10)": sel_file["P_top10"].values,
})
ui.table(bl, digits=3, name="research bowler selection", download_name="research_bowler_selection.csv",
         key="bowl_sel")

# ---- 2. full comparison: raw death-over statistics, newly calculated here
st.subheader("Bowler Performance Comparison")
f1, f2, f3 = st.columns([2, 2, 2])
leagues = f1.multiselect("Competition", sorted(si.league.unique()), default=[], key="bowl_lg",
                         help="Empty = all competitions in the research dataset")
years = f2.multiselect("Season", sorted(int(y) for y in si.year.unique()), default=[], key="bowl_yr")
min_balls = f3.slider("Minimum pressure balls", 0, 60, 0, key="bowl_min")

d = S.scope(si, leagues=leagues, years=years, phases=("death",))
base = ppl[ppl.bowl_status.notna()][["pid", "name", "bowl_status"]]
table = base.merge(S.bowl_split(d), on="pid", how="left")
career = S.ipl_career(o)
if career is not None:
    table = table.merge(career[["pid", "ipl_wickets", "ipl_economy"]], on="pid", how="left")
table = table[table.balls_p.fillna(0) >= min_balls]
if table.empty:
    st.info("No bowler meets these filters.")
    st.stop()

show = pd.DataFrame({
    "Player": table.name,
    "Research status": table.bowl_status,
    "Pressure balls (sample)": table.balls_p.fillna(0).astype(int),
    "Raw death-over economy, pressure": table.econ_p,
    "Raw death-over economy, normal": table.econ_n,
    "Raw wickets per 100 balls, pressure": table.wkt100_p,
    "Raw wickets per 100 balls, normal": table.wkt100_n,
    "Raw IPL 2022-26 wickets": table.ipl_wickets if "ipl_wickets" in table else None,
    "Raw IPL 2022-26 economy": table.ipl_economy if "ipl_economy" in table else None,
    "Sample": table.balls_p.map(S.sample_note),
}).sort_values("Pressure balls (sample)", ascending=False)
summary_cols = ["Player", "Pressure balls (sample)", "Raw death-over economy, pressure", "Raw death-over economy, normal",
                "Sample"]
ui.table(show[summary_cols], digits=2, key="bowl_sum")
with st.expander("All bowler statistics, with download"):
    ui.table(show, name="bowler performance comparison", download_name="bowler_performance_comparison.csv",
             digits=2, key="bowl_table")

plot_df = table.dropna(subset=["econ_p", "econ_n"])
plot_df = plot_df[plot_df.balls_p >= S.SMALL_SAMPLE_BALLS]
if len(plot_df):
    ui.plot(charts.scatter_xy(plot_df, "econ_n", "econ_p", "name",
                              "Raw death-over economy, pressure against normal",
                              "raw normal economy", "raw economy under pressure"))
else:
    st.info("No bowler has enough pressure balls for this view.")

st.subheader("Compare selected bowlers")
names = table.sort_values("balls_p", ascending=False).name.tolist()
chosen = st.multiselect("Bowlers", names, default=names[:3], max_selections=4, key="bowl_cmp")
sel = table[table.name.isin(chosen)]
if len(sel):
    left, right = st.columns(2)
    with left:
        cmp = sel.rename(columns={"econ_p": "Pressure", "econ_n": "Normal"})
        ui.plot(charts.grouped_bars(cmp, "name", ["Pressure", "Normal"], "Raw death-over economy", "runs per over"))
    with right:
        cmp2 = sel.rename(columns={"wkt100_p": "Pressure", "wkt100_n": "Normal"})
        ui.plot(charts.grouped_bars(cmp2, "name", ["Pressure", "Normal"], "Raw wickets", "wickets per 100 balls"))
else:
    st.info("Choose one to four bowlers to compare.")

st.subheader("Season trend for one bowler, raw death overs")
pick = st.selectbox("Bowler", names, key="bowl_trend")
pid = int(table[table.name == pick].pid.iloc[0])
trend = S.bowl_by_year(d, pid)
if len(trend):
    ui.plot(charts.line(trend, "year", "value", "series", f"{pick}: raw economy by season (death overs)",
                        "runs per over"))
    ui.table(trend.rename(columns={"year": "Season", "series": "Condition", "value": "Raw economy",
                                   "balls": "Legal balls"}), digits=2, key="bowl_trend_t")
else:
    st.info("No death-over deliveries recorded for this bowler in the chosen scope.")

bands = S.urgency_bands(d, "bowl")
if bands is not None:
    band_df, ylabel = bands
    ui.plot(charts.bar(band_df, "band", "value", "Raw death-over economy under pressure, by urgency quartile", ylabel))

st.subheader("Recorded delivery styles")
mix = visuals.delivery_mix(o, pid)
if mix is not None:
    ui.plot(charts.bar(mix, "delivery_style", "share_of_classified", f"{pick}: share of recorded delivery styles",
                       "share of classified deliveries"))
