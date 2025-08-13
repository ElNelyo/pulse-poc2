# 🎈 Blank app template

A simple Streamlit app template for you to modify!

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://blank-app-template.streamlit.app/)

### How to run it on your own machine

1. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

2. Set your OpenAI API key (recommended: use a local `.env`)

   - Windows PowerShell
     ```
     $ setx OPENAI_API_KEY "sk-..."
     ```
   - Or create a `.env` file at the project root:
     ```
     OPENAI_API_KEY=sk-...
     ```

3. Run the app

   ```
   $ python3 -m streamlit run streamlit_app.py
   ```

Voici le brief rapide du projet:
https://pulsepartners-usecases.notion.site/?pvs=73


# Script 


```
A ce stade, on veut simplement, se baser sur un contrat / un client pour spotter des différences ou evolution entre ce qui est dans le contrat et dans les tables de données (formats xlsx).

Je dirais donc, sans trop aller au profondeur, juste faire une première comparaison efficace:

AI multimodal
Structuration
Analyse de différences

Sur une application streamlit hostée


# USE CASE

Multi-modal  -  Italian Accounting Software

## Objectif du projet

Mise en place un système automatisé pour contrôler la cohérence entre les contrats dans la base Vega et les données réelles (prix, conditions, modèles, adresses…), afin de réduire le temps manuel passé à vérifier et corriger les écarts.

1. Gagner du temps en supprimant les vérifications manuelles répétitives.
2. Identifier rapidement les différences entre Vega et la base réelle (prix, adresses, modèles, conditions).
3. Suivre l’évolution des contrats pour un même destinataire afin de détecter les changements par rapport à la version précédente.

---

## **Données & Sources**

### Tables clés dans **VEGA [sous excel]**

- **vega.clienti** → Clients (bureaux, adresses, distributeurs, facturation)
- **vega.contratti** → Contrats clients (OPA, OPP, OPK, dates, légales…)
- **vega.ctbcont** → Adresses de facturation
- **vega.modelli** → Modèles de distributeurs
- **vega.unopv** → Distributeurs individuels (point d’entrée de toutes les liaisons)

**Relations importantes :**

- `CNTR_SEDELEGALE` (contrats) ↔ `ctb_cod` (ctbcont)
- `UPV_COD` (unopv) ↔ modèles (`MOD_COD` / `MOD_DESCITA`)
- `cli_cod` (clienti) ↔ contrats


CLIENT cli_cod->CONTRAT.CNTR_SEDELEGALE
CONTRAT
CTBCONT CTBCONT.CTB_COD -> CLIENT.cli_cod
MODELLI CODE -> unopv.UPV_MOD
UNOPV upv_cli -> CONTRAT.CNTR_SEDELEGALE
---

## Points de contrôle à automatiser

1. **Vérification des prix**
    - Différences Vega vs DB (ex: 1.50 CHF vs 1.70 CHF pour Coca-Cola)
    - Prix selon mode de paiement (cash, badge, carte)
    - Différences par emplacement (ex: 1er étage payant, 2e étage gratuit)
2. **Conditions contractuelles**
    - Durée (60 mois, renouvellement auto 12 mois)
    - Date de début / fin / prochaine échéance
    - Type de contrat (OPA, OPP, OPK)
3. **Informations clients & facturation**
    - Nom et adresse client cohérents (CLI_NAME, CLI_IND)
    - Adresses légales et de facturation correctes
    - Holdings / filiales reliées au même contrat
4. **Inventaire des distributeurs**
    - Modèle & localisation corrects
    - Association au bon contrat et au bon prix

---

## Contexte opérationnel

- **Historique** : Vega est le logiciel comptable depuis 20 ans
- **Volume** :
    - Plusieurs milliers de contrats actifs
    - Quelques centaines renouvelés par an
- **Process actuel** :
    1. Saisie des infos dans Vega
    2. Scan PDF du contrat et archivage
    3. Vérifications manuelles → ~30 min/contrat
- **Problème** : Vérification coûteuse en temps et en charge cognitive
- **Vision** : Automatiser la comparaison Vega ↔ DB pour signaler uniquement les écarts
