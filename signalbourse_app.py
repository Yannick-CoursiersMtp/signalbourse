import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# Configuration de la page
st.set_page_config(page_title="SignalBourse", layout="centered")

# Titre et description
st.title("📈 SignalBourse – Analyse rapide d'actions")
st.markdown(
    "Entrez un **ticker boursier** (ex : `AAPL`, `TSLA`, `SAN.PA`) pour recevoir "
    "un signal d'achat, vente ou attente basé sur les moyennes mobiles."
)

# Saisie du ticker
ticker = st.text_input("Nom de l'action / Ticker :", value="AAPL").upper().strip()

if ticker:
    # Récupérer 6 mois de données quotidiennes
    data = yf.download(ticker, period="6mo", interval="1d", progress=False)

    # Si aucune donnée
    if data.empty:
        st.error("❌ Aucune donnée trouvée pour ce ticker.")
    else:
        # Calcul des moyennes mobiles 20j et 50j
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

        # Vérifier qu'on a au moins 50 points pour MA50
        st.subheader("🚦 Signal automatique")
        if len(data) < 50 or pd.isna(data["MA50"].iloc[-1]):
            st.info("Signal non disponible (données insuffisantes).")
        else:
            last_close = data["Close"].iloc[-1]
            ma20 = data["MA20"].iloc[-1]
            ma50 = data["MA50"].iloc[-1]

            if last_close > ma20 and ma20 > ma50:
                st.success("✅ SIGNAL : Achat – tendance haussière confirmée.")
            elif last_close < ma20 and ma20 < ma50:
                st.error("❌ SIGNAL : Vente – tendance baissière confirmée.")
            else:
                st.warning("⚠️ SIGNAL : Attente – marché incertain.")

            # Afficher le dernier cours
            st.markdown(f"**Dernier cours** : {last_close:.2f} USD")
