import json
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ————— CONFIG —————
st.set_page_config(page_title="SignalBourse", layout="centered")

# ————— CHARGEMENT DU PANEL (tes 50 tickers) —————
# Crée un fichier mes_actions.json à la racine contenant ta liste de tickers, par ex :
# ["AAPL","MSFT","GOOGL", ...]
with open("mes_actions.json", "r") as f:
    tickers_list = json.load(f)

# ————— SIDEBAR —————
st.sidebar.title("Paramètres")
periode = st.sidebar.selectbox("Période historique", ["6mo", "1y", "2y"], index=2)
vol_window = st.sidebar.slider("Fenêtre volume (jours)", 5, 50, 20)

# ————— INPUT —————
st.title("📈 SignalBourse – Analyse rapide")
ticker = st.text_input("Saisis un ticker", value="AAPL").upper()
if not ticker:
    st.error("👉 Renseigne un ticker pour commencer.")
    st.stop()

# ————— RÉCUP DONNÉES —————
data = yf.download(ticker, period=periode, interval="1d")
if data.empty:
    st.error(f"Aucune donnée pour « {ticker} ».")
    st.stop()

# ————— CALCULS —————
data["MA20"] = data["Close"].rolling(20).mean()
data["MA50"] = data["Close"].rolling(50).mean()
data["VolMoy"] = data["Volume"].rolling(vol_window).mean()

# ————— GRAPHIQUE PRIX + MA —————
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(data.index, data["Close"], label="Cours")
ax.plot(data.index, data["MA20"], "--", label="MA20")
ax.plot(data.index, data["MA50"], ":", label="MA50")
ax.legend(loc="upper left")
ax.set_ylabel("Prix USD")
st.pyplot(fig)

# ————— VOLUME (Streamlit natif) —————
st.subheader("📊 Volume & Moyenne volume")
st.bar_chart(data["Volume"])
st.line_chart(data["VolMoy"])

# ————— SIGNAL PRINCIPAL —————
# on force la récupération en scalaire avec .iat
last = data["Close"].iat[-1]
ma20 = data["MA20"].iat[-1]
ma50 = data["MA50"].iat[-1]

if np.isnan(ma20) or np.isnan(ma50):
    st.info("Signal principal non disponible (trop peu de données).")
else:
    if (last > ma20) and (ma20 > ma50):
        st.success("✅ ACHETER maintenant")
    elif (last < ma20) and (ma20 < ma50):
        st.error("❌ VENDRE maintenant")
    else:
        st.warning("⚠️ ATTENDRE")

# ————— DÉTAILS —————
st.markdown(f"- **Prix actuel** : {last:.2f} USD")
st.markdown(f"- **Écart vs MA20** : {100*(last/ma20-1):+.2f}%")
st.markdown(f"- **Volume ajd** : {data['Volume'].iat[-1]:,d} | Moy{vol_window}j : {data['VolMoy'].iat[-1]:,.0f}")

# ————— TOP 5 OPPORTUNITÉS —————
st.header("✅ Top 5 opportunités sur ton panel")
opps = []
for tk in tickers_list:
    df = yf.download(tk, period="6mo", interval="1d", progress=False)
    if df.empty:
        continue
    ma20_ = df["Close"].rolling(20).mean().iat[-1]
    close_ = df["Close"].iat[-1]
    if not np.isnan(ma20_) and (close_ > ma20_):
        opps.append((tk, close_, 100 * (close_ / ma20_ - 1)))
opps = sorted(opps, key=lambda x: x[2], reverse=True)[:5]
if not opps:
    st.info("Aucune opportunité détectée.")
else:
    for tk, price, diff in opps:
        st.markdown(f"- **{tk}** : {price:.2f} USD ({diff:+.2f}% vs MA20)")
