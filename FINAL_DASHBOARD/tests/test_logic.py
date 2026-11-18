"""Data loaders, calculations, status gates, reconciliation, downloads and file integrity.
No Streamlit or Plotly needed. Run:   python tests/test_logic.py      (or: python -m pytest tests)"""
import csv
import hashlib
import io
import py_compile
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

DASH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DASH))

from utils import calc, labels as L, loaders, reconcile  # noqa: E402
from utils.paths import DATA, MANIFEST  # noqa: E402

_CACHE = {}


def _o():
    if "o" not in _CACHE:
        _CACHE["o"] = loaders.load_all()
        _CACHE["si"] = loaders.load_second_innings()
    return _CACHE["o"], _CACHE["si"]


# 1. compile -------------------------------------------------------------------------------------
def test_every_python_file_compiles():
    files = sorted(DASH.rglob("*.py"))
    for f in files:
        py_compile.compile(str(f), doraise=True)
    assert len(files) >= 20, len(files)


# 2. loaders: every required file present; missing files give None, never an exception -------------
def test_all_required_files_present():
    fs = loaders.file_status()
    assert fs.present.all(), fs[~fs.present]


def test_missing_root_returns_none_without_error():
    with tempfile.TemporaryDirectory() as empty:
        o = loaders.load_all(root=empty)
        assert all(v is None for v in o.values()), [k for k, v in o.items() if v is not None]
        assert loaders.load_second_innings(root=empty) is None
        fs = loaders.file_status(root=empty)
        assert not fs.present.any()


def test_real_outputs_load_and_have_expected_shape():
    o, si = _o()
    assert [k for k, v in o.items() if v is None] == []
    assert len(o["final_eval"]) == 66
    assert set(o["final_eval"].role) == {"bat", "bowl"}
    assert si is not None and len(si) == 66162
    assert {"pressure_strict", "league", "year", "phase", "leverage"}.issubset(si.columns)


# 3. reconciliation with the final report / decision note ------------------------------------------
def test_counts_reconcile_with_report():
    o, si = _o()
    hc = calc.headline_counts(o)
    assert hc["pressure_deliveries"] == 8467
    assert hc["pressure_matches"] == 386
    assert hc["batters_evaluated"] == 25 and hc["bowlers_evaluated"] == 41
    assert hc["matches_total"] == 883 and hc["matches_retained"] == 615
    assert int(si.pressure_strict.sum()) == 8467


def test_anomaly_counts_match_report_and_are_disjoint():
    o, _ = _o()
    ac = calc.anomaly_counts(o["matches"])
    assert ac["flagged"] == 207
    assert ac["in_anomaly_category"] + ac["flagged_but_earlier_category"] == ac["flagged"]
    assert ac["flagged_but_earlier_category"] == 6
    assert ac["flag_by_innings_over_120"] == 147 and ac["flag_by_over_only"] == 60
    assert ac["flag_by_innings_over_120"] + ac["flag_by_over_only"] == ac["flagged"]


def test_reconciliation_has_no_unexpected_failures():
    o, si = _o()
    checks = reconcile.run_checks(o, si)
    assert len(checks) >= 25
    assert reconcile.unexpected_failures(checks).empty, reconcile.unexpected_failures(checks)
    flagged = set(checks[checks.result.str.startswith("FLAG")].check)
    assert flagged == reconcile.KNOWN_INCONSISTENCIES, flagged


# 4. status gate and labels --------------------------------------------------------------------
def test_gate_supported_only_when_role_test_and_probability_both_pass():
    g = calc.player_status
    assert g(0.97, 0.001) == L.SUPPORTED
    assert g(0.97, 0.06) == L.PROVISIONAL_HIGH_P       # high P but role test not significant
    assert g(0.50, 0.001) == L.NOT_ESTABLISHED         # role significant, P too low
    assert g(0.50, 0.50) == L.NOT_ESTABLISHED
    assert g(0.97, float("nan")) == L.INSUFFICIENT
    assert g(None, 0.001) == L.INSUFFICIENT
    assert g(0.95, 0.049) == L.SUPPORTED               # boundaries are inclusive / exclusive as stated
    assert g(0.95, 0.05) == L.PROVISIONAL_HIGH_P


def test_real_players_are_never_labelled_supported_while_role_test_fails():
    o, _ = _o()
    counts = calc.status_counts(o["final_eval"])
    assert counts["bat"]["supported"] == 0 and counts["bowl"]["supported"] == 0
    bat = calc.role_frame(o["final_eval"], "bat")
    bowl = calc.role_frame(o["final_eval"], "bowl")
    rinku = bat[bat.name == "Rinku Singh"].dashboard_status.iloc[0]
    rashid_bowl = bowl[bowl.name == "Rashid Khan"].dashboard_status.iloc[0]
    assert rinku == L.PROVISIONAL_HIGH_P
    assert rashid_bowl == L.PROVISIONAL_HIGH_P
    # the research's own status column also says not supported, for every player
    assert not o["final_eval"].status.astype(str).str.startswith("statistically supported").any()
    assert o["final_eval"].status.astype(str).str.startswith("provisional").all()


def test_labels_are_consistent():
    assert set(L.KIND) == set(L.ALL_LABELS)
    assert all(v in {"success", "warning", "error", "info"} for v in L.KIND.values())
    assert L.KIND[L.SUPPORTED] == "success"
    assert L.KIND[L.NOT_IDENTIFIABLE] == "error"
    # the phrase "statistically supported" may appear unnegated only in the SUPPORTED label
    for lab in L.ALL_LABELS:
        if lab != L.SUPPORTED:
            assert not lab.startswith("Statistically supported")


def test_findings_use_only_defined_labels_and_bowler_list_is_not_ranking():
    o, _ = _o()
    ft = calc.findings_table(o)
    assert set(ft.status).issubset(set(L.ALL_LABELS)), set(ft.status) - set(L.ALL_LABELS)
    bowler = ft[ft.finding.str.startswith("Bowler top-10")]
    assert bowler.status.iloc[0] == L.NOT_IDENTIFIABLE
    batter = ft[ft.finding.str.startswith("Batter top-10")]
    assert batter.status.iloc[0] == L.PROVISIONAL
    supported_row = ft[ft.finding.str.startswith("Players statistically supported")]
    assert supported_row.status.iloc[0] == L.NOT_ESTABLISHED


def test_findings_handle_missing_inputs():
    ft = calc.findings_table({})
    assert len(ft) == 1 and ft.status.iloc[0] == L.INSUFFICIENT


# 5. shortlists: exact counts and unchanged source values -------------------------------------------
def test_shortlists_have_ten_rows_and_source_flags_as_delivered():
    o, _ = _o()
    assert len(o["top10_batters"]) == 10 and len(o["top10_bowlers"]) == 10
    assert set(o["top10_batters"].name) <= set(o["final_eval"][o["final_eval"].role == "bat"].name)
    assert not o["top10_bowlers"].identifiable_ranking.any()


# 6. filters and summaries --------------------------------------------------------------------
def test_filters_subset_and_empty_means_no_filter():
    _, si = _o()
    assert len(calc.filter_frame(si)) == len(si)
    assert len(calc.filter_frame(si, league=[])) == len(si)
    sub = calc.filter_frame(si, league=["IPL"])
    assert 0 < len(sub) < len(si) and set(sub.league) == {"IPL"}
    assert int(sub.pressure_strict.sum()) <= int(si.pressure_strict.sum())


def test_pressure_summary_reconciles_to_total():
    _, si = _o()
    s = calc.pressure_summary(si, "league")
    assert int(s.pressure.sum()) == int(si.pressure_strict.sum())
    assert int(s.states.sum()) == len(si)
    assert ((s.pressure_share >= 0) & (s.pressure_share <= 1)).all()


def test_overlap_at_k():
    assert calc.overlap_at_k(range(1, 11), range(1, 11)) == 1.0
    assert calc.overlap_at_k(range(1, 11), range(11, 21)) == 0.0
    assert calc.overlap_at_k([1, 2, 3, 4, 5], [1, 2, 9, 9, 9], k=5) == 0.4


def test_helpers_read_saved_values():
    o, _ = _o()
    lo, hi = calc.bayes_mass_range(o["grid"], "bat")
    assert 0 <= lo <= hi <= 1
    assert calc.rolling_players_range(o["rolling"], "bat") == (9, 12)
    assert abs(calc.sim_detection(o["sim"], "bowl", 0.20) - 0.8167) < 0.001
    assert calc.h2_row(o["h2"], "bowl").mean_se > 0.2
    rt = calc.role_tests(o, "bat")
    assert abs(rt["joint_p"] - 0.063) < 0.001 and abs(rt["ability_p"] - 0.058) < 0.001


# 7. downloads carry the correct data ----------------------------------------------------------
def test_as_delivered_downloads_match_manifest_and_project_source_when_present():
    manifest = {r["file"]: r["sha256"] for r in csv.DictReader(open(MANIFEST, encoding="utf-8"))}
    project = DASH.parent  # the research project root, when this folder sits inside it
    for rel in ("data/final/top10_batters.csv", "data/final/top10_bowlers.csv", "data/final/FINAL_PLAYER_EVALUATION.csv"):
        assert hashlib.sha256((DASH / rel).read_bytes()).hexdigest() == manifest[rel], rel
        source = project / rel.replace("data/final/", "data/final/")
        if source.is_file():
            assert source.read_bytes() == (DASH / rel).read_bytes(), f"copy differs from project source: {rel}"


def test_filtered_download_has_only_selected_rows_and_unrounded_values():
    o, _ = _o()
    fe = calc.role_frame(o["final_eval"], "bat")
    sub = fe[fe.pressure_deliveries >= 100]
    text = sub.to_csv(index=False)
    back = pd.read_csv(io.StringIO(text))
    assert len(back) == len(sub)
    assert set(back.name) == set(sub.name)
    # values are not rounded in the download
    assert back.P_deviation_from_population_gt0.iloc[0] == sub.P_deviation_from_population_gt0.iloc[0]


# 8. integrity of the bundled data ------------------------------------------------------------
def test_manifest_matches_every_file():
    rows = list(csv.DictReader(open(MANIFEST, encoding="utf-8")))
    listed = {r["file"] for r in rows}
    on_disk = {p.relative_to(DASH).as_posix() for base in (DATA, DASH / "assets") for p in base.rglob("*")
               if p.is_file() and p.name != "MANIFEST.csv"}
    assert listed == on_disk, (listed ^ on_disk)
    for r in rows:
        assert hashlib.sha256((DASH / r["file"]).read_bytes()).hexdigest() == r["sha256"], r["file"]


def test_no_absolute_paths_or_old_project_references_in_code():
    bad = []
    for f in list(DASH.rglob("*.py")) + [DASH / "requirements.txt"]:
        if "tests" in f.parts:
            continue
        txt = f.read_text(encoding="utf-8")
        for needle in ("/home/", "C:\\", "C:/", "/mnt/", "SUPERR_ROOT", "outputs/final", "outputs/review"):
            if needle in txt:
                bad.append((f.relative_to(DASH).as_posix(), needle))
    assert not bad, bad


def test_requirements_have_no_unused_packages():
    reqs = [l.split(">")[0].split("=")[0].strip().lower() for l in (DASH / "requirements.txt").read_text().splitlines()
            if l.strip() and not l.startswith("#")]
    code = "\n".join(f.read_text(encoding="utf-8") for f in DASH.rglob("*.py") if "tests" not in f.parts)
    for pkg in reqs:
        mod = {"streamlit": "streamlit", "plotly": "plotly", "pandas": "pandas", "numpy": "numpy"}[pkg]
        assert f"import {mod}" in code or f"from {mod}" in code, f"{pkg} listed but not imported"


def run_all():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except Exception as e:  # report every failure
            failed += 1
            print(f"FAIL  {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failed} of {len(tests)} logic tests passed")
    return failed


if __name__ == "__main__":
    sys.exit(1 if run_all() else 0)
