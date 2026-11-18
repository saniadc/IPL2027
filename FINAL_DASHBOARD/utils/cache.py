"""Streamlit caching wrappers around the pure loaders (Streamlit is imported only here and in components/)."""
import streamlit as st

from utils import loaders


@st.cache_data(show_spinner="Loading research outputs...")
def outputs():
    return loaders.load_all()


@st.cache_data(show_spinner="Loading second-innings states...")
def second_innings():
    return loaders.load_second_innings()


@st.cache_data(show_spinner=False)
def file_status():
    return loaders.file_status()
