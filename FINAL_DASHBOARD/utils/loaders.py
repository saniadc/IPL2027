"""Pure loaders (no Streamlit). A missing or unreadable file returns None; nothing here raises on a missing file.

FILES is the single list of research outputs the dashboard reads. Paths are relative to the data folder."""
from pathlib import Path

import pandas as pd

from utils.paths import DATA

FILES = {
    # player-level decision files (provided; never edited by the dashboard)
    "top10_batters": "final/top10_batters.csv",
    "top10_bowlers": "final/top10_bowlers.csv",
    "final_eval": "final/FINAL_PLAYER_EVALUATION.csv",
    "decision_note": "final/FINAL_DECISION_NOTE.md",
    # model and validation outputs
    "joint": "final/JOINT_MODEL_RESULTS.csv",
    "grid": "final/BAYES_GRID_TAU_BETA_PRIOR_SENSITIVITY.csv",
    "opp": "final/OPPOSITION_ADJUSTMENT.csv",
    "abcd": "final/MODEL_ABCD_ROLLING_ORIGIN_LEAKAGE_FREE.csv",
    "conc": "final/CONCENTRATION_PREDICTIVE_TEST.csv",
    "sim": "final/SIMULATION_RECOVERY_RESULTS_v2.csv",
    "sens": "final/SENSITIVITY_RESULTS_v2.csv",
    "h1": "review/H1_population_pressure_effect.csv",
    "h2": "review/H2_profile_likelihood_tau.csv",
    "ability_summary": "review/ability_controlled_summary.csv",
    "ability_bat": "review/ability_controlled_bat.csv",
    "wp_metrics": "tables/phase2_wp_metrics_second_innings.csv",
    "wp_bins": "tables/phase2_calibration_bins_second_innings.csv",
    "split_half": "tables/phase6_reliability.csv",
    "rolling": "tables/phase7_rolling_origin.csv",
    "placebo": "tables/phase9_placebo.csv",
    "identifiability": "tables/identifiability_check.csv",
    "phase1_checks": "tables/phase1_validation_checks.csv",
    # data coverage and exclusions (frozen Phase 0 and Phase 1 outputs)
    "matches": "processed/matches_master.csv",
    "register": "processed/matches_exclusion_register.csv",
    "exclusion_log": "processed/data_exclusion_log.csv",
    "waterfall": "processed/phase0_v2_frozen/pressure_waterfall_strict.csv",
    "alternatives": "processed/phase0_v2_frozen/pressure_alternatives.csv",
    "exposure": "processed/phase0_v2_frozen/exposure_by_league_regular.csv",
    "frozen_spec": "processed/FROZEN_SPEC.md",
    # real-data aggregates from the raw ball-by-ball file (tools/build_visual_aggregates.py); labels, not locations
    "vis_batter": "processed/visual_batter_summary.csv",
    "vis_shots": "processed/visual_batter_shots.csv",
    "vis_delivery": "processed/visual_bowler_delivery.csv",
    # franchise history (tools/build_franchise_history.py) and the verification files (manual, dated, sourced)
    "fh_players": "processed/franchise_history_players.csv",
    "fh_seasons": "processed/franchise_history_seasons.csv",
    "fh_status_verified": "manual/ipl2027_status_verified.csv",
    "fh_affiliation_verified": "manual/current_affiliation_verified.csv",
    # large table, loaded only by the pressure pages
    "second_innings": "processed/second_innings_pressure.csv.gz",
}

TEXT_KEYS = {"decision_note", "frozen_spec"}
SECOND_INNINGS_COLS = [
    "match_id", "innings", "league", "year", "phase", "striker_id", "bowler_id", "legal", "runs",
    "bowler_conceded", "batter_out", "bowler_wkt", "pressure_strict", "leverage", "closeness",
    "urgency_rate_gap", "scarcity_balls", "scarcity_wkts", "wp_oof", "balls_rem", "wk", "runs_needed", "rrr",
]


def _root(root):
    return DATA if root is None else Path(root)


def read_csv(path, **kw):
    p = Path(path)
    if not p.is_file():
        return None
    try:
        return pd.read_csv(p, **kw)
    except Exception:
        return None


def read_text(path):
    p = Path(path)
    if not p.is_file():
        return None
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return None


def load(key, root=None, **kw):
    """One output by key. Returns a DataFrame, text, or None when the file is missing."""
    path = _root(root) / FILES[key]
    if key in TEXT_KEYS:
        return read_text(path)
    return read_csv(path, **kw)


def load_all(root=None):
    """Every small output by key (the large second-innings table is loaded separately)."""
    return {k: load(k, root) for k in FILES if k != "second_innings"}


def load_second_innings(root=None):
    path = _root(root) / FILES["second_innings"]
    return read_csv(path, usecols=lambda c: c in SECOND_INNINGS_COLS)


def file_status(root=None):
    """Presence and size of every required file: used by the coverage page and the tests."""
    rows = []
    for key, rel in FILES.items():
        p = _root(root) / rel
        rows.append({"output": key, "file": rel, "present": p.is_file(),
                     "kilobytes": round(p.stat().st_size / 1024, 1) if p.is_file() else None})
    return pd.DataFrame(rows)
