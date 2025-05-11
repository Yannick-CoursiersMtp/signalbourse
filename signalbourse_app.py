import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import math

# 1) Config de la page
st.set_page_config(page_title="SignalBourse", layout="centered")

# 2) En-tête
st.title("📈 SignalBourse – Avis et Top 5 Opportunités")
st.markdown(
    "1️⃣ Entre un **ticker** pour obtenir ton signal et graphique  •  "
    "2️⃣ Je scanne le S&P 500 et affiche un **Top 5** d’ACHETER maintenant."
)

# 3) Champ ticker principal
ticker = st.text_input("Ton ticker principal :", "AAPL").upper().strip()
if not ticker:
    st.info("🔍 Commence par saisir un ticker.")
    st.stop()

# 4) Récupération et indicateurs du ticker principal (6 mois)
data = yf.download(ticker, period="6mo", interval="1d", progress=False)
if data.empty:
    st.error(f"❌ Historique introuvable pour « {ticker} ».")
    st.stop()
data["MA20"]     = data["Close"].rolling(20).mean()
data["MA50"]     = data["Close"].rolling(50).mean()
data["VolAvg20"] = data["Volume"].rolling(20).mean()

last  = float(data["Close"].iloc[-1])
ma20  = data["MA20"].iloc[-1]
ma50  = data["MA50"].iloc[-1]
vol   = int(data["Volume"].iloc[-1])
vol20 = data["VolAvg20"].iloc[-1]

# 5) Affichage graphique principal
st.subheader(f"📊 Graphique pour {ticker}")
fig, (ax1, ax2) = plt.subplots(2,1, figsize=(6,6), sharex=True)
ax1.plot(data.index, data["Close"], label="Cours", linewidth=2)
ax1.plot(data.index, data["MA20"], "--", label="MA20")
ax1.plot(data.index, data["MA50"], ":",  label="MA50")
ax1.legend()
ax2.plot(data.index, data["Volume"],      label="Volume", alpha=0.4)
ax2.plot(data.index, data["VolAvg20"],    label="Vol Moy20", color="orange")
ax2.legend()
st.pyplot(fig)

# 6) Signal principal
st.subheader("🚦 Ton signal")
if any(map(lambda x: pd.isna(x), (ma20, ma50, vol20))):
    st.warning("Données insuffisantes pour calculer ton signal.")
else:
    is_buy  = (last > ma20 and ma20 > ma50 and vol >= 0.8 * vol20)
    is_sell = (last < ma20 and ma20 < ma50 and vol <= 1.2 * vol20)
    if is_buy:
        st.success("🟢 ACHETER maintenant")
    elif is_sell:
        st.error("🔴 VENDRE maintenant")
    else:
        st.info("🟡 ATTENDRE")

    st.markdown(f"- **Prix actuel** : {last:.2f} USD") 
    pct20 = (last - ma20) / ma20 * 100
    st.markdown(f"- **Écart vs MA20** : {pct20:+.2f}%")
    st.markdown(f"- **Volume aujourd’hui** : {vol:,}  |  Moy20 : {int(vol20):,}")

# 7) Chargement S&P 500 (cache 24 h) avec le nom des sociétés
@st.cache_data(ttl=24*3600)
def load_sp500():
    url   = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    table = pd.read_html(url, header=0)[0]
    table = table[["Symbol","Security","GICS Sector"]]
    table.columns = ["Ticker","Name","Sector"]
    return table

sp500 = load_sp500()

# 8) Scan du S&P 500 pour Top 5 ACHETER avec le nom
st.subheader("✅ Top 5 opportunités dans ton secteur")
sector = yf.Ticker(ticker).info.get("sector","Inconnu")
candidates = sp500[sp500["Sector"]==sector][["Ticker","Name"]].to_dict("records")

buy_list = []
progress = st.progress(0)
for i, record in enumerate(candidates):
    sym, name = record["Ticker"], record["Name"]
    try:
        df = yf.download(sym, period="6mo", interval="1d", progress=False)
        if df.shape[0] < 60: 
            continue
        m20 = df["Close"].rolling(20).mean().iloc[-1]
        m50 = df["Close"].rolling(50).mean().iloc[-1]
        v   = int(df["Volume"].iloc[-1])
        v20 = df["Volume"].rolling(20).mean().iloc[-1]
        m20_f,m50_f,v20_f = float(m20), float(m50), float(v20)
        if math.isnan(m20_f) or math.isnan(m50_f) or math.isnan(v20_f):
            continue
        last_f = float(df["Close"].iloc[-1])
        if last_f > m20_f and m20_f > m50_f and v >= 0.8 * v20_f:
            pct = (last_f - m20_f) / m20_f * 100
            buy_list.append((sym, name, last_f, pct))
    except:
        pass
    progress.progress((i+1)/len(candidates))

# Trier et afficher
buy_list.sort(key=lambda x: x[3], reverse=True)
if buy_list:
    for sym, name, price, pct in buy_list[:5]:
        st.markdown(f"- **{sym}** — {name} : {price:.2f} USD  ({pct:+.1f}% vs MA20)")
else:
    st.info("Aucune opportunité d’achat pour l’instant.")
