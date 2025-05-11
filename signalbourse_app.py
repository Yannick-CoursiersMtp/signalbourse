import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# Config page
st.set_page_config(page_title="SignalBourse", layout="centered")

# En-tête
st.title("📈 SignalBourse – Signal Clair")
st.markdown("Un seul message pour **Acheter / Attendre / Vendre**, plus % vs MA20 et volume.")

# Ticker
ticker = st.text_input("Ticker :", value="AAPL").upper().strip()
if not ticker:
    st.stop()

# Data fetch
data = yf.download(ticker, period="6mo", interval="1d", progress=False)
if data.empty:
    st.error("❌ Ticker introuvable")
    st.stop()

# Indicateurs
data["MA20"] = data["Close"].rolling(20).mean()
data["MA50"] = data["Close"].rolling(50).mean()
data["VolAvg20"] = data["Volume"].rolling(20).mean()

last = data["Close"].iat[-1]
ma20  = data["MA20"].iat[-1]
ma50  = data["MA50"].iat[-1]
vol   = data["Volume"].iat[-1]
vol20 = data["VolAvg20"].iat[-1]
pct20 = (last - ma20) / ma20 * 100 if pd.notna(ma20) else None

# Graphique
fig, (ax1, ax2) = plt.subplots(2,1, figsize=(6,6), sharex=True)
ax1.plot(data.index, data["Close"], label="Cours", linewidth=2)
ax1.plot(data.index, data["MA20"], "--", label="MA20")
ax1.plot(data.index, data["MA50"], ":",  label="MA50")
ax1.legend()
ax2.bar(data.index, data["Volume"], alpha=0.3, label="Volume")
ax2.plot(data.index, data["VolAvg20"], color="orange", label="Vol Moy20")
ax2.legend()
st.pyplot(fig)

# Calcul du signal
if pd.notna(ma20) and pd.notna(ma50) and pd.notna(vol20):
    if last > ma20 > ma50 and vol > vol20:
        st.success("🟢 ACHETER maintenant")
        advice = "Placez un stop‐loss à 5 % sous le cours actuel."
    elif last < ma20 < ma50 and vol < vol20:
        st.error("🔴 VENDRE maintenant")
        advice = "Envisagez de sécuriser vos gains."
    else:
        st.info("🟡 ATTENDRE")
        advice = "Attendez qu’une condition claire soit confirmée."
else:
    st.warning("⚠️ données insuffisantes pour signal")
    advice = "Revenez demain ou vérifiez un autre ticker."

# Affichage des métriques
st.markdown(f"**Prix actuel** : {last:.2f} USD")
if pct20 is not None: st.markdown(f"**Écart vs MA20** : {pct20:+.2f}%")
st.markdown(f"**Volume aujourd’hui** : {int(vol):,}  (Moy20 : {int(vol20):,})")

# Conseils
st.markdown("**Conseil rapide :** " + advice)
