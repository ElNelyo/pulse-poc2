import os
from openai import OpenAI
import json
from dotenv import load_dotenv
import json
import pandas as pd
load_dotenv()
api_key = os.environ.get("OPENAI_API_KEY")




def make_json_serializable(obj):
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def analyze_contract(report_data: dict, contract_text: str) -> str:
    """
    Appelle OpenAI pour analyser les données d'un contrat.
    report_data : dictionnaire contenant toutes les données extraites et matches DB.
    contract_text : texte complet du contrat PDF.
    Retourne un résumé texte des anomalies détectées.
    """
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    prompt = f"""
    Voici le texte complet du contrat :
    {contract_text}

    Voici les données extraites et les fichiers associés (DB) :
    {json.dumps(report_data, ensure_ascii=False, indent=2, default=make_json_serializable)}

    Vérifie les points suivants :
    1. Vérification des prix (différences Vega vs DB, par mode de paiement, par emplacement)
    2. Conditions contractuelles (durée, dates, type de contrat)
    3. Informations clients & facturation (noms, adresses, holdings)
    4. Inventaire des distributeurs (modèles, localisation, association)

    Compare le contrat avec les données extraites et indique toutes incohérences ou points à vérifier.
    Fournis un résumé structuré.
    """

    response = client.responses.create(
        model="gpt-4.1",
        input=prompt
    )

    return response.output_text
