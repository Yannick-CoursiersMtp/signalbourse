import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="SignalBourse", layout="centered")

st.title("📈 SignalBourse – Analyse rapide d'actions")
st.markdown(
    "Tape un **ticker boursier** (ex : `AAPL`, `TSLA`, `SAN.PA`) pour recevoir "
    "un signal d'achat, vente ou attente basé sur les moyennes mobiles."
)

ticker = st.text_input("Nom de l'action / Ticker :", value="AAPL")

if ticker:
    data = yf.download(ticker, period="6mo", interval="1d")
    if data.empty:
        st.error("Aucune donnée trouvée pour ce ticker.")
    else:
        data["MA20"] = data["Close"].rolling(window=20).mean()
        data["MA50"] = data["Close"].rolling(window=50).mean()

        st.subheader("Graphique de l'action")
        fig, ax = plt.subplots()
        ax.plot(data.index, data["Close"], label="Cours")
        ax.plot(data.index, data["MA20"], label="MA20", linestyle="--")
        ax.plot(data.index, data["MA50"], label="MA50", linestyle=":")
        ax.legend()
        st.pyplot(fig)

        st.subheader("Signal automatique")
        try:
            last_close = data["Close"].iloc[-1]
            ma20 = data["MA20"].iloc[-1]
            ma50 = data["MA50"].iloc[-1]
            if last_close > ma20 > ma50:
                st.success("SIGNAL : Achat – tendance haussière confirmée.")
            elif last_close < ma20 < ma50:
                st.error("SIGNAL : Vente – tendance baissière confirmée.")
            else:
                st.warning("SIGNAL : Attente – marché incertain.")
        except Exception:
            st.info("Signal non disponible (données insuffisantes ou erreur).")

        st.markdown(f"**Dernier cours** : {last_close:.2f} USD")
