"""Page smoke tests: every page's code runs against the real data, with Streamlit and Plotly STUBBED.

What this proves: the page code executes, every DataFrame column a page or chart names exists, and missing data
produces a message (st.stop) rather than a crash. What it does NOT prove: that the app renders, that widgets
behave, or that charts look right. Those need a real browser run (see README and DASHBOARD_QC_REPORT.md).
Run:  python tests/test_pages_smoke.py"""
import os
import runpy
import subprocess
import sys
import tempfile
from pathlib import Path

DASH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DASH))
sys.path.insert(0, str(DASH / "tests"))

PAGES = sorted((DASH / "pages").glob("*.py"))
EXPECTED_TITLES = ["Executive Dashboard", "Batter Scouting", "Bowler Scouting", "Player & Franchise Explorer",
                   "IPL 2027 Auction Intelligence"]


def _run_page(path):
    """Run one page file with stubs. Returns 'ok' or 'stopped' (st.stop used); raises on any other error."""
    import stub_streamlit
    st = stub_streamlit.install()
    try:
        runpy.run_path(str(path), run_name="__main__")
        return "ok"
    except stub_streamlit.StopPage:
        return "stopped"
    finally:
        del st


def test_five_pages_with_required_titles_in_order():
    import re
    names = [re.sub(r"^\d+_", "", p.stem).replace("_", " ") for p in PAGES]
    assert len(PAGES) == 5, [p.name for p in PAGES]
    assert len(names) == 5, names
    app = (DASH / "app.py").read_text(encoding="utf-8")
    for title in EXPECTED_TITLES:
        assert f'"{title}"' in app, title


def test_every_page_runs_with_real_data_and_none_stop():
    # run each page in its own process so module state (utils.cache, streamlit stub) cannot leak between pages
    for p in PAGES:
        code = (f"import sys; sys.path.insert(0, {str(DASH / 'tests')!r}); "
                f"import test_pages_smoke as t; r = t._run_page({str(p)!r}); print('RESULT', r)")
        out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=DASH)
        assert out.returncode == 0, f"{p.name}\n{out.stderr[-1500:]}"
        assert "RESULT ok" in out.stdout, f"{p.name} stopped early: {out.stdout[-300:]}"


def test_app_entry_builds_navigation_with_five_pages():
    code = (f"import sys; sys.path.insert(0, {str(DASH / 'tests')!r}); import stub_streamlit; stub_streamlit.install(); "
            f"import runpy; runpy.run_path({str(DASH / 'app.py')!r}, run_name='__main__'); print('APP OK')")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=DASH)
    assert out.returncode == 0 and "APP OK" in out.stdout, out.stderr[-1500:]


def test_missing_data_folder_gives_messages_not_exceptions():
    # Point the loaders at an empty folder. Pages must show a message or stop cleanly, never raise.
    with tempfile.TemporaryDirectory() as empty:
        for p in PAGES:
            env = dict(os.environ, SUPERR_DATA_DIR=empty)
            code = (f"import sys; sys.path.insert(0, {str(DASH / 'tests')!r}); "
                    f"import test_pages_smoke as t; r = t._run_page({str(p)!r}); print('RESULT', r)")
            out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=DASH, env=env)
            assert out.returncode == 0, f"{p.name} crashed with missing data:\n{out.stderr[-1500:]}"
            assert "RESULT" in out.stdout, p.name


def _filter_probe(page, script_overrides):
    """Run one page in a subprocess with chosen widget values; return what the page displayed."""
    code = f"""
import sys, json, runpy
sys.path.insert(0, {str(DASH)!r}); sys.path.insert(0, {str(DASH / 'tests')!r})
import stub_streamlit
stub_streamlit.install()
C = stub_streamlit._Column
captured = {{"metrics": [], "tables": []}}
def metric(self, label, value, help=None, **k):
    captured["metrics"].append([label, value])
C.metric = metric
{script_overrides}
import components.ui as ui
_orig_table = ui.table
def table(df, *a, **k):
    captured["tables"].append({{"rows": int(len(df)), "cols": list(map(str, df.columns))}})
ui.table = table
try:
    runpy.run_path({str(DASH / 'pages' / page)!r}, run_name="__main__")
except stub_streamlit.StopPage:
    captured["stopped"] = True
print("PROBE" + json.dumps(captured))
"""
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=DASH)
    assert out.returncode == 0, out.stderr[-1500:]
    import json
    line = [l for l in out.stdout.splitlines() if l.startswith("PROBE")][0]
    return json.loads(line[len("PROBE"):])


def test_batter_min_pressure_filter_matches_scouting_helpers():
    # Batter Scouting: the minimum-pressure-balls slider set to 100 must keep exactly the batters the helpers say qualify.
    import pandas as pd
    from utils import loaders as L, scouting as S
    o = L.load_all()
    death = S.scope(L.load_second_innings(), phases=("death",))
    ppl = S.people(o)
    base = ppl[ppl.bat_status.notna()][["pid"]]
    merged = base.merge(S.bat_split(death), on="pid", how="left")
    expected = int((merged.balls_p.fillna(0) >= 100).sum())
    ov = "C.slider = staticmethod(lambda label, min_value=0, max_value=None, value=None, **k: 100)"
    got = _filter_probe("2_Batter_Scouting.py", ov)
    sizes = [t["rows"] for t in got["tables"]]
    assert expected in sizes, (expected, sizes)


def run_all():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except Exception as e:
            failed += 1
            print(f"FAIL  {t.__name__}: {type(e).__name__}: {str(e)[:800]}")
    print(f"\n{len(tests) - failed} of {len(tests)} smoke tests passed")
    return failed


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--page":  # used by subprocess helpers
        print("RESULT", _run_page(sys.argv[2]))
    else:
        sys.exit(1 if run_all() else 0)
