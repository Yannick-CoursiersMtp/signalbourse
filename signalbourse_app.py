import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
from concurrent.futures import ThreadPoolExecutor, as_completed

@st.cache_data(ttl=3600)
def backtest_signals(data: pd.DataFrame, entry_signal: pd.Series, exit_pct: float = 0.05):
    trades = []
    in_trade = False
    entry_price = None
    entry_date = None
    tp = sl = None

    for date, signal in entry_signal.iteritems():
        price = data.at[date, "Close"]
        if signal and not in_trade:
            in_trade = True
            entry_price = price
            entry_date = date
            tp = entry_price * (1 + exit_pct)
            sl = entry_price * (1 - exit_pct)
        elif in_trade:
            if price >= tp or price <= sl:
                ret = (price - entry_price) / entry_price
                trades.append({
                    "entry": entry_date,
                    "exit": date,
                    "return": ret
                })
                in_trade = False

    df_trades = pd.DataFrame(trades)
    if df_trades.empty:
        return {"trades": df_trades, "precision": None, "avg_return": None, "profit_factor": None}
    precision = (df_trades["return"] > 0).mean()
    avg_ret = df_trades["return"].mean()
    gains = df_trades[df_trades["return"] > 0]["return"].sum()
    losses = -df_trades[df_trades["return"] <= 0]["return"].sum()
    pf = gains / losses if losses > 0 else None
    return {"trades": df_trades, "precision": precision, "avg_return": avg_ret, "profit_factor": pf}

@st.cache_data(ttl=3600)
def get_ticker_data(sym: str) -> pd.DataFrame:
    return yf.download(sym, period="6mo", interval="1d", progress=False)

st.set_page_config(page_title="SignalBourse Pro", layout="wide")

exit_pct = st.sidebar.slider("Stop/Loss & Take/Profit (%)", min_value=1, max_value=20, value=5, step=1) / 100

ticker = st.text_input("Ton ticker principal :", "AAPL").upper().strip()
if not ticker:
    st.info("🔍 Entre un ticker pour commencer.")
    st.stop()

data = get_ticker_data(ticker)
if data.empty:
    st.error(f"❌ Pas de données pour '{ticker}'.")
    st.stop()

data["MA20"] = data["Close"].rolling(20).mean()
data["MA50"] = data["Close"].rolling(50).mean()
data["VolAvg20"] = data["Volume"].rolling(20).mean()

delta = data["Close"].diff()
gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)
data["RSI"] = 100 - (100 / (1 + gain.rolling(14).mean() / loss.rolling(14).mean()))

ema12 = data["Close"].ewm(span=12, adjust=False).mean()
ema26 = data["Close"].ewm(span=26, adjust=False).mean()
data["MACD"] = ema12 - ema26
data["Signal9"] = data["MACD"].ewm(span=9, adjust=False).mean()

m20 = data["Close"].rolling(20).mean()
std = data["Close"].rolling(20).std()
data["BB_up"] = m20 + 2 * std
data["BB_dn"] = m20 - 2 * std

last = float(data["Close"].iloc[-1])
ma20 = float(data["MA20"].iloc[-1])
ma50 = float(data["MA50"].iloc[-1])
vol = float(data["Volume"].iloc[-1])
vol20 = float(data["VolAvg20"].iloc[-1])
rsi = float(data["RSI"].iloc[-1])
macd = float(data["MACD"].iloc[-1])
sig9 = float(data["Signal9"].iloc[-1])
bb_up = float(data["BB_up"].iloc[-1])
bb_dn = float(data["BB_dn"].iloc[-1])

st.subheader(f"📊 Indicateurs pour {ticker}")
fig = plt.figure(constrained_layout=True, figsize=(10, 8))
gs = fig.add_gridspec(3, 1, height_ratios=[3, 1, 1])
ax0 = fig.add_subplot(gs[0])
ax0.plot(data.index, data["Close"], label="Cours", lw=1.5)
ax0.plot(data.index, data["MA20"], "--", label="MA20")
ax0.plot(data.index, data["MA50"], ":", label="MA50")
ax0.fill_between(data.index, data["BB_up"], data["BB_dn"], color="grey", alpha=0.1, label="Bollinger")
ax0.legend(loc="upper left")
ax1 = fig.add_subplot(gs[1], sharex=ax0)
ax1.plot(data.index, data["RSI"], label="RSI(14)", color="purple")
ax1.axhline(70, color="red", linestyle="--")
ax1.axhline(30, color="green", linestyle="--")
ax1.legend(loc="upper left")
ax2 = fig.add_subplot(gs[2], sharex=ax0)
ax2.plot(data.index, data["MACD"], label="MACD", color="blue")
ax2.plot(data.index, data["Signal9"], label="Signal(9)", color="orange")
ax2.legend(loc="upper left")
st.pyplot(fig)

st.subheader("🚦 Ton signal enrichi")
notes = []
up1 = last > ma20
up2 = ma20 > ma50
vol1 = vol >= 0.8 * vol20
if up1 and up2 and vol1:
    notes.append("✅ Tendance haussière (MA20>MA50 + volume ok)")
else:
    dn1 = last < ma20
    dn2 = ma20 < ma50
    vol2 = vol <= 1.2 * vol20
    if dn1 and dn2 and vol2:
        notes.append("❌ Tendance baissière (MA20<MA50 + volume faible)")
    else:
        notes.append("⚠️ Tendance neutre ou volume non significatif")
if rsi < 30:
    notes.append("🟢 RSI survendu (<30)")
elif rsi > 70:
    notes.append("🔴 RSI suracheté (>70)")
notes.append("🟢 MACD bullish" if macd > sig9 else "🔴 MACD bearish")
if last < bb_dn:
    notes.append("🟢 Sous bande inférieure")
elif last > bb_up:
    notes.append("🔴 Au-dessus bande supérieure")
b = sum(n.startswith("🟢") for n in notes)
s = sum(n.startswith("🔴") for n in notes)
advice = "🟢 ACHETER" if b > s else "🔴 VENDRE" if s > b else "🟡 ATTENDRE"
st.markdown(f"## {advice} maintenant")
for n in notes:
    st.markdown(f"- {n}")

st.subheader("⚖️ Stop-loss & Take-profit")
entry = last
st.markdown(f"- Entrée : {entry:.2f} USD")
st.markdown(f"- SL (-{exit_pct*100:.0f}%) : {entry*(1-exit_pct):.2f} USD")
st.markdown(f"- TP (+{exit_pct*200:.0f}%) : {entry*(1+exit_pct*2):.2f} USD")

@st.cache_data(ttl=24*3600)
def load_sp500():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    table = pd.read_html(url, header=0)[0]
    table = table[["Symbol", "Security", "GICS Sector"]]
    table.columns = ["Ticker", "Name", "Sector"]
    return table

sp500 = load_sp500()
sector = yf.Ticker(ticker).info.get("sector", "Inconnu")
cands = sp500[sp500["Sector"] == sector][["Ticker", "Name"]].to_dict("records")

st.subheader("✅ Top 5 opportunités sectorielles (scan parallèle)")
buy_list = []
progress = st.progress(0)

with ThreadPoolExecutor(max_workers=8) as executor:
    futures = {executor.submit(get_ticker_data, rec["Ticker"]): rec for rec in cands}
    total = len(futures)
    done = 0
    for fut in as_completed(futures):
        rec = futures[fut]
        sym, name = rec["Ticker"], rec["Name"]
        try:
            df = fut.result()
            if df.shape[0] < 60:
                continue
            m20v = float(df["Close"].rolling(20).mean().iloc[-1])
            m50v = float(df["Close"].rolling(50).mean().iloc[-1])
            v20v = float(df["Volume"].rolling(20).mean().iloc[-1])
            lastv = float(df["Close"].iloc[-1])
            volv = float(df["Volume"].iloc[-1])
            if lastv > m20v > m50v and volv >= 0.8 * v20v:
                pct = (lastv - m20v) / m20v * 100
                buy_list.append((sym, name, lastv, pct))
        except:
            pass
        done += 1
        progress.progress(done / total)

buy_list.sort(key=lambda x: x[3], reverse=True)
if buy_list:
    for sym, name, price, pct in buy_list[:5]:
        st.markdown(f"- **{sym}** — {name} : {price:.2f} USD ({pct:+.1f}% vs MA20)")
else:
    st.info("Aucune opportunité détectée.")
