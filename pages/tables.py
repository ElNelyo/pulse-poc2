import streamlit as st
import pandas as pd
from pathlib import Path

DATA_DIR = Path("documents/table")

def render():
    st.subheader("Tables de référence Vega")
    
    files = [
        "clienti.xlsx",
        "contratti.xlsx",
        "ctbcont.xlsx",
        "modelli.xlsx",
        "unopv.xlsx"
    ]
    
    for file in files:
        path = DATA_DIR / file
        if path.exists():
            try:
                df = pd.read_excel(path)
                st.write(f"### {file}")
                st.dataframe(df.head(10))
            except Exception as e:
                st.error(f"Erreur lors du chargement de {file}: {e}")
        else:
            st.warning(f"Fichier non trouvé : {file}")
