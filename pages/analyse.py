import fitz
import easyocr
from pdf2image import convert_from_bytes
import streamlit as st
import re
import pandas as pd
import unicodedata
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
import os

api_key = os.environ.get("OPENAI_API_KEY")


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


def _looks_like_person(name_line: str) -> bool:
    tokens = [t for t in re.split(r"[\s\-]+", name_line.strip()) if t]
    if len(tokens) < 2 or len(tokens) > 4:
        return False
    # Heuristique simple: 2-3 mots qui commencent par une majuscule (ou majuscule accentuée)
    upper_initial = all(bool(re.match(r"^[A-ZÀ-ÝÄÖÜÈÉÊËÇÎÏÔÛŸ][a-zà-ÿ'\-]*$", t)) for t in tokens)
    # Éviter les suffixes d'entreprises
    company_suffix = any(suf in name_line for suf in [
        " SA", " AG", " GmbH", " Srl", " SRL", " SAS", " SPA", " Inc", " SARL", " SNC", " Ltd"
    ])
    return upper_initial and not company_suffix


def _looks_like_address(line: str) -> bool:
    line_l = line.lower()
    has_number = bool(re.search(r"\b\d+[a-z]?\b", line_l))
    street_markers = [
        "strasse", "straße", "str.", "str ", "via ", "rue ", "weg", "allee", "platz", "chemin", "avenue", "bd ", "boulevard"
    ]
    has_street_word = any(m in line_l for m in street_markers)
    return has_number and has_street_word


def _is_noise(line: str) -> bool:
    l = line.strip()
    if not l:
        return True
    if "@" in l or l.lower().startswith("tel") or l.lower().startswith("tél"):
        return True
    if re.search(r"\b(www\.|https?://)\S+", l):
        return True
    if re.fullmatch(r"[0-9\s\-\.]+", l):
        return True
    return False


def extract_header_text(text: str, max_words: int = 50) -> str:
    """Extrait les premiers mots du texte pour constituer l'en-tête"""
    words = text.split()
    header_words = words[:max_words]
    return " ".join(header_words)

def parse_client_info_with_openai(header_text: str) -> dict:
    """Utilise OpenAI pour extraire les informations du client depuis l'en-tête"""
    try:
        print(os.environ.get("OPENAI_API_KEY"))
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        prompt = f"""
        Analyse ce texte d'en-tête de contrat et extrait les informations du client au format JSON.
        
        Texte: {header_text}
        
        Retourne un JSON avec ces champs (null si non trouvé):
        {{
            "client_code": "code client (4-6 chiffres)",
            "client_name": "nom de l'entreprise/client",
            "contact_name": "nom du contact/personne",
            "address": "adresse complète",
            "zip": "code postal",
            "city": "ville",
            "country": "pays"
        }}
        
        Exemple pour "27106 Los Mensch + Arbeitswelt Gabriel Wüst Kasinostrasse 25 5001 Aarau 1 Schweiz":
        {{
            "client_code": "27106",
            "client_name": "Los Mensch + Arbeitswelt",
            "contact_name": "Gabriel Wüst",
            "address": "Kasinostrasse 25",
            "zip": "5001",
            "city": "Aarau 1",
            "country": "Schweiz"
        }}
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        st.error(f"Erreur OpenAI: {e}")
        return parse_client_info_fallback(header_text)

def parse_client_info_fallback(text: str) -> dict:
    """Méthode de fallback si OpenAI échoue"""
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]

    client_code = None
    client_name = None
    address_line = None
    zip_code = None
    city = None
    country = None
    contact_name = None

    for i, ln in enumerate(lines):
        if re.fullmatch(r"\d{4,6}", ln):
            client_code = ln
            j = i + 1
            while j < len(lines) and _is_noise(lines[j]):
                j += 1
            if j < len(lines):
                if not _looks_like_person(lines[j]):
                    client_name = lines[j]
                    k = j + 1
                    while k < len(lines) and not _looks_like_address(lines[k]):
                        if contact_name is None and _looks_like_person(lines[k]):
                            contact_name = lines[k]
                        k += 1
                    if k < len(lines) and _looks_like_address(lines[k]):
                        address_line = lines[k]
                        if k + 1 < len(lines):
                            m = re.match(r"^(\d{4})\s+(.+)$", lines[k + 1])
                            if m:
                                zip_code, city = m.group(1), m.group(2).strip()
                                if k + 2 < len(lines):
                                    if re.search(r"\b(Schweiz|Suisse|Svizzera|Switzerland|Italia|France|Deutschland|Österreich)\b", lines[k + 2], re.I):
                                        country = lines[k + 2]
                    break
            break

    if client_name is None:
        for i, ln in enumerate(lines):
            m = re.match(r"^(\d{4})\s+(.+)$", ln)
            if m:
                zip_code, city = m.group(1), m.group(2).strip()
                if i - 1 >= 0:
                    address_line = lines[i - 1]
                if i - 2 >= 0 and not _looks_like_person(lines[i - 2]) and not _is_noise(lines[i - 2]):
                    client_name = lines[i - 2]
                if i + 1 < len(lines):
                    if re.search(r"\b(Schweiz|Suisse|Svizzera|Switzerland|Italia|France|Deutschland|Österreich)\b", lines[i + 1], re.I):
                        country = lines[i + 1]
                break

    return {
        "client_code": client_code,
        "client_name": client_name,
        "contact_name": contact_name,
        "address": address_line,
        "zip": zip_code,
        "city": city,
        "country": country,
    }

def parse_client_info(text: str) -> dict:
    """Fonction principale qui utilise OpenAI avec fallback"""
    header_text = extract_header_text(text, max_words=50)
    return parse_client_info_with_openai(header_text)

def load_clienti(path: Path) -> pd.DataFrame:
        return pd.read_excel(path)

def render():
    account_path = Path("documents/table/ctbcont.xlsx")
    clienti_path = Path("documents/table/clienti.xlsx")
    contratti_path = Path("documents/table/contratti.xlsx")
    modelli_path = Path("documents/table/modelli.xlsx")
    unopv_path = Path("documents/table/unopv.xlsx")

    uploaded_pdf = st.file_uploader("Choisissez un PDF", type=["pdf"])
    if uploaded_pdf is not None:
        text = extract_text(uploaded_pdf)
        st.subheader("Extract content from contract")
        st.text_area("Contract Reading", text, height=300)
        
        # info = parse_client_info(text)  # <-- ligne commentée pour les tests
        info = {
            "client_code": "27106",
            "client_name": "Los Mensch + Arbeitswelt",
            "contact_name": "Gabriel Wüst",
            "address": "Kasinostrasse 25",
            "zip": "5001",
            "city": "Aarau 1",
            "country": "Schweiz"
        }
        st.subheader("Extract Customer ID")
        st.write(f"Customer detected : {info.get('client_name') or 'No detected'}") 
        with st.expander("Détails"):
            st.json(info)

        # Recherche dans clienti.xlsx
        st.subheader("Search in clienti.xlsx")
        if not clienti_path.exists():
            st.warning("Le fichier `documents/table/clienti.xlsx` est introuvable.")
            return

        

        def normalize(text_value: str) -> str:
             if not isinstance(text_value, str):
                text_value = str(text_value)
             text_value = text_value.replace("&", " ").replace("+", " ")
             text_value = unicodedata.normalize("NFKD", text_value).encode("ascii", "ignore").decode("ascii")
             text_value = re.sub(r"[^a-z0-9\+\&\-\s]", " ", text_value.lower())
             text_value = re.sub(r"\s+", " ", text_value).strip()
             return text_value

        df_clienti = load_clienti(clienti_path)

        name_cols = [col for col in ["CLI_NOME", "CLI_NOME2"] if col in df_clienti.columns]
        if not name_cols:
            st.error("Aucune colonne CLI_NOME ou CLI_NOME2 trouvée dans clienti.xlsx.")
            return

        client_name = info.get("client_name")
        if not client_name:
            st.warning("Customer not find.")
            return

        client_name_norm = normalize(client_name)
        mask = pd.Series(False, index=df_clienti.index)
        for col in name_cols:
            col_norm = df_clienti[col].astype(str).apply(normalize)
            mask = mask | (col_norm == client_name_norm)
            

        result_rows = df_clienti[mask]

        if result_rows.empty:
            st.warning(f"Aucun client trouvé avec le nom exact : {client_name_norm}")
        else:
            st.success(f"{len(result_rows)} customer found with name : {client_name_norm}")
            st.dataframe(result_rows)
            cli_cod = result_rows.iloc[0]["CLI_COD"]

           
            if not account_path.exists():
                st.warning("Le fichier `ctbcont.xlsx` est introuvable.")
                return
            st.subheader("Search in ctbcont.xlsx")
            df_ctbcont = pd.read_excel(account_path)

            accounts_customer = df_ctbcont[df_ctbcont["CTB_COD"] == cli_cod]

            if accounts_customer.empty:
                st.warning(f"no account found for customer {client_name_norm} ({cli_cod})")
            else:
                 st.success(f"account found for customer {client_name_norm} ({cli_cod})")
                 st.dataframe(accounts_customer)
                 
                 if not contratti_path.exists():
                    st.warning("Le fichier `contratti.xlsx` est introuvable.")
                    return

                 st.subheader("Search in contratti.xlsx")
                 df_contratti = pd.read_excel(contratti_path)

                 contrats_match = df_contratti[df_contratti["CNTR_SEDELEGALE"].isin(accounts_customer["CTB_COD"])]

                 if contrats_match.empty:
                     st.warning(f"no contract found for customer {client_name_norm} ({cli_cod})")
                 else:
                     st.success(f"{len(contrats_match)} contract(s) found for accounts of customer {cli_cod}")
                     st.dataframe(contrats_match)
                     
                     # Recherche dans unopv.xlsx pour les modèles
                     st.subheader("Search in unopv.xlsx")
                     if not unopv_path.exists():
                         st.warning("Le fichier `unopv.xlsx` est introuvable.")
                         return
                     
                     df_unopv = pd.read_excel(unopv_path)
                     unopv_match = df_unopv[df_unopv["UPV_CLI"] == cli_cod]
                     
                     if unopv_match.empty:
                         st.warning(f"no unopv found for customer {client_name_norm} ({cli_cod})")
                     else:
                         st.success(f"{len(unopv_match)} unopv(s) found for customer {cli_cod}")
                         st.dataframe(unopv_match)
                         
                         # Recherche dans modelli.xlsx pour les détails des modèles
                         st.subheader("Search in modelli.xlsx")
                         if not modelli_path.exists():
                             st.warning("Le fichier `modelli.xlsx` est introuvable.")
                             return
                         
                         df_modelli = pd.read_excel(modelli_path)
                         
                         # Vérifier la présence des colonnes nécessaires
                         if "UPV_MOD" not in unopv_match.columns:
                             st.warning("Colonne UPV_MOD absente dans unopv.xlsx")
                         elif "MOD_COD" not in df_modelli.columns:
                             st.warning("Colonne MOD_COD absente dans modelli.xlsx")
                         else:
                             # Convertir les valeurs en numériques de manière robuste
                             upv_mod_codes = pd.to_numeric(unopv_match["UPV_MOD"], errors="coerce").dropna().astype(int).unique()
                             if upv_mod_codes.size == 0:
                                 st.warning("Aucun code modèle valide dans UPV_MOD pour ce client")
                             else:
                                 df_modelli = df_modelli.copy()
                                 df_modelli["MOD_COD_NUM"] = pd.to_numeric(df_modelli["MOD_COD"], errors="coerce").astype("Int64")
                                 modelli_match = df_modelli[df_modelli["MOD_COD_NUM"].isin(upv_mod_codes)]
 
                                 if modelli_match.empty:
                                     if upv_mod_codes.size == 1:
                                         st.warning(f"no models found for MOD_COD of {int(upv_mod_codes[0])} customer {cli_cod}")
                                     else:
                                         st.warning(f"no models found for MOD_COD among {list(map(int, upv_mod_codes))} customer {cli_cod}")
                                 else:
                                     if upv_mod_codes.size == 1:
                                         st.success(f"{len(modelli_match)} model(s) {int(upv_mod_codes[0])} found for customer {cli_cod}")
                                     else:
                                         st.success(f"{len(modelli_match)} model(s) found for codes {list(map(int, upv_mod_codes))} for customer {cli_cod}")
                                     st.dataframe(modelli_match)
 