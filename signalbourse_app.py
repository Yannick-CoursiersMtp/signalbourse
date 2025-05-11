import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import math

# Configuration de la page
st.set_page_config(page_title="SignalBourse", layout="centered")

# En-tête
st.title("📈 SignalBourse – Analyse rapide d'actions")
st.markdown(
    "Entrez un **ticker boursier** (ex : `AAPL`, `TSLA`, `SAN.PA`) pour recevoir "
    "un signal d'achat, vente ou attente basé sur les moyennes mobiles 20j/50j."
)

# Champ de saisie avec valeur par défaut
ticker = st.text_input("Nom de l'action / Ticker :", value="AAPL").upper().strip()

# Si l'utilisateur n'a rien saisi, on arrête ici
if not ticker:
    st.info("🔍 Veuillez entrer un ticker pour lancer l'analyse.")
    st.stop()

# Récupération des données
data = yf.download(ticker, period="6mo", interval="1d", progress=False)

if data.empty:
    st.error(f"❌ Aucune donnée trouvée pour « {ticker} ».")
else:
    # Calcul des moyennes mobiles
    data["MA20"] = data["Close"].rolling(window=20).mean()
    data["MA50"] = data["Close"].rolling(window=50).mean()

    # Affichage du graphique
    st.subheader("📊 Graphique de l'action")
    fig, ax = plt.subplots()
    ax.plot(data.index, data["Close"], label="Cours", linewidth=2)
    ax.plot(data.index, data["MA20"], label="MA20 (20j)", linestyle="--")
    ax.plot(data.index, data["MA50"], label="MA50 (50j)", linestyle=":")
    ax.legend()
    st.pyplot(fig)

    # Calcul du signal
    st.subheader("🚦 Signal automatique")
    # On récupère les dernières valeurs
    last_close = data["Close"].iloc[-1]
    ma20 = data["MA20"].iloc[-1]
    ma50 = data["MA50"].iloc[-1]

    # On ne compare que si on a vraiment 50+ jours et pas de NaN
    if len(data) >= 50 and not math.isnan(ma20) and not math.isnan(ma50):
        if last_close > ma20 and ma20 > ma50:
            st.success("✅ SIGNAL : Achat – tendance haussière confirmée.")
        elif last_close < ma20 and ma20 < ma50:
            st.error("❌ SIGNAL : Vente – tendance baissière confirmée.")
        else:
            st.warning("⚠️ SIGNAL : Attente – marché incertain.")

        st.markdown(f"**Dernier cours ({ticker})** : {last_close:.2f} USD")
    else:
        st.info("ℹ️ Signal non disponible (données insuffisantes ou trop récentes).")
