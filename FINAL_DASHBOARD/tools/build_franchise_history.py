"""Builds season-by-season IPL franchise history for the evaluated players, from the raw data pack.

Run once, by hand:   python tools/build_franchise_history.py "path/to/Data Pack"
Writes to data/processed/:
  franchise_history_seasons.csv   one row per player, IPL season and franchise (squad list from the mapping)
  franchise_history_players.csv   one row per evaluated person: franchise path and record status

What this is: the HISTORICAL franchise a player is recorded with in an IPL season (2022 onwards).
What this is NOT: current affiliation or IPL 2027 auction status. Neither is in the supplied data, so neither is written here.

Definitions match the research pipeline: a bowler is credited with caught, bowled, LBW, stumped and hit-wicket
dismissals on legal deliveries; runs conceded = off-bat runs + wide runs + no-ball penalty runs; balls faced exclude wides.
The script stops if the squad mapping and the playing-eleven records disagree for any player-season."""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parents[1]
OUT = HERE / "data" / "processed"
BOWLER_CREDIT = {"Caught", "Bowled", "LBW", "Stump", "Hit Wicket"}


def main(raw_dir):
    raw = Path(raw_dir)
    comps = pd.read_csv(raw / "competitions.csv")
    ipl = comps[comps.comp_name.fillna("").str.startswith("IPL")][["comp_id", "season"]]
    matches = pd.read_csv(raw / "matches.csv", usecols=["match_id", "comp_id"]).merge(ipl, on="comp_id")
    ipl_matches = set(matches.match_id)

    squad = pd.read_csv(raw / "competition_team_player_mapping.csv",
                        usecols=["comp_id", "team_id", "team_name", "player_id"]).merge(ipl, on="comp_id")
    squad = squad.drop_duplicates(["season", "player_id", "team_id"])
    if squad.duplicated(["season", "player_id"]).any():
        sys.exit("A player is mapped to two franchises in one season: stop and check the mapping.")

    all_lineup = pd.read_csv(raw / "playing_eleven.csv", usecols=["match_id", "team_id", "player_id", "is_played"])
    all_lineup = all_lineup[all_lineup.match_id.isin(ipl_matches)].merge(matches, on="match_id")
    listed = all_lineup.groupby(["season", "player_id", "team_id"]).match_id.nunique().rename(
        "listed_in_playing_eleven").reset_index()
    lineup = all_lineup[all_lineup.is_played.astype(str).str.lower() == "true"]
    played = lineup.groupby(["season", "player_id", "team_id"]).match_id.nunique().rename("matches_played").reset_index()
    chk = played.merge(squad[["season", "player_id", "team_id"]], how="left", indicator=True)
    if (chk._merge != "both").any():
        sys.exit("A player played for a franchise that is not in the squad mapping for that season: stop and check.")

    ball_cols = ["match_id", "batting_team_id", "bowling_team_id", "striker_id", "bowler_id", "dismissed_player_id",
                 "runs", "is_four", "is_six", "is_wicket", "dismissal_type", "extras_type", "extras1_runs"]
    b = pd.read_csv(raw / "ball_by_ball.csv", usecols=ball_cols, low_memory=False)
    b = b[b.match_id.isin(ipl_matches)].merge(matches, on="match_id")
    b["is_wide"] = b.extras_type == "wide"
    b["is_noball"] = b.extras_type == "Overstep"
    b["legal"] = ~(b.is_wide | b.is_noball)

    f = b[~b.is_wide]
    bat = f.groupby(["season", "striker_id", "batting_team_id"]).agg(
        balls_faced=("runs", "size"), runs=("runs", "sum"), fours=("is_four", "sum"), sixes=("is_six", "sum"))
    dis = b[b.is_wicket].groupby(["season", "dismissed_player_id", "batting_team_id"]).size().rename("dismissals")
    bat = bat.join(dis.rename_axis(["season", "striker_id", "batting_team_id"]), how="outer").fillna(0)
    bat.index = bat.index.set_names(["season", "pid", "team_id"])

    b["conceded"] = b.runs + b.extras1_runs.where(b.is_wide | b.is_noball, 0)
    bl = b[b.legal]
    bowl = b.groupby(["season", "bowler_id", "bowling_team_id"]).agg(conceded=("conceded", "sum"))
    bowl["legal_balls"] = bl.groupby(["season", "bowler_id", "bowling_team_id"]).size()
    bowl["wickets"] = bl[bl.is_wicket & bl.dismissal_type.isin(BOWLER_CREDIT)].groupby(
        ["season", "bowler_id", "bowling_team_id"]).size()
    bowl = bowl.fillna(0)
    bowl.index = bowl.index.set_names(["season", "pid", "team_id"])

    # The evaluation file has 66 role-evaluations for 61 people: five players are evaluated both as batter and as bowler.
    # The history is keyed by person; 'evaluated_as' records which evaluation or evaluations they have.
    fe = pd.read_csv(HERE / "data" / "final" / "FINAL_PLAYER_EVALUATION.csv", usecols=["role", "pid", "name"])
    evaluated = fe.groupby("pid").role.apply(lambda s: " and ".join(sorted(set(s))))
    evaluated = evaluated.map({"bat": "batter", "bowl": "bowler", "bat and bowl": "batter and bowler"})
    names = fe.drop_duplicates("pid").set_index("pid").name
    top_b = set(pd.read_csv(HERE / "data" / "final" / "top10_batters.csv").pid)
    top_w = set(pd.read_csv(HERE / "data" / "final" / "top10_bowlers.csv").pid)

    rows = squad.rename(columns={"player_id": "pid"})
    rows = rows[rows.pid.isin(names.index)]
    rows = rows.merge(played.rename(columns={"player_id": "pid"}), on=["season", "pid", "team_id"], how="left")
    rows["matches_played"] = rows.matches_played.fillna(0).astype(int)
    rows = rows.merge(bat.reset_index(), on=["season", "pid", "team_id"], how="left")
    rows = rows.merge(bowl.reset_index(), on=["season", "pid", "team_id"], how="left")
    rows["player_name"] = rows.pid.map(names)
    rows["evaluated_as"] = rows.pid.map(evaluated)
    rows["strike_rate"] = (rows.runs / rows.balls_faced * 100).where(rows.balls_faced > 0).round(2)
    rows["boundary_pct"] = ((rows.fours + rows.sixes) / rows.balls_faced * 100).where(rows.balls_faced > 0).round(2)
    rows["batting_average"] = (rows.runs / rows.dismissals).where(rows.dismissals > 0).round(2)
    rows["overs_bowled"] = (rows.legal_balls / 6).round(2)
    rows["economy"] = (rows.conceded * 6 / rows.legal_balls).where(rows.legal_balls > 0).round(2)
    rows["in_research_top10_batters"] = rows.pid.isin(top_b)
    rows["in_research_top10_bowlers"] = rows.pid.isin(top_w)
    rows = rows.merge(listed.rename(columns={"player_id": "pid"}), on=["season", "pid", "team_id"], how="left")
    rows["listed_in_playing_eleven"] = rows.listed_in_playing_eleven.fillna(0).astype(int)
    rows = rows.rename(columns={"team_name": "franchise"})
    keep = ["pid", "player_name", "evaluated_as", "season", "franchise", "team_id", "matches_played",
            "listed_in_playing_eleven",
            "balls_faced", "runs", "dismissals", "strike_rate", "batting_average", "boundary_pct",
            "legal_balls", "overs_bowled", "conceded", "wickets", "economy",
            "in_research_top10_batters", "in_research_top10_bowlers"]
    seasons = rows[keep].sort_values(["player_name", "season"]).reset_index(drop=True)
    for c in ["matches_played", "listed_in_playing_eleven", "balls_faced", "runs", "dismissals", "legal_balls", "conceded", "wickets"]:
        seasons[c] = seasons[c].astype("Int64")  # counts stay whole numbers; blanks mean not applicable
    seasons.to_csv(OUT / "franchise_history_seasons.csv", index=False)

    players = []
    for pid, g in seasons.groupby("pid", sort=False):
        g = g.sort_values("season")
        path = list(dict.fromkeys(g.franchise))
        players.append({
            "pid": pid, "player_name": g.player_name.iloc[0], "evaluated_as": g.evaluated_as.iloc[0],
            "seasons_in_squad": len(g), "seasons_with_match": int((g.matches_played > 0).sum()),
            "franchises_represented": " / ".join(path), "number_of_franchises": len(path),
            "first_season": int(g.season.min()), "latest_season": int(g.season.max()),
            "latest_historical_franchise": g.iloc[-1].franchise,
            "franchise_changes": int((g.franchise.values[1:] != g.franchise.values[:-1]).sum()),
            "in_research_top10_batters": bool(pid in top_b), "in_research_top10_bowlers": bool(pid in top_w),
        })
    for pid in names.index:
        if pid not in set(seasons.pid):
            players.append({"pid": pid, "player_name": names[pid], "evaluated_as": evaluated[pid],
                            "seasons_in_squad": 0, "seasons_with_match": 0, "franchises_represented": "",
                            "number_of_franchises": 0, "first_season": None, "latest_season": None,
                            "latest_historical_franchise": "", "franchise_changes": 0,
                            "in_research_top10_batters": bool(pid in top_b),
                            "in_research_top10_bowlers": bool(pid in top_w)})
    pl = pd.DataFrame(players).sort_values("player_name").reset_index(drop=True)
    pl.to_csv(OUT / "franchise_history_players.csv", index=False)
    print(f"season rows {len(seasons)}, people {len(pl)}, people with no IPL record {int((pl.seasons_in_squad == 0).sum())}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "Data Pack")
