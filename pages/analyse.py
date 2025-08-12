import fitz
import easyocr
from pdf2image import convert_from_bytes
import streamlit as st


reader = easyocr.Reader(['fr'], gpu=False) 

def extract_text(pdf_file):
 
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    doc.close()


    if len(full_text.strip()) < 50:
        pdf_file.seek(0) 
        images = convert_from_bytes(pdf_file.read())
        full_text = ""
        for img in images:
            result = reader.readtext(img, detail=0)
            full_text += "\n".join(result) + "\n"

    return full_text


def render():
    st.header("Page Analyse")
    st.write("Envoyez un contrat PDF à analyser.")

    uploaded_pdf = st.file_uploader("Choisissez un PDF", type=["pdf"])
    if uploaded_pdf is not None:
        text = extract_text(uploaded_pdf)
        st.subheader("📜 Contenu extrait du PDF")
        st.text_area("Texte brut", text, height=300)
