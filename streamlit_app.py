import streamlit as st
from pages import analyse, tables

st.set_page_config(page_title="Vega Data Viewer", page_icon="📊")
st.title("📊 Vega's Data exploration")

tab1, tab2 = st.tabs(["Analyse", "Table Reference"])

with tab1:
    analyse.render()

with tab2:
    tables.render()