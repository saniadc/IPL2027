"""Builds the small, real-data aggregates behind the Cricket Visuals page from the raw ball-by-ball file.

Run once, by hand:   python tools/build_visual_aggregates.py "path/to/ball_by_ball.csv"
Writes data/processed/visual_batter_summary.csv, visual_batter_shots.csv, visual_bowler_delivery.csv.

Definitions (chosen to match the research files):
- balls faced: deliveries where extras_type is not 'wide' (same rule as batter_faced in the research pipeline)
- runs: off-bat runs; boundaries: is_four or is_six
- dismissals: is_wicket rows where dismissed_player_id is the batter
- shots: the 'stroke' label as recorded; blank strokes are excluded from shares and counted separately
- delivery styles: the 'delivery_style' label as recorded; blank styles are excluded from shares
Nothing here is an estimate. Shot and delivery labels are NOT locations, so no wagon wheel or line-and-length grid is derived."""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parents[1]
OUT = HERE / "data" / "processed"
COLS = ["striker_id", "bowler_id", "dismissed_player_id", "runs", "is_four", "is_six", "is_wicket",
        "extras_type", "stroke", "delivery_style"]


def main(raw_path):
    b = pd.read_csv(raw_path, usecols=COLS, low_memory=False)
    fe = pd.read_csv(HERE / "data" / "final" / "FINAL_PLAYER_EVALUATION.csv", usecols=["role", "pid", "name"])
    bats = fe[fe.role == "bat"][["pid", "name"]]
    bowls = fe[fe.role == "bowl"][["pid", "name"]]

    faced = b[b.extras_type != "wide"]
    g = faced.groupby("striker_id")
    summ = pd.DataFrame({
        "balls_faced": g.size(), "runs": g.runs.sum(),
        "boundaries": g.apply(lambda d: int((d.is_four | d.is_six).sum()), include_groups=False),
        "fours": g.is_four.sum(), "sixes": g.is_six.sum(),
    })
    out_dis = b[b.is_wicket].groupby("dismissed_player_id").size().rename("dismissals")
    summ = summ.join(out_dis, how="left").fillna({"dismissals": 0})
    summ.index = summ.index.astype(int)
    summ = bats.assign(pid=bats.pid.astype(int)).merge(summ, left_on="pid", right_index=True, how="left")
    summ["strike_rate"] = (summ.runs / summ.balls_faced * 100).round(2)
    summ["boundary_pct"] = (summ.boundaries / summ.balls_faced * 100).round(2)
    summ["average"] = (summ.runs / summ.dismissals.replace(0, pd.NA)).astype("Float64").round(2)
    summ.to_csv(OUT / "visual_batter_summary.csv", index=False)

    st = b[b.stroke.notna()]
    shots = st.groupby(["striker_id", "stroke"]).size().rename("balls").reset_index()
    shots = shots.merge(bats.assign(pid=bats.pid.astype(int)), left_on="striker_id", right_on="pid")
    totals = shots.groupby("pid").balls.transform("sum")
    shots["share_of_classified"] = (shots.balls / totals).round(4)
    shots[["pid", "name", "stroke", "balls", "share_of_classified"]].to_csv(OUT / "visual_batter_shots.csv", index=False)

    dl = b[b.delivery_style.notna()]
    dd = dl.groupby(["bowler_id", "delivery_style"]).size().rename("balls").reset_index()
    dd = dd.merge(bowls.assign(pid=bowls.pid.astype(int)), left_on="bowler_id", right_on="pid")
    totals = dd.groupby("pid").balls.transform("sum")
    dd["share_of_classified"] = (dd.balls / totals).round(4)
    dd[["pid", "name", "delivery_style", "balls", "share_of_classified"]].to_csv(
        OUT / "visual_bowler_delivery.csv", index=False)
    print("batters", len(summ), "shot rows", len(shots), "bowlers", bowls.shape[0], "delivery rows", len(dd))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "ball_by_ball.csv")
