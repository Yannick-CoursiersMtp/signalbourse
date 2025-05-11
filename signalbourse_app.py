import json
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ————— CONFIGURATION DE LA PAGE —————
st.set_page_config(page_title="SignalBourse", layout="centered")

# ————— CHARGEMENT DE TA WATCHLIST —————
# Assure-toi que le fichier mes_actions.json est à la racine
with open("mes_actions.json", "r") as f:
    tickers_list = json.load(f)

# ————— SIDEBAR —————
st.sidebar.title("Paramètres")
periode    = st.sidebar.selectbox("Période historique", ["6mo", "1y", "2y"], index=2)
vol_window = st.sidebar.slider("Fenêtre volume (jours)", 5, 50, 20)

# ————— INTERFACE PRINCIPALE —————
st.title("📈 SignalBourse – Analyse rapide")
ticker = st.text_input("Saisis un ticker", value="AAPL").upper()
if not ticker:
    st.error("👉 Renseigne un ticker pour commencer.")
    st.stop()

# ————— RÉCUPÉRATION DES DONNÉES —————
data = yf.download(ticker, period=periode, interval="1d", progress=False)
if data.empty:
    st.error(f"Aucune donnée pour « {ticker} ».")
    st.stop()

# ————— CALCUL DES INDICATEURS —————
data["MA20"]   = data["Close"].rolling(window=20).mean()
data["MA50"]   = data["Close"].rolling(window=50).mean()
data["VolMoy"] = data["Volume"].rolling(window=vol_window).mean()

# ————— AFFICHAGE DU GRAPHIQUE DES PRIX & MAs —————
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(data.index, data["Close"], label="Cours")
ax.plot(data.index, data["MA20"], "--", label="MA20")
ax.plot(data.index, data["MA50"], ":", label="MA50")
ax.legend(loc="upper left")
ax.set_ylabel("Prix USD")
st.pyplot(fig)

# ————— AFFICHAGE DU VOLUME & DE SA MOYENNE —————
st.subheader("📊 Volume & Moyenne volume")
st.bar_chart(data["Volume"])
st.line_chart(data["VolMoy"])

# ————— SIGNAL PRINCIPAL (ACHAT / VENTE / ATTENDRE) —————
# On force la conversion en float pour éviter toute Series ambiguë
last       = float(data["Close"].iloc[-1])
ma20       = float(data["MA20"].iloc[-1])
ma50       = float(data["MA50"].iloc[-1])

# calcul des flags d’achat et de vente
buy_signal  = (last > ma20) and (ma20 > ma50)
sell_signal = (last < ma20) and (ma20 < ma50)

if buy_signal:
    st.success("✅ ACHETER maintenant")
elif sell_signal:
    st.error("❌ VENDRE maintenant")
else:
    st.warning("⚠️ ATTENDRE")

# ————— DÉTAILS CHIFFRÉS —————
vol_today = int(data["Volume"].iloc[-1])
vol_moy   = int(data["VolMoy"].iloc[-1])
ecart     = 100 * (last / ma20 - 1)

st.markdown(f"- **Prix actuel** : {last:.2f} USD")
st.markdown(f"- **Écart vs MA20** : {ecart:+.2f}%")
st.markdown(f"- **Volume ajd** : {vol_today:,d} | Moy{vol_window}j : {vol_moy:,d}")

# ————— TOP 5 OPPORTUNITÉS SUR TON PANEL —————
st.header("✅ Top 5 opportunités sur ton panel")
opps = []
for tk in tickers_list:
    df = yf.download(tk, period="6mo", interval="1d", progress=False)
    if df.empty: 
        continue
    m20 = df["Close"].rolling(window=20).mean().iloc[-1]
    c   = df["Close"].iloc[-1]
    if not np.isnan(m20) and (c > m20):
        diff = 100 * (c / m20 - 1)
        opps.append((tk, c, diff))

opps = sorted(opps, key=lambda x: x[2], reverse=True)[:5]
if not opps:
    st.info("Aucune opportunité détectée.")
else:
    for tk, price, diff in opps:
        st.markdown(f"- **{tk}** : {price:.2f} USD ({diff:+.2f}% vs MA20)")
