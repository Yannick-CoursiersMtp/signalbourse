import json
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# —————— CONFIG ——————
st.set_page_config(page_title="SignalBourse", layout="centered")

# —————— CHARGEMENT DES ACTIONS ——————
with open("mes_actions.json", "r") as f:
    tickers_list = json.load(f)

# —————— SIDEBAR ——————
st.sidebar.title("Paramètres")
periode = st.sidebar.selectbox("Période historique", ["6mo", "1y", "2y"], index=2)
vol_window = st.sidebar.slider("Fenêtre volume (jours)", 5, 50, 20)

# —————— INPUT PRINCIPAL ——————
st.title("📈 SignalBourse – Analyse rapide")
ticker = st.text_input("Saisis un ticker", value="AAPL").upper()

if not ticker:
    st.error("👉 Tapez un ticker pour commencer.")
    st.stop()

# —————— RÉCUP DONNÉES ——————
data = yf.download(ticker, period=periode, interval="1d")
if data.empty:
    st.error(f"Aucune donnée pour {ticker}.")
    st.stop()

# —————— CALCUL MOYENNES & VOLUME ——————
data["MA20"] = data["Close"].rolling(window=20).mean()
data["MA50"] = data["Close"].rolling(window=50).mean()
data["Vol_Moy"] = data["Volume"].rolling(window=vol_window).mean()

# —————— GRAPHIQUES ——————
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
ax1.plot(data.index, data["Close"], label="Cours")
ax1.plot(data.index, data["MA20"], "--", label="MA20")
ax1.plot(data.index, data["MA50"], ":", label="MA50")
ax1.legend(loc="upper left")
ax1.set_ylabel("Prix USD")

ax2.bar(data.index, data["Volume"], width=0.8, alpha=0.3, label="Volume quotidien")
ax2.plot(data.index, data["Vol_Moy"], "-", linewidth=2, label=f"Volume Moy{vol_window}j")
ax2.legend(loc="upper left")
ax2.set_ylabel("Volume")
st.pyplot(fig)

# —————— SIGNAL PRINCIPAL ——————
last = data["Close"].iloc[-1]
ma20 = data["MA20"].iloc[-1]
ma50 = data["MA50"].iloc[-1]
vol = data["Volume"].iloc[-1]
vol_moy = data["Vol_Moy"].iloc[-1]

if np.isnan(ma20) or np.isnan(ma50):
    st.info("Signal principal non disponible (trop peu de données).")
else:
    if last > ma20 > ma50:
        st.success("✅ ACHETER maintenant")
    elif last < ma20 < ma50:
        st.error("❌ VENDRE maintenant")
    else:
        st.warning("⚠️ ATTENDRE")

# —————— DÉTAILS DU SIGNAL ——————
st.markdown(f"- **Prix actuel** : {last:.2f} USD")
st.markdown(f"- **Écart vs MA20** : {100*(last/ma20-1):+.2f}%")
st.markdown(f"- **Volume ajd** : {vol:,d} | Moy{vol_window}j : {vol_moy:,.0f}")

# —————— TOP 5 OPPORTUNITÉS ——————
st.header("✅ Top 5 opportunités sur ton panel")

opps = []
for tk in tickers_list:
    try:
        df = yf.download(tk, period="6mo", interval="1d")
        if df.empty: continue
        ma20_ = df["Close"].rolling(20).mean().iloc[-1]
        close_ = df["Close"].iloc[-1]
        if close_ > ma20_:  # condition simplifiée d'achat
            diff = 100*(close_/ma20_-1)
            opps.append((tk, close_, diff))
    except:
        pass

opps = sorted(opps, key=lambda x: x[2], reverse=True)[:5]
if not opps:
    st.info("Aucune opportunité détectée.")
else:
    for tk, price, diff in opps:
        st.markdown(f"- **{tk}** : {price:.2f} USD ({diff:+.2f}% vs MA20)")
