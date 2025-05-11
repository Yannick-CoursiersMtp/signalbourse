import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import json

st.set_page_config(page_title="SignalBourse", layout="wide")

# Chargement des secteurs depuis le fichier JSON
with open("sector_tickers.json", "r") as f:
    sector_map = json.load(f)

st.title("📈 SignalBourse – Analyse et Backtest")
ticker = st.text_input("Nom de l'action / Ticker :", value="AAPL").upper()

if ticker:
    # 1) Récupération des données 2 ans
    data = yf.download(ticker, period="2y", interval="1d")
    if data.empty:
        st.error(f"Aucune donnée trouvée pour « {ticker} »")
        st.stop()

    # Calcul des moyennes mobiles 20j et 50j et volume moyen 20j
    data["MA20"] = data["Close"].rolling(window=20).mean()
    data["MA50"] = data["Close"].rolling(window=50).mean()
    data["Vol20"] = data["Volume"].rolling(window=20).mean()

    # 2) Graphique prix + moyennes
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(data.index, data["Close"], label="Cours", linewidth=1)
    ax.plot(data.index, data["MA20"], "--", label="MA20")
    ax.plot(data.index, data["MA50"], ":", label="MA50")
    ax.legend(loc="upper left")
    ax.set_title("Cours & Moyennes Mobiles")
    st.pyplot(fig)

    # 3) Graphique volume + volume moyen
    fig2, ax2 = plt.subplots(figsize=(8, 2.5))
    ax2.bar(data.index, data["Volume"], 0.8, alpha=0.3, label="Volume quotidien")
    ax2.plot(data.index, data["Vol20"], label="Vol Moy20", color="orange")
    ax2.legend(loc="upper left")
    ax2.set_title("Volume & Volume Moy. 20j")
    st.pyplot(fig2)

    # Dernières valeurs
    last = data["Close"].iloc[-1]
    ma20 = data["MA20"].iloc[-1]
    ma50 = data["MA50"].iloc[-1]
    vol = data["Volume"].iloc[-1]
    v20 = data["Vol20"].iloc[-1]

    # 4) Signal simple
    signal = "ATTENDRE"
    if pd.notna(last) and pd.notna(ma20) and pd.notna(ma50):
        if last > ma20 > ma50:
            signal = "ACHETER"
        elif last < ma20 < ma50:
            signal = "VENDRE"
    st.subheader("🚦 Ton signal")
    st.info(f"**{signal}** maintenant")

    # 5) Détails numériques
    st.markdown(f"- **Prix actuel** : {last:.2f} USD")
    st.markdown(f"- **Écart vs MA20** : {(last/ma20-1)*100:+.2f}%")
    st.markdown(f"- **Volume aujourd’hui** : {vol:,} | Moy20 : {v20:,.0f}")

    # 6) Top 5 opportunités secteur
    # 6.1) Détection du secteur
    secteur = None
    for sec, symbols in sector_map.items():
        if ticker in symbols:
            secteur = sec
            break
    st.subheader(f"✅ Top 5 opportunités dans « {secteur or '—'} »")
    if secteur is None:
        st.write("Secteur non référencé.")
    else:
        # Pour chaque symbole du secteur, calculer %écart MA20
        df_sec = pd.DataFrame()
        for sym in sector_map[secteur]:
            d = yf.download(sym, period="1mo", interval="1d")[["Close", "Volume"]]
            if len(d) < 20: continue
            m20 = d["Close"].rolling(20).mean().iloc[-1]
            if pd.isna(m20): continue
            pct = (d["Close"].iloc[-1]/m20 - 1)*100
            df_sec.loc[sym, "pct"] = pct
            df_sec.loc[sym, "price"] = d["Close"].iloc[-1]
        df_top = df_sec.sort_values("pct", ascending=False).head(5)
        if df_top.empty:
            st.write("Aucune opportunité détectée.")
        else:
            for sym, row in df_top.iterrows():
                st.markdown(f"- **{sym}** : {row['price']:.2f} USD ({row['pct']:+.1f}% vs MA20)")

    # 7) Backtest MA20/MA50 + volume
    def run_backtest(df):
        df = df.copy().reset_index()
        df["signal"] = 0
        for i in range(1, len(df)):
            if df.loc[i, "Close"] > df.loc[i, "MA20"] > df.loc[i, "MA50"] and df.loc[i, "Volume"] >= df.loc[i, "Vol20"]:
                df.loc[i, "signal"] = 1  # acheter
            elif df.loc[i, "Close"] < df.loc[i, "MA20"] < df.loc[i, "MA50"]:
                df.loc[i, "signal"] = -1  # vendre
        df["position"] = df["signal"].replace(0, method="ffill")
        df["returns"] = df["Close"].pct_change() * df["position"].shift(1)
        return df

    bt = run_backtest(data)
    cumret = (1 + bt["returns"].dropna()).cumprod() - 1
    fig3, ax3 = plt.subplots(figsize=(8, 3))
    ax3.plot(bt["Date"], cumret * 100, label="Performance Backtest (%)")
    ax3.set_title("Résultats du backtest (%)")
    ax3.legend()
    st.pyplot(fig3)
