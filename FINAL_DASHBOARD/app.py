"""SupeRR Selector Season 2: pressure analytics dashboard.

Run from the FINAL_DASHBOARD folder:   streamlit run app.py
(or from any folder:                   streamlit run path/to/FINAL_DASHBOARD/app.py)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import streamlit as st  # noqa: E402

from components import ui  # noqa: E402

st.set_page_config(page_title="IPL 2027 Auction Intelligence | SupeRR Selector", page_icon="🏏",
                   layout="wide", initial_sidebar_state="expanded")
ui.inject_css()

PAGE_FILES = [
    ("1_Executive_Dashboard.py", "Executive Dashboard", True),
    ("2_Batter_Scouting.py", "Batter Scouting", False),
    ("3_Bowler_Scouting.py", "Bowler Scouting", False),
    ("4_Player_and_Franchise_Explorer.py", "Player & Franchise Explorer", False),
    ("5_IPL_2027_Auction_Intelligence.py", "IPL 2027 Auction Intelligence", False),
]
pages = [st.Page(str(HERE / "pages" / f), title=t, default=d) for f, t, d in PAGE_FILES]

st.navigation(pages).run()
