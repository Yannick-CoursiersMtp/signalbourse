import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math

# 1) Config page
st.set_page_config(page_title="SignalBourse Pro", layout="wide")

# 2) Header
st.title("📈 SignalBourse Pro – Indicateurs & Gestion de risque")
st.markdown(
    "Moyennes mobiles, RSI, MACD, Bollinger, stop-loss/take-profit + Top 5 sectoriel"
)

# 3) Input ticker
ticker = st.text_input("Ton ticker principal :", "AAPL").upper().strip()
if not ticker:
    st.info("🔍 Entre un ticker pour commencer.")
    st.stop()

# 4) Download data
data = yf.download(ticker, period="6mo", interval="1d", progress=False)
if data.empty:
    st.error(f"❌ Aucune donnée pour « {ticker} ».")
    st.stop()

# 5) Indicateurs de base
data["MA20"]     = data["Close"].rolling(20).mean()
data["MA50"]     = data["Close"].rolling(50).mean()
data["VolAvg20"] = data["Volume"].rolling(20).mean()

# 6) RSI(14)
delta     = data["Close"].diff()
gain      = delta.clip(lower=0)
loss      = -delta.clip(upper=0)
avg_gain  = gain.rolling(14).mean()
avg_loss  = loss.rolling(14).mean()
rs        = avg_gain / avg_loss
data["RSI"] = 100 - (100 / (1 + rs))

# 7) MACD (12,26,9)
ema12          = data["Close"].ewm(span=12, adjust=False).mean()
ema26          = data["Close"].ewm(span=26, adjust=False).mean()
data["MACD"]   = ema12 - ema26
data["Signal9"]= data["MACD"].ewm(span=9, adjust=False).mean()

# 8) Bollinger Bands (20j, ±2σ)
m20 = data["Close"].rolling(20).mean()
std = data["Close"].rolling(20).std()
data["BB_up"] = m20 + 2 * std
data["BB_dn"] = m20 - 2 * std

# 9) Extraire last values (cast en float)
last  = float(data["Close"].iloc[-1])
ma20  = float(data["MA20"].iloc[-1])
ma50  = float(data["MA50"].iloc[-1])
vol   = float(data["Volume"].iloc[-1])
vol20 = float(data["VolAvg20"].iloc[-1])
rsi   = float(data["RSI"].iloc[-1])
macd  = float(data["MACD"].iloc[-1])
sig9  = float(data["Signal9"].iloc[-1])
bb_up = float(data["BB_up"].iloc[-1])
bb_dn = float(data["BB_dn"].iloc[-1])

# 10) Graphiques principaux
st.subheader(f"📊 Graphiques et indicateurs pour {ticker}")
fig = plt.figure(constrained_layout=True, figsize=(10,8))
gs  = fig.add_gridspec(3,1, height_ratios=[3,1,1])

# 10a) Cours + MA + Bollinger
ax0 = fig.add_subplot(gs[0])
ax0.plot(data.index, data["Close"], label="Cours", lw=1.5)
ax0.plot(data.index, data["MA20"], "--", label="MA20")
ax0.plot(data.index, data["MA50"], ":",  label="MA50")
ax0.fill_between(data.index, data["BB_up"], data["BB_dn"], color="grey", alpha=0.1, label="Bollinger")
ax0.legend(loc="upper left")

# 10b) RSI
ax1 = fig.add_subplot(gs[1], sharex=ax0)
ax1.plot(data.index, data["RSI"], label="RSI(14)", color="purple")
ax1.axhline(70, color="red", linestyle="--")
ax1.axhline(30, color="green", linestyle="--")
ax1.legend(loc="upper left")

# 10c) MACD
ax2 = fig.add_subplot(gs[2], sharex=ax0)
ax2.plot(data.index, data["MACD"], label="MACD", color="blue")
ax2.plot(data.index, data["Signal9"], label="Signal(9)", color="orange")
ax2.legend(loc="upper left")

st.pyplot(fig)

# 11) Signal enrichi (dé-chaînage des comparaisons)
st.subheader("🚦 Ton signal enrichi")
notes = []

# 11a) Tendance MA + volume
cond_up1  = last > ma20
cond_up2  = ma20 > ma50
cond_vol1 = vol >= 0.8 * vol20
if cond_up1 and cond_up2 and cond_vol1:
    notes.append("✅ Tendance haussière confirmée (MA20>MA50 & volume élevé)")
else:
    cond_dn1  = last < ma20
    cond_dn2  = ma20 < ma50
    cond_vol2 = vol <= 1.2 * vol20
    if cond_dn1 and cond_dn2 and cond_vol2:
        notes.append("❌ Tendance baissière confirmée (MA20<MA50 & volume faible)")
    else:
        notes.append("⚠️ Tendance neutre ou volume non significatif")

# 11b) RSI
if rsi < 30:
    notes.append("🟢 RSI survendu (<30)")
elif rsi > 70:
    notes.append("🔴 RSI suracheté (>70)")

# 11c) MACD
if macd > sig9:
    notes.append("🟢 MACD bullish cross")
else:
    notes.append("🔴 MACD bearish cross")

# 11d) Bollinger
if last < bb_dn:
    notes.append("🟢 Cours sous bande inférieure (possible rebond)")
elif last > bb_up:
    notes.append("🔴 Cours au-dessus bande supérieure (possible excès)")

# 11e) Calcul final
buys  = sum(1 for n in notes if n.startswith("🟢"))
sells = sum(1 for n in notes if n.startswith("🔴"))
advice = "🟢 ACHETER maintenant" if buys > sells else "🔴 VENDRE maintenant" if sells > buys else "🟡 ATTENDRE"
st.markdown(f"## {advice}")
for n in notes:
    st.markdown(f"- {n}")

# 12) Gestion de risque (théorique stop-loss/take-profit)
st.subheader("⚖️ Gestion de risque (théorique)")
entry = last
sl    = entry * 0.95  # -5 %
tp    = entry * 1.10  # +10 %
st.markdown(f"- Prix d’entrée : {entry:.2f} USD")
st.markdown(f"- Stop-loss (-5 %) : {sl:.2f} USD")
st.markdown(f"- Take-profit (+10 %) : {tp:.2f} USD")

# 13) Top 5 sectoriel (ticker + nom)
@st.cache_data(ttl=24*3600)
def load_sp500():
    url   = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    table = pd.read_html(url, header=0)[0]
    table = table[["Symbol","Security","GICS Sector"]]
    table.columns = ["Ticker","Name","Sector"]
    return table

sp500    = load_sp500()
sector   = yf.Ticker(ticker).info.get("sector","Inconnu")
candidates = sp500[sp500["Sector"]==sector][["Ticker","Name"]].to_dict("records")

st.subheader("✅ Top 5 opportunités dans ton secteur")
buy_list = []
progress = st.progress(0)
for i, rec in enumerate(candidates):
    sym, name = rec["Ticker"], rec["Name"]
    try:
        df = yf.download(sym, period="6mo", interval="1d", progress=False)
        if df.shape[0] < 60: continue
        m20 = df["Close"].rolling(20).mean().iloc[-1]
        m50 = df["Close"].rolling(50).mean().iloc[-1]
        v20= df["Volume"].rolling(20).mean().iloc[-1]
        lastf = float(df["Close"].iloc[-1])
        m20f,m50f,v20f = float(m20), float(m50), float(v20)
        if math.isnan(m20f) or math.isnan(m50f) or math.isnan(v20f):
            continue
        volf = float(df["Volume"].iloc[-1])
        if lastf > m20f and m20f > m50f and volf >= 0.8 * v20f:
            pct = (lastf - m20f) / m20f * 100
            buy_list.append((sym, name, lastf, pct))
    except:
        pass
    progress.progress((i+1)/len(candidates))

buy_list.sort(key=lambda x: x[3], reverse=True)
if buy_list:
    for sym, name, price, pct in buy_list[:5]:
        st.markdown(f"- **{sym}** — {name} : {price:.2f} USD  ({pct:+.1f}% vs MA20)")
else:
    st.info("Aucune opportunité d’achat détectée dans ce secteur.")
