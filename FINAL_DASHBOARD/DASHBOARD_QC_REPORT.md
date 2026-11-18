# Dashboard QC report: SupeRR Selector Season 2

> **Note:** sections 1 to 9 describe earlier builds. Pages 1 to 11, the Live Match Centre and the cricket visuals they mention were removed in the five-page redesign in section 10, which is the current state.

**Scope:** `FINAL_DASHBOARD/` only. The research outputs, the final report, the sensitivity and simulation results, and the decision note were not modified. This visual upgrade adds three derived files (section 8) and does not change any research value. The two inconsistencies found in them are documented in section 5 and left as delivered.

**Build environment:** Linux, Python 3.13, with pandas and numpy available. **Streamlit and Plotly were not installed and could not be installed, because there was no network access.** The app has **not been launched**, and no browser test was run. Nothing in this report claims a launch.

---

## 1. Tests performed and results

| # | Test | What it checks | Result |
|---|------|----------------|--------|
| T1 | `test_every_python_file_compiles` | All 25 Python files compile | Pass |
| T2 | `test_all_required_files_present` | All 30 files listed in `utils/loaders.py` exist in `data/` | Pass |
| T3 | `test_missing_root_returns_none_without_error` | Empty data folder gives `None` from every loader, no exception | Pass |
| T4 | `test_real_outputs_load_and_have_expected_shape` | 66 evaluated players; second-innings table has 66,162 states | Pass |
| T5 | `test_counts_reconcile_with_report` | 8,467 pressure deliveries; 386 matches; 25 batters; 41 bowlers; 883 matches in dataset; 615 retained | Pass |
| T6 | `test_anomaly_counts_match_report_and_are_disjoint` | Legal-ball anomaly: 207 flagged = 201 in anomaly category + 6 classed earlier (3 DLS/D-L, 3 shortened); 147 by innings over 120, 60 by over rule only | Pass |
| T7 | `test_reconciliation_has_no_unexpected_failures` | 29 checks: 27 pass, 2 are the known, documented flags, 0 unexpected failures | Pass |
| T8 | `test_gate_supported_only_when_role_test_and_probability_both_pass` | Status gate, including boundaries: supported needs role p < 0.05 **and** P >= 0.95 | Pass |
| T9 | `test_real_players_are_never_labelled_supported_while_role_test_fails` | 0 players labelled supported; Rinku Singh and Rashid Khan labelled "Provisional: P >= 0.95, role test not significant" | Pass |
| T10 | `test_labels_are_consistent` | Every label has a display colour; only one label starts with "Statistically supported" | Pass |
| T11 | `test_findings_use_only_defined_labels_and_bowler_list_is_not_ranking` | Batter list = Provisional shortlist; bowler list = Not identifiable | Pass |
| T12 | `test_findings_handle_missing_inputs` | No inputs gives one "Insufficient evidence" row, not an exception | Pass |
| T13 | `test_shortlists_have_ten_rows_and_source_flags_as_delivered` | 10 batters and 10 bowlers; every batter has an evaluation row | Pass |
| T14 | `test_filters_subset_and_empty_means_no_filter` | Filters subset correctly; empty list means no filter | Pass |
| T15 | `test_pressure_summary_reconciles_to_total` | Pressure counts sum to 8,467 across leagues | Pass |
| T16 | `test_overlap_at_k` | Top-k overlap function on known inputs | Pass |
| T17 | `test_helpers_read_saved_values` | Saved values read correctly: simulation detection 0.817 at tau 0.20; rolling fold size 9 to 12; joint p 0.063; ability p 0.058 | Pass |
| T18 | `test_as_delivered_downloads_match_manifest_and_project_source_when_present` | Shortlist and evaluation files match their checksums; byte-identical to project source where the project is present | Pass |
| T19 | `test_filtered_download_has_only_selected_rows_and_unrounded_values` | Filtered CSV has the right rows and unrounded values | Pass |
| T20 | `test_manifest_matches_every_file` | 32 files; every SHA-256 matches `data/MANIFEST.csv`; no unlisted files | Pass |
| T21 | `test_no_absolute_paths_or_old_project_references_in_code` | No `/home/`, `C:\`, `/mnt/`, `SUPERR_ROOT` or old `outputs/` paths in code | Pass |
| T22 | `test_requirements_have_no_unused_packages` | Each requirement is imported somewhere | Pass |
| S1 | `test_eight_pages_with_required_titles` | Eight pages with the required titles, in `app.py` | Pass |
| S2 | `test_every_page_runs_with_real_data_and_none_stop` | Each page's code runs with the real data; none stops early | Pass |
| S3 | `test_app_entry_builds_navigation_with_eight_pages` | `app.py` builds navigation with eight pages | Pass |
| S4 | `test_filters_change_the_displayed_numbers` | Competition = IPL changes the selected-states metric to the independently computed IPL count; minimum 100 pressure deliveries reduces the batter table to the independently computed count | Pass |
| S5 | `test_missing_data_folder_gives_messages_not_exceptions` | With an empty data folder, every page shows a message or stops cleanly; none crash | Pass |

**Other checks run:**

- **Relocation:** the folder copied to an unrelated directory and both test suites were run there. 22 of 22 and 5 of 5 pass.
- **Missing-message audit:** with the real data, no page shows a "not in the data folder" message.
- **Stub sensitivity check:** the Plotly stand-in was given a deliberately wrong column name. It raised an error, so the column checks in S2 and S4 are not vacuous.
- **Prose audit:** the text each page displays was captured and checked against the saved files. Every number in it now comes from a file, or from a constant that is itself checked by the tests.

**Commands run:** `python tests/test_logic.py` (22 passed) and `python tests/test_pages_smoke.py` (5 passed), both from the folder.

## 2. What the smoke tests do and do not prove

The smoke tests replace Streamlit and Plotly with stand-ins (`tests/stub_streamlit.py`). They run each page's Python against the real data, and they check that every column a page or chart names exists.

They **prove:** the page code runs; column names match the data; filters change the displayed numbers as they should; missing files give messages, not crashes.

They **do not prove:** that the app starts, that the layout is right, that widgets behave in a browser, that charts render with the intended styling, that download buttons deliver files when clicked, that the navigation sidebar works, or that the Streamlit API calls used are correct for the version you install. Those need the launch test in section 4.

## 3. Issues found and fixed

**Portability and structure**

1. **The folder could not be moved alone.** Data was read from the project root (`outputs/`, `data/`). **Fixed:** the 30 needed research files are copied into `data/`, with checksums in `MANIFEST.csv`. All paths are relative to the folder. Verified by T20 and the relocation check.
2. **Old README gave wrong instructions** (`cd dashboard`, `SUPERR_ROOT`, a `requirements.txt` path that no longer exists). **Fixed:** README rewritten for Windows and VS Code.
3. **Dependencies:** `scipy` was listed but never imported. **Fixed:** removed. Versions now have ranges (`streamlit>=1.36,<2`, and so on), with a comment that they were not tested on Windows.
4. **Pages did not match the required eight.** Titles and content differed. **Fixed:** the eight pages now carry the required titles, in order, through `st.navigation`.
5. **Large raw table shipped unnecessarily.** The 5 MB ball-by-ball table was read only for counts. **Fixed:** removed. Counts come from the frozen Phase 0 and Phase 1 outputs.

**Research integrity: wrong or unsupported statements on the pages**

6. **"Most players have fewer than 60 pressure deliveries"** was contradicted by the data (every evaluated player passes the 60 threshold). **Fixed:** replaced with the IPL exposure count from the frozen table (16 batters, 17 bowlers reach 60).
7. **"9 to 35 players per fold"** on the validation page. The saved table gives 9 to 26 bowlers and 9 to 12 batters. **Fixed:** computed from the table.
8. **Closeness was described as 1 minus the distance from 0.5.** The saved values are `|WP − 0.5|`, the distance itself. **Fixed:** the text and chart title now match the saved values. This error was only in the dashboard; the research documents do not state the formula.
9. **The anomaly was described as "innings over 120 legal deliveries".** The flag also includes matches with an over of more than 6 legal deliveries: 147 matches by the innings rule, 60 by the over rule alone. **Fixed:** the page states both rules, with counts computed from the data.
10. **"Six matches overlap DLS and shortened rules"** was imprecise. The six are anomaly-flagged matches classed under an earlier category (3 DLS/D-L, 3 shortened records). **Fixed:** reworded with the computed breakdown.
11. **Model A–D page used the leaky table** (`MODEL_ABCD_ROLLING_ORIGIN.csv`, which uses later seasons for baselines). **Fixed:** the leakage-free file is used, and the leaky version is not shipped.
12. **Three outputs carry baseline leakage** (phase-7 rolling table, concentration test, opposition covariate), per the research report. They were shown without a warning. **Fixed:** each now has a "Provisional: baseline leakage" warning. The Model A–D caption also states that the wicket cost is still derived from all seasons.
13. **Unverified reason given for eligibility.** The opposition page said eligibility falls because 2022 has no prior season. Nothing in the files confirms that. **Fixed:** the reason is removed; only the counts remain (17 batters, 22 bowlers).
14. **"Skew about 0.5" for residuals** appeared as a fact, but no saved output contains it. The review script prints it without saving it. **Fixed:** removed, with a note that it is not saved.
15. **Invented threshold:** "A variant with fewer than about 30 eligible players is not reliable". It is not in the research. **Fixed:** removed.
16. **Hard-coded statistics** across pages (p-values, SDs, sampling errors, detection rates, posterior ranges, eligibility counts). **Fixed:** all now read from the saved files. A search of the final code found no typed statistics left, apart from labelled constants such as the 0.05 and 0.95 thresholds, which the research defines.
17. **Batter shortlist's source flag.** `top10_batters.csv` marks `identifiable_ranking = True` on every row. The page showed the file without comment, which reads as a supported ranking. **Fixed:** the page labels the shortlist "Provisional shortlist", and states the flag and why it is not statistical support. The source file is unchanged.
18. **Bowler top-10 rank column** reflects the raw pressure order, which is not a posterior order. Displaying it would suggest an ordering the data does not support. **Fixed:** the rank column is not displayed; the file is available unchanged as a download.

**Status labels and downloads**

19. **Inconsistent status wording** ("not detected", "not a ranking", "provisional: not statistically supported", and others). **Fixed:** one fixed vocabulary in `utils/labels.py`, each label with a fixed colour, enforced by T10 and T11.
20. **Downloads contained rounded values.** The display rounding was also applied to the download. **Fixed:** the table display is rounded; the download is unrounded. Files marked "as delivered" are byte-identical copies.
21. **No single place for page configuration.** Each page relied on the same entry file for setup. **Fixed:** the configuration is set once in `app.py`, before `st.navigation`, and the pages carry no setup code of their own.

**Defects found by the new tests**

22. **Reconciliation crashed on missing inputs.** With no data, the check table had no columns, so the Final Decision page failed. Found by S5. **Fixed:** columns are always defined.
23. **Findings listed the shortlist even when its files were absent.** Found by T12. **Fixed:** rows appear only when their inputs are present.

## 4. Tests not possible in this environment

These are the checks that must be done on your machine before the dashboard is presented:

- **Launch:** run `streamlit run app.py` and confirm it starts without error. **Not done.**
- **Navigation:** all eight pages reachable from the sidebar, in order, with the right titles. **Not done.**
- **Layout and visual quality:** each page rendered, columns and spacing checked, nothing overcrowded. **Not done.**
- **Widgets:** every filter (multiselect, slider, radio) changes the page when moved in a browser. The stand-in test checks the logic, not the widget. **Not done.**
- **Charts:** every Plotly chart renders with the expected axes, legend and hover text. Plotly was stubbed, so the figures themselves were never built. **Not done.**
- **Downloads:** each download button produces a file with the expected contents when clicked. **Not done.**
- **API compatibility:** the Streamlit calls used (`st.navigation`, `st.Page`, `st.dataframe(hide_index=...)`, `st.plotly_chart(width=...)` with a fallback, `st.download_button`, `st.latex`, `st.metric(help=...)`) were written against Streamlit 1.36 and later from documentation knowledge. They were not checked against a live install. **Not done.**
- **Windows:** the setup steps, PowerShell activation, path handling and CSV encoding on Windows. **Not done.**
- **Python versions:** tested on Python 3.13 only. **Not done** on 3.10 to 3.12.
- **Fresh install:** `pip install -r requirements.txt` in a clean environment. **Not done**: network access was off.
- **Clean-environment README walkthrough**: followed from scratch on a second machine. **Not done.**
- **Accessibility:** colour contrast of the status colours and keyboard navigation. **Not done.**

## 5. Research inconsistencies found (documented, not edited)

The brief asks that research files be changed only after a genuine inconsistency is documented separately. Both items below are shown on the Final Decision page as known inconsistencies.

**A. Bowler raw heterogeneity p-value in the decision note.** `FINAL_DECISION_NOTE.md` gives the bowler raw heterogeneity p-value as 0.36. The saved H2 output (`H2_profile_likelihood_tau.csv`) gives 0.3545, which rounds to 0.35 at two decimals. The conclusion is unaffected: the bowler effect is not significant either way. Recommended correction: change the note to 0.35, or quote three decimals (0.355). Not changed here.

**B. Batter shortlist flag.** `top10_batters.csv` has `identifiable_ranking = True` on all 10 rows, with the note "posterior ordering supported by tau2 > 0". The research rules make the batter list a provisional shortlist, because the role-level test gives p = 0.063. The flag can be read as a supported ranking. Recommended correction: set the flag to `False`, or change the note to say the flag refers to the raw residual ordering only. Not changed here, because the file is a delivered decision file.

## 6. Remaining limitations

- **Baseline leakage** remains in the phase-7 rolling table, the concentration test, and the opposition covariate. The wicket cost is still derived from all seasons. The dashboard labels these as provisional; it does not correct them.
- **No full Bayesian fit.** The prior sensitivity is a grid posterior with other parameters profiled. No R-hat, effective sample size or divergence checks exist.
- **Legal-ball anomaly unresolved.** The cause is unknown, and the dashboard does not assume under-recorded no-balls.
- **Final Research Protocol not supplied.** Protocol compliance is unverified.
- **Variants not run:** the A3 anomaly-exclusion variant, team-season random effects, and alternative reference pressure distributions.
- **Small samples.** Most individual estimates carry wide intervals; the bowler effect is not identifiable at this exposure.
- **Model not re-estimated.** The dashboard reads saved outputs. Changing a data file does not re-run a model.
- **Superseded folder.** The project root still contains an older `dashboard/` folder. It is outside `FINAL_DASHBOARD/`, so it was left in place. It should be deleted or archived to avoid confusion.
- **Layout not seen.** The visual design (colours, spacing, responsive behaviour) was specified in `assets/style.css` and `.streamlit/config.toml`, and has not been viewed in a browser. Only the hero SVG was rasterised and inspected (section 8).
- **Live Match Centre has no provider.** The page is inactive. Nothing about a live feed has been tested against a real service.

## 7. Contents

- 32 Python files including tests, the build tool and the two new pages; 34 files under `data/` (including the manifest); 3 assets (CSS, PDF, licence notes).
- `data/MANIFEST.csv` lists 36 files with SHA-256 checksums. Regenerate with `python tests/build_manifest.py` after replacing any file.
- Total folder size on disk: about 5.3 MB, excluding `__pycache__`.

## 8. Visual upgrade (this build)

### What changed

- **Hero.** An original SVG stadium under floodlights, with the title "IPL 2027 Auction Intelligence", on the Executive Overview page. Drawn in code: no photograph, no external URL, no franchise logo.
- **Cricket Visuals (page 9).** Batting comparison, shot mix heatmap, bowling delivery-style mix, pressure by phase and season, and player cards with initials.
- **Live Match Centre (page 10).** Inactive by default. Provider adapter (`utils/live.py`), failure states, run-rate arithmetic, and a manual calculator.
- **Styling.** Navy, gold and a subtle red accent; short hover transitions on tabs and cards only. Theme primary colour changed to navy.
- **Data.** `tools/build_visual_aggregates.py` builds three CSVs from the raw `ball_by_ball.csv`: a batter summary, a batter shot mix, and a bowler delivery mix. Definitions match the research pipeline (balls faced exclude wides).

### Visuals that use real data, and those that are decorative

| Visual | Data-driven or decorative |
|---|---|
| Batting comparison, shot mix, delivery-style mix | Data-driven (recorded labels from the raw file) |
| Pressure by phase and season | Data-driven, descriptive; the phase split follows the strict definition |
| Player cards | Data-driven (research file); initials, no photographs |
| Stadium hero, ground schematic | Decorative, no data |

### Not built, because the data does not support them

- **Wagon wheel.** The raw file has no shot direction or coordinates. The `stroke` field is a shot type (for example Cover Drive), not a direction.
- **Line-and-length heatmap.** The raw file has no length or line measurement. `delivery_style` (for example Yorker, Off Break) is a label, not a location.

### Checks run

| Check | Result |
|---|---|
| `tests/test_logic.py` | 22 of 22 pass |
| `tests/test_visuals_live.py` (run-rate arithmetic, provider failure states, aggregate consistency) | 12 of 12 pass |
| Same tests with `SUPERR_RAW_BALL` set (batter runs and balls recounted from the raw file) | Pass, including the recount |
| `tests/test_pages_smoke.py` (all 10 pages run with real data; missing data gives messages) | 5 of 5 pass |
| Hero SVG parsed as XML and rasterised to PNG, then inspected | Pass: floodlights, stands and pitch render |
| Research values unchanged | Compared with the manifest in the previously delivered ZIP: 31 of 32 earlier files are byte-identical. The one changed file is `assets/style.css` (styling only). Four files were added: the three visual CSVs and `ASSET_LICENSES.md`. |

### Issues found and fixed in this stage

- The test stub returned an empty object for `st.tabs`, `st.selectbox` and `go.Heatmap`, so the new pages could not run under the stubs. The stub now provides those, returning the first option as a user starts.
- The first hero drawing left the stands almost invisible against the sky. The stands were redrawn as lit tiers and re-rendered.
- Two lines in the Cricket Visuals page were corrected before the first run: a conditional expression used as a statement, and a provisional status label used for a descriptive caveat. An unused import was removed.
- A pressure-by-phase chart would have implied a finding. The strict rule gives 0% in the powerplay and middle overs and 67.6% in the death overs. The page now says the split is definitional, and a test records that property.

### Not verified in this build

- **Streamlit was not installed and could not be installed (no network).** The app has **not been launched**. The layout, transitions, tabs, cards, heatmap and the live-refresh fragment have not been seen in a browser.
- **Streamlit 1.37 or later** is required for the timed refresh on the Live Match Centre (`st.fragment(run_every=...)`). The requirement was raised to `>=1.37`. This is not yet tested against that version. On an older version the page still runs without the timed refresh.
- **Plotly graph-object charts are not column-checked** by the smoke test. Only `plotly.express` calls are. Their columns come from the same frames the tests build, and the aggregate tests check their values.
- **No live provider has been connected.** The live logic is tested with mock payloads only. Those tests check arithmetic and failure handling. They are not evidence of any live match.
- **Shot and delivery labels** are the recorded categories as provided. They have not been validated against video or scorecards.


## 9. Franchise History (this build)

### What was built

- **Season-level history.** `tools/build_franchise_history.py` builds `data/processed/franchise_history_seasons.csv` (258 person-season rows, 2022-2026) and `franchise_history_players.csv` (61 people) from the raw data pack.
- **Page 11, Franchise History.** Franchise filter, role filter, research top-10 filter, a table with franchise paths and status fields, a chart of players per franchise, and a player profile. The profile shows season performance, a median benchmark for the same season, and an optional comparison with another evaluated player of the same kind.
- **Verification layer.** `utils/franchise.py` and two manual files, `data/manual/ipl2027_status_verified.csv` and `data/manual/current_affiliation_verified.csv`. Both are empty. Rows are accepted only with an allowed value, an https source, and a valid date.

### Source checks

| Check | Result |
|---|---|
| Squad mapping versus playing-eleven records, all IPL 2022-2026 player-team-season pairs | CORRECTED: 251 of the 258 player-season rows have a playing-eleven record for the same franchise. The other 7 are squad-only records with no playing appearance. 5 further rows are listed in a playing eleven but marked not played (is_played = False), so their matches played is 0. The earlier figure of 1,012 pairs could not be reproduced and has been withdrawn. Original text: no player is mapped to two franchises in one season (the build stops otherwise) |
| Research IDs found in the IPL squad mapping | 59 of 61 people; Shaheen Afridi and Haris Rauf have no IPL 2022-2026 record and are shown as such |
| Independent recount of Ravindra Jadeja from the raw file (runs, balls faced, dismissals, legal balls bowled, all IPL matches) | Exact match on all four |
| Duplicate person-season rows | None (test) |

### Official status search

Two web searches were run on 18 November 2026. They returned predictions of retentions and releases, reports that the retention deadline was 17 November, and lists for the 2026 cycle. No finalised, official IPL 2027 retention or release list was found, and the search results contain no dated official list for any player. So **no player's IPL 2027 status or current affiliation has been verified**. Press reports of trades were not used, because they are not official.

### Issues found and fixed during this build

- **Five people evaluated twice.** The evaluation file has 66 role-evaluations for 61 people (Russell, Holder, Santner, Rashid Khan, Theekshana each appear as batter and as bowler). The first version of the history therefore duplicated person-season rows. The history is now keyed by person, with an `evaluated_as` column. The research counts are unchanged.
- **Players with no record vanished from the table.** With no franchise filter, the table was built from season rows, so Shaheen Afridi and Haris Rauf were missing. The page now starts from the full player list when no franchise is selected. Found by running the profile page for those two players.
- **Stub default.** The test stub returned all options for a multiselect with no default, which made the franchise filter exclude no-record players during testing. The page now passes `default=[]` explicitly, as Streamlit does; this matches real behaviour.

### Tests

| Suite | Result |
|---|---|
| `tests/test_franchise.py` (14 tests, with the raw recount) | 14 of 14 pass |
| `tests/test_logic.py` | 22 of 22 pass |
| `tests/test_visuals_live.py` | 12 of 12 pass |
| `tests/test_pages_smoke.py` (all 11 pages with real data; missing data gives messages) | 5 of 5 pass |
| Profile page run for Shaheen Afridi (no record), Jason Holder (season gaps), Rashid Khan (dual role) under the stubs | All complete |

### Count to decide on (not changed)

The Executive Overview headline reports "players evaluated" as batters plus bowlers, which is 66. Those are role-evaluations, and five people appear in both roles, so the count of distinct people is 61. The research numbers are unchanged. Whether the headline should read 61 people (66 role-evaluations) is a decision for the research owner.

### Not verified

- The page has not been viewed in a browser (Streamlit is not installable here).
- Current affiliation and IPL 2027 status are **Not verified** for every player. The verification files must be populated from official sources before either field can show a value.
- Season performance is descriptive only. It does not feed the research estimates or auction-value claims.

## 10. Five-page redesign (current build)

### What changed
- Navigation is now exactly five pages, in order: Executive Dashboard, Batter Scouting, Bowler Scouting, Player & Franchise Explorer, IPL 2027 Auction Intelligence.
- Removed as navigation pages: Data Coverage & Quality, Pressure Framework, Statistical Model & Validation, Sensitivity & Reliability, Separate Cricket Visuals, Live Match Centre. Their old page files and `utils/live.py` were deleted.
- Detailed methodology is in the downloadable research report and decision note (page 1).
- `utils/scouting.py` provides death-overs matching for every pressure-versus-normal comparison, the person table (61 people) and career totals. `utils/franchise.py` gained `load_verified` and `three_fields`, which show current affiliation and IPL 2027 status as "Not verified" unless an accepted, dated, sourced row exists.
- Research files, statistics, status logic, pressure definitions and shortlists are unchanged. The only data files added are the built visual and franchise tables from earlier sections.

### Death-overs comparison (a correction made during this build)
All-overs comparison of pressure and normal deliveries gives a strike rate of 151.3 under pressure against 134.2 normal. That gap is phase-confounded, because every pressure state falls in the death overs, which score faster. Comparing only death-over deliveries gives 151.3 under pressure against 152.1 normal. Dismissals are 9.5 against 6.2 per 100 legal balls. Economy is 9.08 against 9.12, and wickets are 9.08 against 6.00 per 100 balls. Every pressure comparison in the dashboard uses the death-overs figures and says so.

### Test results (run in this build)
| File | Result |
|---|---|
| `tests/test_logic.py` | 22 of 22 pass |
| `tests/test_franchise.py` | 14 of 14 pass (raw recount skipped: `SUPERR_RAW_DIR` not set) |
| `tests/test_visuals.py` | 4 of 4 pass (raw recount skipped: `SUPERR_RAW_BALL` not set) |
| `tests/test_scouting.py` | 5 of 5 pass (death-overs figures pinned to the verified values) |
| `tests/test_pages_smoke.py` | 5 of 5 pass: every one of the five pages runs with real data; the batter filter (minimum 100 pressure balls) keeps exactly the batters the helper counts; missing data gives messages, not crashes; navigation has five pages |

### Bugs found and fixed during testing
- The test stub returned placeholders for widgets created inside `st.columns` (sliders, select boxes, checkboxes). Those widgets now return the same defaults as the top-level functions. The pages were correct; the stub was wrong.
- The Explorer's transposed comparison table lost its metric names, because the table helper has no index option. Metric names are now a column.
- An Auction page placeholder line that referenced a non-existent frame was removed before the page ran.

### Not verified in this build
- **No browser run.** Streamlit and Plotly are not installed in the build environment, and no network is available to install them. The layout, widgets, charts, download buttons, navigation and filters have not been seen or clicked. The smoke tests run the page code with stand-ins; they prove the code runs, not that the app renders.
- **Chart appearance.** Chart styling, label placement and colours have not been seen.
- **2027 status and current affiliation.** No official, dated source was retrieved. Both fields show "Not verified" for everyone. No auction price, team need, retention or availability is shown anywhere.

### Open decisions for the research owner
- **66 or 61.** The research file holds 66 role-evaluations for 61 people (five dual-role players). The Executive Dashboard shows both numbers and the research counts are unchanged.
- **Statistical support.** No player is statistically supported as pressure-specific. The dashboard says so on every page where it matters.

## 11. Visual polish pass (current build)

### Changes (UI only)
- Status notices are now one subtle grey line each, not coloured banners. The sidebar methodology text was removed.
- Executive Dashboard: one research-status line at the top; key findings are plain statements, not a technical table; the "decorative illustration" line and repeated captions were removed.
- Scatter plots show player names on hover only, so names no longer overlap.
- Pressure distribution charts show the share of each group per bin, not counts on a log scale, so the small pressure group is readable.
- All charts share one height (380 px).
- Batter and bowler pages: a short summary table (about six columns) with the full statistics in an expandable section and download. The duplicate methodology captions were removed.
- Player & Franchise Explorer: text gaps show "No recorded data" instead of None; a missing franchise no longer appears as None.
- IPL 2027 Auction Intelligence: compact table (research status, pressure figures, current affiliation, auction status) with the full evidence in an expandable section.

### Research integrity
No statistics, rankings, shortlist order, pressure definitions, significance results or source files were changed. The 66 role-evaluations versus 61 people distinction is unchanged. No player is shown as statistically supported.

### Tests
Run in this build, after the polish: logic 22/22, franchise 14/14, visuals 4/4, scouting 5/5, page smoke 5/5 (all five pages run with real data).

### Not verified
- **No browser run.** Streamlit and Plotly are not installed here, so the layout, the hover labels, the percent histograms, the expanders and the downloads have not been seen or clicked.
- **Long franchise names may still wrap or truncate** in narrow table columns. The table helper does not set column widths, because the width option differs between Streamlit versions and cannot be checked here.
- The unused `scatter_ci` chart builder remains in `components/charts.py`. It is not called by any page.

## 12. Scouting presentation correction and provenance follow-up (current build)

### What changed
- **Batter Scouting:** "Research Batter Shortlist — Provisional" is first, in the original rank order from top10_batters.csv, with research model estimates only. Below it, "Batter Performance Comparison" lists all 25 batters with raw death-over statistics, ordered by pressure-ball sample size, with a neutral caption.
- **Bowler Scouting:** "Exploratory Bowler Selection — Not a Ranking" is first, in the original file order from top10_bowlers.csv. Below it, "Bowler Performance Comparison" lists all 41 bowlers, with a caption that pressure-ball counts show sample size, not quality.
- **Metric labels:** research model estimates say "Research model"; newly calculated statistics say "Raw death-over" or "Raw IPL". The Executive and Auction pages use the same labels.
- **Executive Dashboard:** the bowler selection is in original file order, not alphabetical.
- **Franchise Explorer:** season rows that have no playing appearance show "Squad record; no playing appearance" when no playing-eleven row exists, and "Listed in playing eleven; not played" when a row exists with is_played = False.
- **Derived file:** `franchise_history_seasons.csv` gained one column, `listed_in_playing_eleven`. It was rebuilt from the raw data pack. Every existing numeric column was checked cell by cell against the previous file and is unchanged. The derived players file is byte-identical.

### Not changed
Original research files, the shortlist files, the evaluation file, the second-innings file, player statistics, shortlist ordering and statistical conclusions. No player is statistically supported as pressure-specific.

### Corrected claim
The earlier statement that 1,012 of 1,012 player-team-season pairs agree with the playing-eleven records could not be reproduced. The verified figures are in section 9 of this report and in the README (section 11).
