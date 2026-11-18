# IPL 2027 Auction Intelligence: Pressure Scouting Dashboard

A five-page Streamlit dashboard for franchise scouting. It presents the IPL 2027 pressure-reliability research and the 2022-2026 IPL and match evidence behind it. It reads saved research outputs and does not refit any model. Every number comes from a file in `data/`, and every status label follows the research rules.

**Headline:** no player is statistically supported as pressure-specific. The batter list is a provisional shortlist. The bowler list is exploratory and is not a ranking. The research did not establish statistically supported pressure-specific top-10 rankings.

---

## 1. What is in this folder

```
FINAL_DASHBOARD/
├── app.py                      entry point: streamlit run app.py
├── pages/                      the five pages (1_ to 5_)
├── tools/                      build scripts that create data from the raw data pack
├── components/                 shared UI (ui.py), Plotly chart builders (charts.py), stadium drawing (hero.py)
├── utils/                      loaders, calculations, scouting helpers, franchise verification, status labels
├── data/                       research outputs copied in unchanged, plus built tables; MANIFEST.csv lists SHA-256 checksums
├── assets/                     style.css, FINAL_RESEARCH_REPORT.pdf (for download), ASSET_LICENSES.md
├── tests/                      automated tests, the stub used by page tests, and build_manifest.py
├── .streamlit/config.toml      theme colours
├── requirements.txt            the four packages to install
├── README.md                   this file
└── DASHBOARD_QC_REPORT.md      what was tested, what passed, what could not be tested
```

The folder is self-contained. Every path is relative to this folder, so you can move or copy the whole folder anywhere.

## 2. Pages

| # | Page | What it shows |
|---|------|---------------|
| 1 | Executive Dashboard | Key indicators, the batter and bowler lists with their status labels, pressure against normal in the death overs, performance overview, pressure situation distribution, season trends, key findings, downloads |
| 2 | Batter Scouting | Batter table with pressure and normal strike rates, dismissals per 100 balls, IPL figures and sample flags; filters; comparison; season trend; urgency bands; recorded shot-type labels |
| 3 | Bowler Scouting | Bowler table with pressure and normal economy, wickets per 100 balls, IPL figures and sample flags; filters; comparison; season trend; urgency bands; recorded delivery-style labels |
| 4 | Player & Franchise Explorer | Searchable profiles, historical franchise filter, season-by-season figures 2022-2026 with missing records marked, dual-role display, comparison, and the three separate fields |
| 5 | IPL 2027 Auction Intelligence | Candidate evidence table, a two-player comparison, and practical considerations limited to what the data supports |

Filters change only what is displayed. They never change an estimate, a status or a source file.

Pressure figures compare **death overs only**. Every pressure state occurs in the death overs, so an all-overs comparison would mix in the faster scoring of those overs. The dashboard states this on each page where it applies.

Detailed methodology is in `FINAL_RESEARCH_REPORT.pdf` (downloadable from page 1) and in `FINAL_DECISION_NOTE.md`.

## 3. Setup on Windows with VS Code

You need Python 3.10 or newer. Check with `py --version` in PowerShell. If that command is not found, install Python from python.org and tick **Add python.exe to PATH**.

1. In VS Code choose **File > Open Folder** and select the `FINAL_DASHBOARD` folder.
2. Open a terminal with **Terminal > New Terminal**. It opens in the folder.
3. Create a virtual environment:

   ```powershell
   py -m venv .venv
   ```

4. Activate it:

   ```powershell
   .venv\Scripts\activate
   ```

   The prompt should now start with `(.venv)`. In PowerShell, if scripts are reported as disabled, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once and activate again.

5. In VS Code, select the interpreter: press `Ctrl+Shift+P`, choose **Python: Select Interpreter**, and pick the one inside `.venv`.

6. Install the packages:

   ```powershell
   py -m pip install -r requirements.txt
   ```

## 4. Launch the dashboard

From the `FINAL_DASHBOARD` folder, with the virtual environment active:

```powershell
streamlit run app.py
```

Your browser opens at `http://localhost:8501`. To stop, press `Ctrl+C` in the terminal.

If `streamlit` is not recognised, use `python -m streamlit run app.py`. That form always uses the interpreter you selected.

## 5. Run the tests

From the `FINAL_DASHBOARD` folder, with the virtual environment active:

```powershell
python tests\test_logic.py
python tests\test_franchise.py
python tests\test_visuals.py
python tests\test_scouting.py
python tests\test_pages_smoke.py
```

- `test_logic.py` checks the loaders, calculations, status gates, reconciliation with the final report, downloads and file integrity. It does not need Streamlit or Plotly.
- `test_franchise.py` checks the squad-history build, the verification gate and the gap reporting. Set `SUPERR_RAW_DIR` to the raw data pack to also recount franchise figures from the raw file.
- `test_visuals.py` checks the visual data aggregates. Set `SUPERR_RAW_BALL` to the raw `ball_by_ball.csv` to also recount batter totals.
- `test_scouting.py` checks the death-overs matching, pinned pooled figures, urgency bands and the 61-person table.
- `test_pages_smoke.py` runs every page's code against the real data, with Streamlit and Plotly replaced by stand-ins. It proves that the code runs, that the columns exist, and that the filters change the displayed rows. It does **not** prove that the app renders correctly. Look at the app in a browser for that.

Each file should end with a count of passed tests and no `FAIL` lines. The QC report lists what the tests cover.

## 6. Replacing or adding research files

1. Put the new file in the matching folder under `data/`, using the **same file name** as the existing file. The list is in `utils/loaders.py` (the `FILES` dictionary).
2. Regenerate the checksum manifest:

   ```powershell
   python tests\build_manifest.py
   ```

3. Run the test files again.
4. Restart the dashboard (`Ctrl+C`, then `streamlit run app.py`). Or press `C` in the browser and choose **Clear cache**.

Rules for replacing files:

- **Keep the column names.** The pages read columns by name. The smoke test reports any column that is missing.
- **Keep the status logic.** A player is labelled statistically supported only if the role-level test p-value is below 0.05 and the player's probability is at least 0.95.
- **Do not edit the decision files to match the dashboard.** The logic tests compare the data with the final report. A mismatch is a finding, not a display bug.

To use a different folder of research outputs without copying files, set the environment variable `SUPERR_DATA_DIR` to that folder before launching. This is optional.

## 7. Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `streamlit : The term 'streamlit' is not recognized` | The virtual environment is not active, or was not created. Run steps 3 and 4 of Setup, then `python -m streamlit run app.py`. |
| `ModuleNotFoundError: No module named 'streamlit'` (or `plotly`) | Packages went into a different Python. Activate `.venv`, then run `py -m pip install -r requirements.txt`. |
| `running scripts is disabled on this system` | PowerShell execution policy. Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once. |
| `Port 8501 is already in use` | Another Streamlit is running. Stop it, or run `streamlit run app.py --server.port 8502`. |
| A page says `'<file>' is not in the data folder` | The file was moved or renamed. Put it back in `data\...` with the name listed in `utils\loaders.py`. |
| Numbers look out of date after replacing a file | Streamlit caches the outputs. Press `C` in the browser, then choose **Clear cache**, or restart the app. |
| Charts do not appear, or the app reports a version error | Plotly or Streamlit is older than required. Run `py -m pip install --upgrade -r requirements.txt`. |
| OneDrive folder causes slow starts or file locks | Move the `FINAL_DASHBOARD` folder out of the OneDrive-synced area, for example to `C:\Projects\`. |

## 8. Status of this build

- **Verified in the build environment:** the logic tests (22), franchise tests (14), visual tests (4), scouting tests (5) and page smoke tests (5) pass. The smoke tests run all five pages against the real data with stand-ins for Streamlit and Plotly, check that every named column exists, and check that the batter filter changes the displayed rows. The file checksums match.
- **Not verified:** the app has **not been launched in a browser**. Streamlit and Plotly were not installable in the build environment, so the layout, widgets, charts, downloads and navigation have not been seen or clicked. Run the app on your machine and check each page before presenting.

See `DASHBOARD_QC_REPORT.md` for the full list.

## 9. Research caveats the dashboard shows on the relevant pages

- No player is statistically supported as pressure-specific.
- Batter pressure heterogeneity is not significant at 5% after controlling for general ability (p = 0.058). The joint model gives p = 0.063.
- Bowler pressure heterogeneity is not established. The correlation parameter sits at its boundary and is not interpretable.
- The Final Research Protocol was not supplied, so protocol compliance is unverified.
- The 207-match legal-ball anomaly is unresolved. Its cause is unknown, and it is not assumed to be under-recorded no-balls.
- The Bayesian component is a grid posterior, not full MCMC. No R-hat, effective sample size or divergence checks exist.
- All-overs pressure comparisons are confounded by phase. The dashboard therefore uses death overs only.

## 10. Images and licences

See `assets/ASSET_LICENSES.md`. The only image is the stadium drawn in code: no photograph, no external image URL, no team logo, and no claim of affiliation with any franchise.

## 11. Historical franchise, current affiliation and auction status

The Player & Franchise Explorer and the Auction Intelligence page keep three things apart, and each page labels them separately:

1. **Historical franchise.** The team a player is recorded with in an IPL season, from the supplied squad mapping. Checked independently against the raw playing-eleven records: 251 of the 258 player-season rows have a playing-eleven record for the same franchise. The other 7 are squad-only records with no playing appearance. 5 further rows are listed in a playing eleven but marked not played (is_played = False), so their matches played is 0. The earlier figure of 1,012 pairs could not be reproduced and has been withdrawn.
2. **Current affiliation.** Shown only from a row in `data/manual/current_affiliation_verified.csv`.
3. **IPL 2027 auction status.** Shown only from a row in `data/manual/ipl2027_status_verified.csv`. Allowed values: Retained, Released, Traded, Auction-listed.

The last historical team is never treated as the current team, and no auction availability is inferred from history. With no accepted row, both fields read **Not verified**. This build has no accepted rows, because no official, dated IPL 2027 list was retrieved.

**Adding a verified entry.** Add one row per player to the relevant file. A row is rejected, and the page does not use it, unless:

- `pid` is the player's number from the evaluation file;
- `source_url` starts with `https://` and points to the official source (for example the IPL or franchise announcement);
- `as_of` is a date in `YYYY-MM-DD` form, the date the source was published or checked;
- for status, `status` is one of the four allowed values; for affiliation, `franchise` is one of the ten IPL franchises in the data.

If two rows exist for one player, the one with the later `as_of` is shown. Keep the source's title in `source_title`.

**Data gaps are shown, not hidden.** Two evaluated people have no IPL 2022-2026 record: Shaheen Afridi and Haris Rauf. Some players have seasons with no squad record (for example Jason Holder in 2024 and 2025). The page says "no squad record in the supplied data" for those seasons. That describes the data, not the player's career.

**Dual-role players.** Andre Russell, Jason Holder, Mitchell Santner, Rashid Khan and Maheesh Theekshana are evaluated both as batter and as bowler. The franchise history is keyed by person, so each appears once, with both sets of figures.

**Evaluation count.** The research evaluation file holds 66 role-evaluations for 61 people. The Executive Dashboard shows both numbers. The research counts are unchanged.

**Season performance.** Batting and bowling figures per season come from the raw ball-by-ball file with the research definitions. A season with fewer than 30 balls faced, or fewer than 18 legal balls bowled, is flagged as a small sample.

**Rebuilding the franchise and visual data.** Only needed if the raw data pack changes:

```powershell
python tools\build_franchise_history.py "C:\path\to\Data Pack"
python tools\build_visual_aggregates.py "C:\path\to\Data Pack\ball_by_ball.csv"
python tests\build_manifest.py
```

The franchise script stops if the squad mapping and the playing-eleven records disagree for any player-season. The visual script uses the research definitions (balls faced exclude wides; boundaries are fours and sixes).

**What the dashboard does not show.** The ball-by-ball file holds no shot direction, shot coordinates, bowling coordinates, line or length. Wagon wheels and line-and-length charts are therefore not drawn. Shot and delivery views show recorded labels only.
