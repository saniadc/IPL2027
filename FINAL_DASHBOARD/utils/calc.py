"""Pure calculations on the saved outputs. No Streamlit, no Plotly. Nothing here re-estimates a model:
it reads saved values, applies the status gate, and counts or filters.
"""
import numpy as np
import pandas as pd

from utils import labels as L

ROLE_ALPHA = 0.05
P_THRESHOLD = 0.95
ROLE_NAME = {"bat": "batters", "bowl": "bowlers"}


def _missing(x):
    return x is None or (isinstance(x, float) and np.isnan(x)) or pd.isna(x)


def player_status(p_deviation, role_p, p_threshold=P_THRESHOLD, alpha=ROLE_ALPHA):
    """The status gate. SUPPORTED only if the role test is significant AND P clears the threshold."""
    if _missing(p_deviation) or _missing(role_p):
        return L.INSUFFICIENT
    if role_p < alpha:
        return L.SUPPORTED if p_deviation >= p_threshold else L.NOT_ESTABLISHED
    return L.PROVISIONAL_HIGH_P if p_deviation >= p_threshold else L.NOT_ESTABLISHED


def role_frame(final_eval, role):
    """Players of one role, with the dashboard status label attached (display only; source values untouched)."""
    if final_eval is None or "role" not in final_eval:
        return None
    d = final_eval[final_eval.role == role].copy()
    if d.empty:
        return None
    d["dashboard_status"] = [player_status(p, r) for p, r in
                             zip(d.P_deviation_from_population_gt0, d.role_level_tau_beta_p)]
    d["error90"] = 1.645 * d.beta_sd
    return d


def status_counts(final_eval):
    out = {}
    for role in ("bat", "bowl"):
        d = role_frame(final_eval, role)
        out[role] = {"players": 0 if d is None else len(d),
                     "supported": 0 if d is None else int((d.dashboard_status == L.SUPPORTED).sum()),
                     "high_p_provisional": 0 if d is None else int((d.dashboard_status == L.PROVISIONAL_HIGH_P).sum())}
    return out


def overlap_at_k(a, b, k=10):
    a, b = list(a)[:k], list(b)[:k]
    return len(set(a) & set(b)) / k if k else np.nan


def pressure_summary(df, by):
    """Share of second-innings states flagged strict pressure, by a grouping column."""
    g = df.groupby(by).agg(states=("pressure_strict", "size"), pressure=("pressure_strict", "sum")).reset_index()
    g["pressure_share"] = g.pressure / g.states
    return g


def filter_frame(df, **conditions):
    """Keep rows where each column is in the given list. None or empty means no filter."""
    if df is None:
        return None
    out = df
    for col, vals in conditions.items():
        if vals and col in out.columns:
            out = out[out[col].isin(vals)]
    return out


def headline_counts(o):
    """Counts shown on the overview. Each comes from one saved file."""
    m, alt, fe = o.get("matches"), o.get("alternatives"), o.get("final_eval")
    out = {}
    if m is not None:
        out["matches_total"] = len(m)
        out["matches_retained"] = int((m.exclusion_strict == "retained").sum())
    if alt is not None:
        strict = alt[alt.rule.astype(str).str.startswith("STRICT")]
        if len(strict):
            out["pressure_deliveries"] = int(strict.deliveries.iloc[0])
            out["pressure_matches"] = int(strict.matches.iloc[0])
    if fe is not None:
        sc = status_counts(fe)
        out["batters_evaluated"] = sc["bat"]["players"]
        out["bowlers_evaluated"] = sc["bowl"]["players"]
        out["supported"] = sc["bat"]["supported"] + sc["bowl"]["supported"]
        out["high_p_provisional"] = sc["bat"]["high_p_provisional"] + sc["bowl"]["high_p_provisional"]
    return out


def anomaly_counts(matches):
    """Legal-ball anomaly: total flagged, classed under the anomaly category, and flagged but classed earlier."""
    if matches is None or "anomaly_legal" not in matches:
        return None
    flagged = matches.anomaly_legal.astype(bool)
    in_cat = matches.exclusion_strict == "legal-ball anomaly"
    earlier = matches.loc[flagged & ~in_cat, "exclusion_strict"].value_counts()
    inn = matches.anomaly_inn_gt120.astype(bool) if "anomaly_inn_gt120" in matches else None
    over = matches.anomaly_over_gt6.astype(bool) if "anomaly_over_gt6" in matches else None
    return {"flagged": int(flagged.sum()), "in_anomaly_category": int(in_cat.sum()),
            "flagged_but_earlier_category": int((flagged & ~in_cat).sum()),
            "earlier_breakdown": earlier.to_dict(),
            # the flag is: an innings over 120 legal deliveries OR an over with more than 6 legal deliveries
            "flag_by_innings_over_120": None if inn is None else int((flagged & inn).sum()),
            "flag_by_over_only": None if inn is None or over is None else int((flagged & ~inn & over).sum())}


def h2_row(h2, role):
    if h2 is None or "role" not in h2:
        return None
    r = h2[h2.role == role]
    return r.iloc[0] if len(r) else None


def findings_table(o):
    """Headline findings. Every number is read from a saved output; missing inputs give 'not available'."""
    rows = []

    def add(finding, estimate, status):
        rows.append({"finding": finding, "estimate": estimate, "status": status})

    h1 = o.get("h1")
    if h1 is not None and "role" in h1:
        r = h1[h1.role == "bat"]
        if len(r):
            r = r.iloc[0]
            add("Population pressure effect, batters (pressure minus non-pressure residual)",
                f"{r.difference_pressure_minus_nonpressure:+.3f} runs/ball, p = {r.difference_p_two_sided:.2f}",
                L.NOT_ESTABLISHED)
    r = h2_row(o.get("h2"), "bat")
    if r is not None:
        add("Raw pressure heterogeneity, batters (includes general ability)",
            f"tau = {r.tau_mle:.3f}, p = {r.p_mixture:.4f}", L.RAW_ONLY)
    s = o.get("ability_summary")
    if s is not None and "role" in s:
        r = s[s.role == "bat"]
        if len(r):
            r = r.iloc[0]
            add("Ability-controlled pressure heterogeneity, batters",
                f"tau = {r.tau_mle:.3f}, p = {r.p_mixture:.3f}", L.NOT_ESTABLISHED)
    j = o.get("joint")
    if j is not None and "role" in j:
        for role, name in (("bat", "batters"), ("bowl", "bowlers")):
            r = j[j.role == role]
            if not len(r):
                continue
            r = r.iloc[0]
            rho_note = "; rho at upper boundary" if abs(r.rho) >= 0.95 else ""
            status = L.NOT_IDENTIFIABLE if role == "bowl" else L.NOT_ESTABLISHED
            add(f"Joint (ability, pressure response) model, {name}",
                f"tau_beta = {r.tau_beta:.3f}, p = {r.p_mixture_tau_beta:.3f}{rho_note}", status)
    fe = o.get("final_eval")
    sc = status_counts(fe)
    for role in ("bat", "bowl") if fe is not None else ():
        add(f"Players with P(deviation from population mean > 0) >= 0.95, {ROLE_NAME[role]}",
            f"{sc[role]['high_p_provisional']} of {sc[role]['players']} (role test not significant)"
            if sc[role]["supported"] == 0 else f"{sc[role]['supported']} supported",
            L.PROVISIONAL_HIGH_P if sc[role]["high_p_provisional"] else L.NOT_ESTABLISHED)
    if fe is not None:
        add("Players statistically supported as pressure-specific (both roles)",
            f"{sc['bat']['supported'] + sc['bowl']['supported']} of {sc['bat']['players'] + sc['bowl']['players']}",
            L.NOT_ESTABLISHED if sc["bat"]["supported"] + sc["bowl"]["supported"] == 0 else L.SUPPORTED)
    if o.get("top10_batters") is not None:
        add("Batter top-10 list", "10 names from the raw pressure residual", L.PROVISIONAL)
    if o.get("top10_bowlers") is not None:
        add("Bowler top-10 list", "10 names with identical posterior means", L.NOT_IDENTIFIABLE)
    if not rows:
        add("No model outputs found", "-", L.INSUFFICIENT)
    out = pd.DataFrame(rows)
    out["kind"] = out.status.map(L.KIND)
    return out


def bayes_mass_range(grid, role):
    """Range of P(tau_beta > 0.05) across the four priors for one role. None if the file is missing."""
    if grid is None or "role" not in grid:
        return None
    v = grid.loc[grid.role == role, "P_tau_beta_gt_0_05"]
    return (float(v.min()), float(v.max())) if len(v) else None


def rolling_players_range(rolling, role):
    if rolling is None or "role" not in rolling:
        return None
    v = rolling.loc[rolling.role == role, "n_players"]
    return (int(v.min()), int(v.max())) if len(v) else None


def sim_detection(sim, role, tau):
    """Detection rate (p < 0.05) for one role at one true tau, from the saved simulation."""
    if sim is None:
        return None
    r = sim[(sim.role == role) & (np.isclose(sim.true_tau, tau))]
    return float(r.detection_rate_p05.iloc[0]) if len(r) else None


def placebo_mean_overlap(placebo, role):
    if placebo is None or "role" not in placebo:
        return None
    r = placebo[placebo.role == role]
    return float(r.mean_top10_overlap_with_real.iloc[0]) if len(r) else None


def rank_by_posterior_mean_safe(df, col, identifiable):
    """A ranked order is returned only for an identifiable role; otherwise None (no misleading ranked chart)."""
    if not identifiable:
        return None
    return df.sort_values(col, ascending=False).reset_index(drop=True)


def role_tests(o, role):
    """Role-level test values as saved (raw, ability-controlled, joint). Missing values are None."""
    def pick(df, col):
        if df is None or "role" not in df or col not in df:
            return None
        r = df[df.role == role]
        return float(r[col].iloc[0]) if len(r) else None

    return {"raw_p": pick(o.get("h2"), "p_mixture"), "raw_tau": pick(o.get("h2"), "tau_mle"),
            "ability_p": pick(o.get("ability_summary"), "p_mixture"),
            "joint_p": pick(o.get("joint"), "p_mixture_tau_beta"),
            "joint_tau_beta": pick(o.get("joint"), "tau_beta"), "joint_rho": pick(o.get("joint"), "rho")}
