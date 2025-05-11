import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# 1) Config de la page
st.set_page_config(page_title="SignalBourse", layout="centered")

# 2) En-tête
st.title("📈 SignalBourse – Signal Clair et Fiable")
st.markdown(
    "Un seul message pour **ACHETER / ATTENDRE / VENDRE**, plus % vs MA20 et volume."
)

# 3) Champ ticker
ticker = st.text_input("Ticker :", value="AAPL").upper().strip()
if not ticker:
    st.info("🔍 Entrez un ticker pour commencer.")
    st.stop()

# 4) Récupération des données
data = yf.download(ticker, period="6mo", interval="1d", progress=False)
if data.empty:
    st.error(f"❌ Aucun historique disponible pour « {ticker} ».")
    st.stop()

# 5) Calcul des indicateurs
data["MA20"]     = data["Close"].rolling(20).mean()
data["MA50"]     = data["Close"].rolling(50).mean()
data["VolAvg20"] = data["Volume"].rolling(20).mean()

# 6) Extraction et conversion en types Python
last  = float(data["Close"].iloc[-1])
ma20  = data["MA20"].iloc[-1]
ma50  = data["MA50"].iloc[-1]
vol   = int(data["Volume"].iloc[-1])
vol20 = data["VolAvg20"].iloc[-1]

# Vérification qu’on a bien des floats, sinon on stop
if pd.isna(ma20) or pd.isna(ma50) or pd.isna(vol20):
    st.subheader("🚦 Signal indisponible")
    st.warning("Données insuffisantes ou trop récentes pour calculer un signal.")
    st.stop()

ma20, ma50, vol20 = float(ma20), float(ma50), float(vol20)

# 7) Graphique prix + volumes
st.subheader("📊 Graphique & Volume")
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 6), sharex=True)

# Prix et moyennes
ax1.plot(data.index, data["Close"], label="Cours", linewidth=2)
ax1.plot(data.index, data["MA20"], "--", label="MA20")
ax1.plot(data.index, data["MA50"], ":",  label="MA50")
ax1.legend()

# Volume et moyenne de volume
ax2.plot(data.index, data["Volume"], label="Volume quotidien", alpha=0.6)
ax2.plot(data.index, data["VolAvg20"], color="orange", label="Volume Moy20")
ax2.legend()

st.pyplot(fig)

# 8) Calcul explicite du signal
st.subheader("🚦 Signal et Conseils")
# Conditions
is_buy  = (last > ma20) and (ma20 > ma50) and (vol > vol20)
is_sell = (last < ma20) and (ma20 < ma50) and (vol < vol20)

if is_buy:
    st.success("🟢 ACHETER maintenant")
    advice = "Placez un stop-loss 5 % en dessous du cours actuel."
elif is_sell:
    st.error("🔴 VENDRE maintenant")
    advice = "Sécurisez vos gains ou réduisez votre position."
else:
    st.info("🟡 ATTENDRE")
    advice = "Attendez qu’une condition claire soit validée."

# 9) Affichage des métriques
pct20 = (last - ma20) / ma20 * 100
st.markdown(f"**Prix actuel ({ticker}) :** {last:.2f} USD")
st.markdown(f"**Écart vs MA20 :** {pct20:+.2f}%")
st.markdown(f"**Volume (aujourd’hui) :** {vol:,} | **Moyenne 20j :** {int(vol20):,}")

# 10) Conseil final
st.markdown("**Conseil rapide :** " + advice)
