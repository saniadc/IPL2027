"""The only status labels the dashboard may show. Each maps to a display colour.

Rules these labels encode (from the research conclusions):
- SUPPORTED needs BOTH a significant role-level heterogeneity test (p < 0.05) AND a player probability >= 0.95.
- A player with P >= 0.95 but a non-significant role test is PROVISIONAL_HIGH_P, never SUPPORTED.
- The batter list is a PROVISIONAL shortlist; the bowler list is NOT_IDENTIFIABLE (not a ranking)."""

SUPPORTED = "Statistically supported (pressure-specific)"
PROVISIONAL_HIGH_P = "Provisional: P >= 0.95, role test not significant"
PROVISIONAL = "Provisional shortlist"
RAW_ONLY = "Raw signal only: confounded with general ability"
NOT_ESTABLISHED = "Not statistically established"
INSUFFICIENT = "Insufficient evidence"
NOT_IDENTIFIABLE = "Not identifiable: not a ranking"
UNRESOLVED = "Unresolved: cause unknown"

# streamlit message kind for each label
KIND = {
    SUPPORTED: "success",
    PROVISIONAL_HIGH_P: "warning",
    PROVISIONAL: "warning",
    RAW_ONLY: "warning",
    NOT_ESTABLISHED: "warning",
    INSUFFICIENT: "info",
    NOT_IDENTIFIABLE: "error",
    UNRESOLVED: "error",
}

ALL_LABELS = tuple(KIND)
