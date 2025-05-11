import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# -------------------------------
# Fonction backtest
# -------------------------------
def run_backtest(data):
    data = data.copy()
    data["MA20"] = data["Close"].rolling(window=20).mean()
    data["MA50"] = data["Close"].rolling(window=50).mean()
    data["Vol20"] = data["Volume"].rolling(window=20).mean()

    data["Signal"] = (
        (data["Close"] > data["MA20"])
        & (data["MA20"] > data["MA50"])
        & (data["Volume"] > data["Vol20"])
    )

    trades = []
    in_trade = False
    entry_price = 0

    for i in range(1, len(data)):
        if data["Signal"].iloc[i] and not in_trade:
            entry_price = data["Close"].iloc[i]
            in_trade = True
        elif in_trade and not data["Signal"].iloc[i]:
            exit_price = data["Close"].iloc[i]
            trades.append((entry_price, exit_price))
            in_trade = False

    if in_trade:
        trades.append((entry_price, data["Close"].iloc[-1]))

    gains = [round((exit - entry) / entry * 100, 2) for entry, exit in trades]
    win_rate = round(100 * sum([g > 0 for g in gains]) / len(gains), 2) if gains else 0
    avg_gain = round(sum(gains) / len(gains), 2) if gains else 0
    profit_factor = round(
        sum([g for g in gains if g > 0]) / -sum([g for g in gains if g < 0]), 2
    ) if any(g < 0 for g in gains) else "Infini"

    score = round(win_rate * 0.5 + avg_gain * 0.5, 2)
    return {
        "nb_trades": len(gains),
        "win_rate": win_rate,
        "avg_gain": avg_gain,
        "profit_factor": profit_factor,
        "score": score
    }

# -------------------------------
# Interface principale
# -------------------------------
st.set_page_config(page_title="SignalBourse", layout="centered")
st.title("📈 SignalBourse – Backtest sur 2 ans")

ticker = st.text_input("Nom de l'action / Ticker :", value="AAPL")

if ticker:
    data = yf.download(ticker, period="2y", interval="1d")

    if data.empty:
        st.error("Aucune donnée pour ce ticker.")
    else:
        st.subheader("Graphique")
        ma20 = data["Close"].rolling(20).mean()
        ma50 = data["Close"].rolling(50).mean()

        fig, ax = plt.subplots()
        ax.plot(data.index, data["Close"], label="Cours")
        ax.plot(data.index, ma20, label="MA20", linestyle="--")
        ax.plot(data.index, ma50, label="MA50", linestyle=":")
        ax.legend()
        st.pyplot(fig)

        st.subheader("Résultats du backtest (stratégie MA20/MA50 + volume)")
        resultats = run_backtest(data)

        st.markdown(f"""
        - **Nombre de trades** : {resultats['nb_trades']}
        - **Taux de succès** : {resultats['win_rate']} %
        - **Gain moyen par trade** : {resultats['avg_gain']} %
        - **Profit factor** : {resultats['profit_factor']}
        - **Score de l’opportunité** : {resultats['score']} / 100
        """)
