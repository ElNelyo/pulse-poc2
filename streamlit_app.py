import streamlit as st
import importlib
import pages.analyse as analyse
import pages.tables as tables

importlib.reload(analyse)
importlib.reload(tables)

from pages import analyse, tables

st.set_page_config(page_title="Vega Data Viewer", page_icon="📊")
st.title("📊 Vega's Data exploration")

tab1, tab2 = st.tabs(["Analyse", "Tables"])

with tab1:
    analyse.render()

with tab2:
    tables.render()