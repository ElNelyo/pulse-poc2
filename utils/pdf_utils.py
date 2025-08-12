import fitz
from pathlib import Path

def extract_text(uploaded_pdf):
    pdf_path = Path("temp_uploaded.pdf")
    with open(pdf_path, "wb") as f:
        f.write(uploaded_pdf.getbuffer())
    full_text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            full_text += page.get_text()
    return full_text
