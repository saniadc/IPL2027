"""Reconciliation: saved data versus the figures quoted in the final report and decision note.

Each check states its source for the expected value. A check that fails is reported as FAIL. Two inconsistencies
already found in the research outputs are listed in KNOWN_INCONSISTENCIES; they are shown as FLAG, not hidden, and
the research outputs are not edited to remove them (see DASHBOARD_QC_REPORT.md)."""
import numpy as np
import pandas as pd

from utils import calc
from utils import labels as L

COLUMNS = ["check", "source of expected value", "expected", "from saved data", "result"]
KNOWN_INCONSISTENCIES = {
    "decision_note_bowler_raw_p",
    "batter_top10_identifiable_flag",
}
DESCRIPTIONS = {
    "decision_note_bowler_raw_p": "FINAL_DECISION_NOTE gives the bowler raw heterogeneity p-value as 0.36. The saved "
                                  "H2 output gives 0.3545, which rounds to 0.35 at two decimals.",
    "batter_top10_identifiable_flag": "top10_batters.csv marks identifiable_ranking = True on every row, which reads as "
                                      "a supported ranking. The research rule (batter role test p = 0.063) makes it a "
                                      "provisional shortlist, so this page labels it that way.",
}


def _check(rows, key, source, expected, observed, dp=None):
    if dp is not None and isinstance(observed, (float, np.floating)):
        ok = round(float(observed), dp) == expected
    else:
        ok = observed == expected
    result = "PASS" if ok else ("FLAG (documented)" if key in KNOWN_INCONSISTENCIES else "FAIL")
    rows.append({"check": key, "source of expected value": source, "expected": expected,
                 "from saved data": observed, "result": result})


def run_checks(o, second_innings=None):
    """Return a DataFrame of checks. `o` is loaders.load_all(); `second_innings` is optional (large table)."""
    rows = []
    alt, fe, m = o.get("alternatives"), o.get("final_eval"), o.get("matches")
    note = o.get("decision_note") or ""

    if second_innings is not None:
        _check(rows, "pressure_deliveries_second_innings", "FINAL_RESEARCH_REPORT executive summary: 8,467 deliveries",
               8467, int(second_innings.pressure_strict.sum()))
    if alt is not None:
        strict = alt[alt.rule.astype(str).str.startswith("STRICT")].iloc[0]
        _check(rows, "pressure_deliveries_frozen", "FINAL_RESEARCH_REPORT executive summary: 8,467 deliveries",
               8467, int(strict.deliveries))
        _check(rows, "pressure_matches", "FINAL_RESEARCH_REPORT executive summary: 386 matches", 386, int(strict.matches))
    ac = calc.anomaly_counts(m)
    if ac:
        _check(rows, "legal_ball_anomaly_flagged", "FINAL_RESEARCH_REPORT section 7 (Limitations): 207-match anomaly",
               207, ac["flagged"])
    if m is not None:
        _check(rows, "matches_total_equals_register", "matches_master vs exclusion register (same match count)",
               len(m), len(o["register"]) if o.get("register") is not None else -1)

    if fe is not None:
        sc = calc.status_counts(fe)
        _check(rows, "batters_evaluated", "FINAL_DECISION_NOTE table: '1 of 25'", 25, sc["bat"]["players"])
        _check(rows, "bowlers_evaluated", "FINAL_DECISION_NOTE table: '1 of 41'", 41, sc["bowl"]["players"])
        _check(rows, "players_supported", "FINAL_DECISION_NOTE decision: no supported player", 0,
               sc["bat"]["supported"] + sc["bowl"]["supported"])
        hi = fe[fe.P_deviation_from_population_gt0 >= 0.95]
        bat_hi = hi[hi.role == "bat"]
        bowl_hi = hi[hi.role == "bowl"]
        _check(rows, "batter_P_ge_095_name", "FINAL_DECISION_NOTE: Rinku Singh",
               "Rinku Singh", bat_hi.name.iloc[0] if len(bat_hi) else None)
        _check(rows, "bowler_P_ge_095_name", "FINAL_DECISION_NOTE: Rashid Khan",
               "Rashid Khan", bowl_hi.name.iloc[0] if len(bowl_hi) else None)
        if len(bat_hi):
            _check(rows, "batter_P_value", "FINAL_DECISION_NOTE: 0.963", 0.963,
                   float(bat_hi.P_deviation_from_population_gt0.iloc[0]), dp=3)
        if len(bowl_hi):
            _check(rows, "bowler_P_value", "FINAL_DECISION_NOTE: 0.958", 0.958,
                   float(bowl_hi.P_deviation_from_population_gt0.iloc[0]), dp=3)

    t10b, t10w = o.get("top10_batters"), o.get("top10_bowlers")
    if t10b is not None:
        _check(rows, "batter_top10_rows", "Final decision: exactly 10 batters", 10, len(t10b))
        names_ok = fe is not None and set(t10b.name) <= set(fe[fe.role == "bat"].name)
        _check(rows, "batter_top10_names_in_evaluation", "every shortlisted batter has an evaluation row", True, bool(names_ok))
        _check(rows, "batter_top10_identifiable_flag",
               "Research rule: batter list is a provisional shortlist (role test p = 0.063), not an identifiable ranking",
               False, bool(t10b.identifiable_ranking.all()))
    if t10w is not None:
        _check(rows, "bowler_top10_rows", "Final decision: exactly 10 bowlers", 10, len(t10w))
        _check(rows, "bowler_top10_not_identifiable", "Research rule: bowler list is not an identifiable ranking",
               True, bool((t10w.identifiable_ranking == False).all()))  # noqa: E712

    wp = o.get("wp_metrics")
    if wp is not None and "auc" in wp:
        row = wp[wp.iloc[:, 0].astype(str) == "all"] if wp.shape[1] > 0 else wp.iloc[:0]
        if len(row):
            _check(rows, "wp_auc_out_of_fold", "FINAL_RESEARCH_REPORT section 3 (Methodology): AUC 0.894", 0.894, float(row.auc.iloc[0]), dp=3)
            _check(rows, "wp_brier", "FINAL_RESEARCH_REPORT section 3 (Methodology): Brier 0.132", 0.132, float(row.brier.iloc[0]), dp=3)

    h2 = o.get("h2")
    r = calc.h2_row(h2, "bat")
    if r is not None:
        _check(rows, "batter_raw_tau", "FINAL_DECISION_NOTE: tau = 0.250", 0.250, float(r.tau_mle), dp=3)
        _check(rows, "batter_raw_p", "FINAL_DECISION_NOTE: p = 0.0009", 0.0009, float(r.p_mixture), dp=4)
    rb = calc.h2_row(h2, "bowl")
    if rb is not None:
        _check(rows, "decision_note_bowler_raw_p", "FINAL_DECISION_NOTE table: bowlers 'p = 0.36'", 0.36,
               float(rb.p_mixture), dp=2)

    sim = o.get("sim")
    for role, tau, exp in (("bat", 0.15, 0.33), ("bat", 0.20, 0.56), ("bat", 0.30, 0.94),
                           ("bowl", 0.15, 0.45), ("bowl", 0.20, 0.82), ("bowl", 0.30, 0.99)):
        v = calc.sim_detection(sim, role, tau)
        if v is not None:
            _check(rows, f"sim_detection_{role}_tau{tau:.2f}", f"FINAL_RESEARCH_REPORT section 4 (Results): {exp}", exp, v, dp=2)

    if fe is not None:
        ad = o.get("abcd")  # optional extra check: Model A-D file is the leakage-free one
        if ad is not None and "leakage_free" in ad:
            _check(rows, "abcd_is_leakage_free", "Model A-D must use training-only baselines", True,
                   bool(ad.leakage_free.all()))
    return pd.DataFrame(rows, columns=COLUMNS)


def summary(df):
    """Counts by result, for display and tests."""
    return df.result.value_counts().to_dict() if len(df) else {}


def unexpected_failures(df):
    return df[df.result == "FAIL"]


__all__ = ["run_checks", "summary", "unexpected_failures", "KNOWN_INCONSISTENCIES", "L"]
