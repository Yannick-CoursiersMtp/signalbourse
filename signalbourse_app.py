import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import json

# 1) Config de la page
st.set_page_config(page_title="SignalBourse", layout="centered")

# 2) En-tête
st.title("📈 SignalBourse – Opportunités par secteur")
st.markdown(
    "Signal unique (Acheter/Attendre/Vendre) + top 5 opportunités dans le même secteur."
)

# 3) Saisie du ticker et récupération du secteur
ticker = st.text_input("Ticker :", "AAPL").upper().strip()
if not ticker:
    st.info("🔍 Entrez un ticker pour démarrer.")
    st.stop()
info   = yf.Ticker(ticker).info
sector = info.get("sector", "Inconnu")
st.markdown(f"**Secteur détecté :** {sector}")

# 4) Récupération des données du ticker principal
data = yf.download(ticker, period="6mo", interval="1d", progress=False)
if data.empty:
    st.error("❌ Ticker introuvable.")
    st.stop()

# 5) Calcul des indicateurs principaux
data["MA20"]     = data["Close"].rolling(20).mean()
data["MA50"]     = data["Close"].rolling(50).mean()
data["VolAvg20"] = data["Volume"].rolling(20).mean()

last  = float(data["Close"].iloc[-1])
ma20  = data["MA20"].iloc[-1]
ma50  = data["MA50"].iloc[-1]
vol   = int(data["Volume"].iloc[-1])
vol20 = data["VolAvg20"].iloc[-1]

# Si pas assez de données pour le signal principal
if pd.isna(ma20) or pd.isna(ma50) or pd.isna(vol20):
    st.subheader("🚦 Signal principal")
    st.warning("Données insuffisantes pour un signal fiable.")
    st.stop()

# 6) Affichage du graphique et volume
st.subheader("📊 Graphique & Volume")
fig, (ax1, ax2) = plt.subplots(2,1, figsize=(6,6), sharex=True)
ax1.plot(data.index, data["Close"], label="Cours", linewidth=2)
ax1.plot(data.index, data["MA20"], "--", label="MA20")
ax1.plot(data.index, data["MA50"], ":",  label="MA50")
ax1.legend()
ax2.plot(data.index, data["Volume"], label="Volume quotidien", alpha=0.6)
ax2.plot(data.index, data["VolAvg20"], color="orange", label="Vol Moy20")
ax2.legend()
st.pyplot(fig)

# 7) Calcul du signal principal
st.subheader("🚦 Signal principal")
is_buy  = (last > ma20 > ma50) and (vol > vol20)
is_sell = (last < ma20 < ma50) and (vol < vol20)

if is_buy:
    st.success("🟢 ACHETER maintenant")
elif is_sell:
    st.error("🔴 VENDRE maintenant")
else:
    st.info("🟡 ATTENDRE")

# 8) Top 5 dans le même secteur
st.subheader(f"✅ Top opportunités dans « {sector} »")
try:
    with open("sector_tickers.json") as f:
        universe = json.load(f).get(sector, [])
except Exception:
    universe = []

buy_list = []
for sym in universe:
    if sym == ticker:
        continue
    df = yf.download(sym, period="3mo", interval="1d", progress=False)
    if df.shape[0] < 50:
        continue
    m20 = df["Close"].rolling(20).mean().iloc[-1]
    m50 = df["Close"].rolling(50).mean().iloc[-1]
    v   = df["Volume"].iloc[-1]
    v20 = df["Volume"].rolling(20).mean().iloc[-1]
    if pd.notna(m20) and pd.notna(m50) and (df["Close"].iloc[-1] > m20 > m50) and (v > v20):
        pct = (df["Close"].iloc[-1] - m20) / m20 * 100
        buy_list.append((sym, df["Close"].iloc[-1], pct))

# Trier et afficher
buy_list.sort(key=lambda x: x[2], reverse=True)
if buy_list:
    for sym, price, pct in buy_list[:5]:
        st.markdown(f"- **{sym}** à {price:.2f} USD ({pct:+.1f}% vs MA20)")
else:
    st.info("Aucune autre opportunité d'achat détectée.")
