"""Shared Streamlit building blocks, so every page has the same layout, status colours, tables and downloads.

Tables show values rounded for reading. Downloads always carry the unrounded values, so a download equals the source."""
import html

import pandas as pd
import streamlit as st

from utils.labels import KIND
from utils.paths import ASSETS

_MSG = {"success": st.success, "warning": st.warning, "error": st.error, "info": st.info}


def inject_css():
    css_path = ASSETS / "style.css"
    css = css_path.read_text(encoding="utf-8") if css_path.is_file() else ""
    from components.hero import CSS as HERO_CSS
    css = css + HERO_CSS
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def title_block(title, purpose):
    st.title(title)
    st.caption(purpose)


def status_box(label, text):
    """A subtle neutral status line: the label in bold, then the explanation. No coloured banner."""
    st.caption(f"**{label}.** {text}")


LEAKAGE = ("**Provisional: baseline leakage.** This output uses stratum baselines fitted on all seasons, including seasons "
           "after the ones it predicts. The research report (section 3) flags it. Read it as provisional.")


def leakage_note():
    st.warning(LEAKAGE)


def missing(name):
    st.warning(f"'{name}' is not in the data folder, so this section is empty. "
               "Copy the file into FINAL_DASHBOARD/data (see README, 'Replacing the research files').")


def have(df, name):
    if df is None or len(df) == 0:
        missing(name)
        return False
    return True


def plot(fig):
    try:
        st.plotly_chart(fig, width="stretch")
    except TypeError:  # Streamlit older than the width argument
        st.plotly_chart(fig, use_container_width=True)


def table(df, name=None, download_name=None, digits=3, key=None):
    """Display rounded to `digits`; the download button writes the unrounded frame."""
    shown = df.round(digits) if digits is not None else df.copy()
    for c in shown.columns:  # text gaps read as a label, never as None; numeric gaps stay blank, not zero
        if not pd.api.types.is_numeric_dtype(shown[c]):
            shown[c] = shown[c].where(shown[c].notna(), "No recorded data")
    st.dataframe(shown, hide_index=True)
    if download_name:
        st.download_button(f"Download {name or download_name}", df.to_csv(index=False).encode("utf-8"),
                           file_name=download_name, mime="text/csv", key=key or f"dl_{download_name}")


def file_download(path, label, file_name, mime, key=None):
    """Download a file exactly as stored (byte-identical to the source)."""
    if path is None or not path.is_file():
        missing(file_name)
        return
    st.download_button(label, path.read_bytes(), file_name=file_name, mime=mime, key=key or f"file_{file_name}")


def kpis(items):
    """items: list of (label, value, help). Renders one row of metrics."""
    cols = st.columns(len(items))
    for col, (label, value, help_text) in zip(cols, items):
        col.metric(label, value, help=help_text)


_STATUS_CLASS = {"success": "ok", "warning": "warn", "error": "bad", "info": "info"}


def player_cards(df, role_word):
    """Initials-based cards (no photographs). df needs name, initials, dashboard_status, P_deviation_from_population_gt0."""
    if df is None or len(df) == 0:
        return
    cards = []
    for _, r in df.iterrows():
        kind = KIND.get(r["dashboard_status"], "info")
        cards.append(
            f'<div class="card"><div class="avatar">{html.escape(str(r["initials"]))}</div>'
            f'<div class="card-name">{html.escape(str(r["name"]))}</div>'
            f'<div class="card-role">{role_word}</div>'
            f'<span class="pill {_STATUS_CLASS.get(kind, "info")}">{html.escape(str(r["dashboard_status"]))}</span>'
            f'<div class="card-stats">P (deviation &gt; 0) = {float(r["P_deviation_from_population_gt0"]):.3f}</div>'
            f'</div>')
    st.markdown('<div class="card-grid">' + "".join(cards) + "</div>", unsafe_allow_html=True)
