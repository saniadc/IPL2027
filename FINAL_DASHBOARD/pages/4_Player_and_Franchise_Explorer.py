import pandas as pd
import streamlit as st

from components import ui
from utils import franchise as F
from utils import scouting as S
from utils.cache import outputs

st.title("Player & Franchise Explorer")
o = outputs()
ppl = S.people(o)
seasons = o.get("fh_seasons")
if ppl is None or seasons is None:
    ui.missing("the franchise history files")
    st.stop()

verified = F.load_verified(o)
career = S.ipl_career(o).set_index("pid")
with_record = set(seasons.pid.astype(int))

chosen_fr = st.multiselect("Historical franchise (2022-2026)", sorted(seasons.franchise.dropna().unique()),
                           default=[], key="ex_fr", help="Empty = all franchises")
allowed = F.players_for_franchises(seasons, chosen_fr) if chosen_fr else set(ppl.pid)
pool = ppl[ppl.pid.isin(allowed)].sort_values("name")
if pool.empty:
    st.info("No player played for the chosen franchise(s) in 2022-2026.")
    st.stop()

names = dict(zip(pool.pid.astype(int), pool.name))
pid = st.selectbox("Search or choose a player", list(names), format_func=lambda p: names[p], key="ex_pick")
row = ppl[ppl.pid == pid].iloc[0]
fields = F.three_fields(verified, pid)
has_record = pid in with_record

st.subheader(row["name"])
ui.kpis([
    ("Historical franchise (latest)",
     (row.latest_historical_franchise if pd.notna(row.latest_historical_franchise) else "No recorded data")
     if has_record else "No IPL record",
     "From 2022-2026 squad records, not necessarily current"),
    ("Current affiliation", fields["affiliation"], "Officially dated source needed"),
    ("IPL 2027 auction status", fields["auction_status"], "Officially dated source needed"),
])
if not has_record:
    st.info("No 2022-2026 IPL record in the supplied research data; this does not establish that the player never played.")

if has_record:
    c = career.loc[pid]
    ui.kpis([
        ("Raw IPL runs 2022-26", f"{int(c.ipl_runs):,}" if pd.notna(c.ipl_runs) else "n/a", f"Raw strike rate {c.ipl_sr:.1f}"
         if pd.notna(c.ipl_sr) else "No batting figures"),
        ("Raw IPL wickets 2022-26", f"{int(c.ipl_wickets):,}" if pd.notna(c.ipl_wickets) else "n/a",
         f"Raw economy {c.ipl_economy:.2f}" if pd.notna(c.ipl_economy) else "No bowling figures"),
    ])

st.subheader("Season by season, IPL 2022-2026")
sr = F.season_rows(seasons, pid)
rows = []
for y in F.IPL_SEASONS:
    hit = sr[sr.season.astype(int) == y]
    if hit.empty:
        rows.append({"Season": y, "Franchise": "Missing record",
                     "Note": "No squad record in the supplied data. This is a data gap, not a confirmed absence."})
        continue
    r = hit.iloc[0]
    note = "; ".join(n for n in [F.appearance_note(r.matches_played, r.listed_in_playing_eleven), r.sample_note] if n)
    rows.append({"Season": y, "Franchise": r.franchise, "Matches played": r.matches_played, "Raw IPL runs": r.runs,
                 "Raw IPL strike rate": r.strike_rate, "Dismissals": r.dismissals,
                 "Raw batting average": r.batting_average, "Legal balls bowled": r.legal_balls,
                 "Raw IPL wickets": r.wickets, "Raw IPL economy": r.economy, "Note": note})
ui.table(pd.DataFrame(rows), name="season table", download_name=f"{row['name']}_seasons.csv".replace(" ", "_"),
         digits=2, key="ex_seasons")
st.subheader("Compare players")
others = st.multiselect("Up to three players", [n for p, n in names.items() if p != pid], default=[], max_selections=3,
                        key="ex_cmp")
if others:
    pids = [pid] + [p for p, n in names.items() if n in others]
    cc = career.reindex(pids)
    tab = pd.DataFrame({
        "Player": [ppl[ppl.pid == p].name.iloc[0] for p in pids],
        "Research batting label": [ppl[ppl.pid == p].bat_status.iloc[0] for p in pids],
        "Research bowling label": [ppl[ppl.pid == p].bowl_status.iloc[0] for p in pids],
        "Raw IPL runs 2022-26": cc.ipl_runs.values,
        "Raw IPL strike rate": cc.ipl_sr.values,
        "Raw IPL wickets 2022-26": cc.ipl_wickets.values,
        "Raw IPL economy": cc.ipl_economy.values,
        "Latest historical franchise": [ppl[ppl.pid == p].latest_historical_franchise.iloc[0] for p in pids],
    }).set_index("Player").T.rename_axis("Measure").reset_index()
    ui.table(tab, digits=2, key="ex_cmp_t")
