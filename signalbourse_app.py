import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="SignalBourse", layout="centered")

st.title("📈 SignalBourse – Analyse rapide d'actions")
st.markdown(
    "Entrez un **ticker boursier** (ex : `AAPL`, `TSLA`, `SAN.PA`) pour recevoir "
    "un signal d'achat, vente ou attente basé sur les moyennes mobiles 20j/50j."
)

ticker = st.text_input("Nom de l'action / Ticker :", value="AAPL").upper().strip()
if not ticker:
    st.info("🔍 Veuillez entrer un ticker pour lancer l'analyse.")
    st.stop()

# Récupère 6 mois de cours
data = yf.download(ticker, period="6mo", interval="1d", progress=False)

if data.empty:
    st.error(f"❌ Aucune donnée trouvée pour « {ticker} ».")
    st.stop()

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

# Préparation des valeurs en tant que float
last_close = float(data["Close"].iloc[-1])
ma20 = data["MA20"].iloc[-1]
ma50 = data["MA50"].iloc[-1]

# Si pas assez de données, on ne calcule pas le signal
if pd.isna(ma20) or pd.isna(ma50):
    st.subheader("🚦 Signal automatique")
    st.info("ℹ️ Signal non disponible (données insuffisantes).")
else:
    ma20 = float(ma20)
    ma50 = float(ma50)

    st.subheader("🚦 Signal automatique")
    if last_close > ma20 and ma20 > ma50:
        st.success("✅ SIGNAL : Achat – tendance haussière confirmée.")
    elif last_close < ma20 and ma20 < ma50:
        st.error("❌ SIGNAL : Vente – tendance baissière confirmée.")
    else:
        st.warning("⚠️ SIGNAL : Attente – marché incertain.")

    st.markdown(f"**Dernier cours ({ticker})** : {last_close:.2f} USD")
