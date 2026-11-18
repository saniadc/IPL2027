# Final decision note

**Decision.** No statistically supported pressure-specific ranking can be established for batters or bowlers from this data. The batter top 10 is a provisional operational shortlist. The bowler top 10 is not a ranking.

| Question | Batters | Bowlers |
|---|---|---|
| Population pressure effect | Not detected (+0.020, p = 0.48) | Not detected (−0.011, p = 0.70) |
| Pressure heterogeneity, raw | τ = 0.250, p = 0.0009 (mostly general ability) | τ = 0.058, p = 0.36 |
| Pressure heterogeneity, ability-controlled | τ = 0.188, p = 0.058 (borderline) | τ = 0.022, p = 0.48 |
| Joint model τ_β | 0.172, p = 0.063 | 0.030, p = 0.32; ρ at boundary |
| Players with P(deviation > 0) ≥ 0.95 | 1 of 25 (Rinku Singh, 0.963) | 1 of 41 (Rashid Khan, 0.958) |
| Status | Provisional (role test not significant) | Not identifiable |

## Files
- `top10_batters.csv`: unchanged. Label: provisional shortlist; reflects general ability as well as pressure.
- `top10_bowlers.csv`: unchanged. Label: not a ranking (identical posterior means).
- `FINAL_PLAYER_EVALUATION.csv`: per-player estimates with P(deviation > 0). Status column enforces the gate.

## Why the top-10 files were not replaced
The brief asks that rankings change only if justified. The analyses added no evidence for a different order: the batter list stays largely the same under the ability-controlled view (9 of 10 names), and the bowler list has no ordering to replace it with.

## What would change the decision
- Roughly several times the current pressure exposure per player, to detect τ ≈ 0.15–0.20 for bowlers at useful power.
- The Final Research Protocol (not supplied; governs methodology).
- Resolution of the 207-match legal-ball anomaly.
- Full hierarchical Bayesian fit with prior predictive checks and MCMC diagnostics, if the panel requires it.

## Confidence
- No population pressure effect: moderate to high (both role tests null).
- Batter heterogeneity exists only in raw residuals; ability-controlled is borderline: moderate.
- Bowling not identifiable at current exposure: moderate to high.
- Posterior intervals are approximate and conservative at low τ: high (simulation).
