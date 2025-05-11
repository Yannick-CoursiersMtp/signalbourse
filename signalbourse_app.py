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

# 3) Saisie du ticker
ticker = st.text_input("Ticker :", value="AAPL").upper().strip()
if not ticker:
    st.info("🔍 Entrez un ticker pour démarrer.")
    st.stop()

# 4) Récupération des données
data = yf.download(ticker, period="6mo", interval="1d", progress=False)
if data.empty:
    st.error(f"❌ Aucun historique pour « {ticker} ».")
    st.stop()

# 5) Calcul des indicateurs
data["MA20"]    = data["Close"].rolling(window=20).mean()
data["MA50"]    = data["Close"].rolling(window=50).mean()
data["VolAvg20"]= data["Volume"].rolling(window=20).mean()

# 6) Extraction des dernières valeurs avec .iloc[-1]
last   = data["Close"].iloc[-1]
ma20   = data["MA20"].iloc[-1]
ma50   = data["MA50"].iloc[-1]
vol    = data["Volume"].iloc[-1]
vol20  = data["VolAvg20"].iloc[-1]
pct20  = (last - ma20) / ma20 * 100 if pd.notna(ma20) else None

# 7) Affichage du graphique prix + volumes
st.subheader("📊 Graphique & Volume")
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 6), sharex=True)
ax1.plot(data.index, data["Close"], label="Cours", linewidth=2)
ax1.plot(data.index, data["MA20"], "--", label="MA20")
ax1.plot(data.index, data["MA50"], ":", label="MA50")
ax1.legend()
ax2.bar(data.index, data["Volume"], alpha=0.3, label="Volume quotidien")
ax2.plot(data.index, data["VolAvg20"], color="orange", label="Volume Moy20")
ax2.legend()
st.pyplot(fig)

# 8) Calcul du signal unique
st.subheader("🚦 Signal et Conseils")
if pd.notna(ma20) and pd.notna(ma50) and pd.notna(vol20):
    if (last > ma20 > ma50) and (vol > vol20):
        st.success("🟢 ACHETER maintenant")
        advice = "Placez un stop-loss à 5 % en dessous du cours actuel."
    elif (last < ma20 < ma50) and (vol < vol20):
        st.error("🔴 VENDRE maintenant")
        advice = "Sécurisez vos gains ou réduisez votre position."
    else:
        st.info("🟡 ATTENDRE")
        advice = "Attendez qu’une condition claire (breakout) soit respectée."
else:
    st.warning("⚠️ Signal indisponible (données insuffisantes).")
    advice = "Revenez demain ou essayez un autre ticker."

# 9) Affichage des métriques
st.markdown(f"**Prix actuel ({ticker}) :** {last:.2f} USD")
if pct20 is not None:
    st.markdown(f"**Écart vs MA20 :** {pct20:+.2f} %")
st.markdown(f"**Volume (aujourd’hui) :** {int(vol):,}  |  **Moyenne 20j :** {int(vol20):,}")

# 10) Conseil final
st.markdown("**Conseil rapide :** " + advice)
