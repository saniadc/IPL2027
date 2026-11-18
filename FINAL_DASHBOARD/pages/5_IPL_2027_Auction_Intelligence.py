import pandas as pd
import streamlit as st

from components import ui
from utils import franchise as F
from utils import labels as L
from utils import scouting as S
from utils.cache import outputs, second_innings

st.title("IPL 2027 Auction Intelligence")
o = outputs()
si = second_innings()
ppl = S.people(o)
if ppl is None or si is None:
    ui.missing("the player evaluation and second-innings files")
    st.stop()

verified = F.load_verified(o)
death = S.scope(si, phases=("death",))
bs = S.bat_split(death).set_index("pid")
ws = S.bowl_split(death).set_index("pid")
career = S.ipl_career(o).set_index("pid")

st.subheader("Candidate evidence")
default = ppl[ppl.in_bat_shortlist | ppl.in_bowl_list].name.sort_values().tolist()
chosen = st.multiselect("Players", ppl.sort_values("name").name.tolist(), default=default, key="auc_pick")
sel = ppl[ppl.name.isin(chosen)].sort_values("name")
if sel.empty:
    st.info("Choose at least one player.")
    st.stop()


def fmt(v, nd=1):
    return "n/a" if v is None or pd.isna(v) else f"{v:.{nd}f}"


rows = []
for _, p in sel.iterrows():
    pid = int(p.pid)
    b = bs.loc[pid] if pid in bs.index else None
    w = ws.loc[pid] if pid in ws.index else None
    c = career.loc[pid] if pid in career.index else None
    f = F.three_fields(verified, pid)
    notes = []
    if pd.notna(p.bat_status):
        notes.append(f"Batting: {p.bat_status}")
    if pd.notna(p.bowl_status):
        notes.append(f"Bowling: {p.bowl_status}")
    if b is not None and b.balls_p < S.SMALL_SAMPLE_BALLS:
        notes.append("Small batting pressure sample")
    if w is not None and w.balls_p < S.SMALL_SAMPLE_BALLS:
        notes.append("Small bowling pressure sample")
    rows.append({
        "Player": p["name"],
        "Research status": "; ".join(notes) or "Not evaluated",
        "Raw death-over SR, pressure / normal": "n/a" if b is None else f"{fmt(b.sr_p)} / {fmt(b.sr_n)}",
        "Raw death-over economy, pressure / normal": "n/a" if w is None else f"{fmt(w.econ_p, 2)} / {fmt(w.econ_n, 2)}",
        "IPL 2022-26 runs": "n/a" if c is None or pd.isna(c.ipl_runs) else f"{int(c.ipl_runs):,}",
        "IPL 2022-26 wickets": "n/a" if c is None or pd.isna(c.ipl_wickets) else f"{int(c.ipl_wickets):,}",
        "Latest historical franchise": p.latest_historical_franchise if pd.notna(p.latest_historical_franchise)
        else "No IPL record",
        "Current affiliation": f["affiliation"],
        "IPL 2027 auction status": f["auction_status"],
    })
tab = pd.DataFrame(rows)
compact = ["Player", "Research status", "Raw death-over SR, pressure / normal", "Raw death-over economy, pressure / normal",
           "Current affiliation", "IPL 2027 auction status"]
ui.table(tab[compact], digits=None, key="auc_tab")
with st.expander("All candidate evidence, with download"):
    ui.table(tab, digits=None, name="candidate evidence", download_name="auction_candidate_evidence.csv", key="auc_full")
st.subheader("Compare two players")
names = sel.name.tolist()
a, b_name = st.columns(2)
pa = a.selectbox("Player A", names, index=0, key="auc_a")
pb = b_name.selectbox("Player B", names, index=min(1, len(names) - 1), key="auc_b")
cmp = tab.set_index("Player").loc[[pa, pb]].T.rename_axis("Measure").reset_index()
ui.table(cmp, digits=None, key="auc_cmp")

st.subheader("Practical considerations supported by the data")
notes = []
for _, p in sel.iterrows():
    pid = int(p.pid)
    if pd.notna(p.bat_status) and pid in bs.index:
        bb = bs.loc[pid]
        if bb.balls_p >= S.SMALL_SAMPLE_BALLS:
            notes.append(f"{p['name']} (batting): {int(bb.balls_p)} pressure balls; raw strike rate "
                         f"{fmt(bb.sr_p)} under pressure against {fmt(bb.sr_n)} normal. Status: {p.bat_status}.")
        else:
            notes.append(f"{p['name']} (batting): only {int(bb.balls_p)} pressure balls, below the "
                         f"{S.SMALL_SAMPLE_BALLS}-ball floor. No pressure conclusion is drawn.")
    if pd.notna(p.bowl_status) and pid in ws.index:
        ww = ws.loc[pid]
        if ww.balls_p >= S.SMALL_SAMPLE_BALLS:
            notes.append(f"{p['name']} (bowling): {int(ww.balls_p)} pressure balls; raw economy "
                         f"{fmt(ww.econ_p, 2)} under pressure against {fmt(ww.econ_n, 2)} normal. "
                         f"Status: {p.bowl_status}.")
        else:
            notes.append(f"{p['name']} (bowling): only {int(ww.balls_p)} pressure balls. No pressure conclusion is drawn.")
    if pd.isna(p.latest_historical_franchise):
        notes.append(f"{p['name']}: no 2022-2026 squad record, so no franchise history is shown.")
for n in notes:
    st.markdown(f"- {n}")
