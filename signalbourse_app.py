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

if ticker:
    data = yf.download(ticker, period="6mo", interval="1d", progress=False)

    if data.empty:
        st.error("❌ Aucune donnée trouvée pour ce ticker.")
    else:
        data["MA20"] = data["Close"].rolling(window=20).mean()
        data["MA50"] = data["Close"].rolling(window=50).mean()

        st.subheader("📊 Graphique de l'action")
        fig, ax = plt.subplots()
        ax.plot(data.index, data["Close"], label="Cours", linewidth=2)
        ax.plot(data.index, data["MA20"], label="MA20 (20j)", linestyle="--")
        ax.plot(data.index, data["MA50"], label="MA50 (50j)", linestyle=":")
        ax.legend()
        st.pyplot(fig)

        st.subheader("🚦 Signal automatique")

        last_close = data["Close"].iloc[-1]
        ma20_value = data["MA20"].iloc[-1]
        ma50_value = data["MA50"].iloc[-1]

        if pd.notna(last_close) and pd.notna(ma20_value) and pd.notna(ma50_value):
            if last_close > ma20_value and ma20_value > ma50_value:
                st.success("✅ SIGNAL : Achat – tendance haussière confirmée.")
            elif last_close < ma20_value and ma20_value < ma50_value:
                st.error("❌ SIGNAL : Vente – tendance baissière confirmée.")
            else:
                st.warning("⚠️ SIGNAL : Attente – marché incertain.")

            st.markdown(f"**Dernier cours** : {last_close:.2f} USD")
        else:
            st.info("Signal non disponible (valeurs manquantes dans les données).")
