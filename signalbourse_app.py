import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# -------------------------------
# 1) Récupération et préparation des données
# -------------------------------
@st.cache_data(ttl=86400)
def get_data(ticker: str) -> pd.DataFrame:
    df = yf.download(ticker, period="2y", interval="1d")
    df["MA20"] = df["Close"].rolling(window=20).mean()
    df["MA50"] = df["Close"].rolling(window=50).mean()
    df["Vol20"] = df["Volume"].rolling(window=20).mean()
    df.dropna(inplace=True)  # on enlève toutes les dates incomplètes
    return df

# -------------------------------
# 2) Génération du signal clair
# -------------------------------
def generate_signal(df: pd.DataFrame) -> str:
    last, ma20, ma50 = df["Close"].iloc[-1], df["MA20"].iloc[-1], df["MA50"].iloc[-1]
    vol, vol20 = df["Volume"].iloc[-1], df["Vol20"].iloc[-1]

    if last > ma20 > ma50 and vol >= 0.8 * vol20:
        return "ACHETER"
    if last < ma20 < ma50 and vol >= 0.8 * vol20:
        return "VENDRE"
    return "ATTENDRE"

# -------------------------------
# 3) Backtest simple
# -------------------------------
def run_backtest(df: pd.DataFrame) -> dict:
    df = df.copy()
    df["Signal"] = (
        (df["Close"] > df["MA20"]) &
        (df["MA20"] > df["MA50"]) &
        (df["Volume"] >= 0.8 * df["Vol20"])
    )
    in_trade = False
    trades = []
    entry_price = None

    for i in range(len(df)):
        if df["Signal"].iloc[i] and not in_trade:
            entry_price = df["Close"].iloc[i]
            in_trade = True
        elif in_trade and not df["Signal"].iloc[i]:
            exit_price = df["Close"].iloc[i]
            trades.append((entry_price, exit_price))
            in_trade = False

    # Si on est encore positionné à la fin
    if in_trade:
        trades.append((entry_price, df["Close"].iloc[-1]))

    gains = [(exit - entry) / entry * 100 for entry, exit in trades]
    nb, wins = len(gains), sum(1 for g in gains if g > 0)
    win_rate = round(100 * wins / nb, 2) if nb else 0
    avg_gain = round(sum(gains) / nb, 2) if nb else 0
    return {"nb_trades": nb, "win_rate": win_rate, "avg_gain": avg_gain}

# -------------------------------
# 4) Affichage Streamlit
# -------------------------------
st.set_page_config(page_title="SignalBourse", layout="centered")
st.title("📈 SignalBourse – Analyse et Backtest")

ticker = st.text_input("Nom de l'action / Ticker :", value="AAPL")

if ticker:
    data = get_data(ticker)
    if data.empty:
        st.error("Pas de données pour ce ticker.")
    else:
        # ——— Graphique prix & MAs ———
        st.subheader("📊 Graphique Cours & Moyennes Mobiles")
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(data["Close"], label="Cours")
        ax.plot(data["MA20"], "--", label="MA20")
        ax.plot(data["MA50"], ":", label="MA50")
        ax.legend()
        st.pyplot(fig)

        # ——— Graphique Volume ———
        st.subheader("📈 Volume & Volume Moy.20j")
        fig2, ax2 = plt.subplots(figsize=(8, 2))
        # on fixe width numérique pour éviter le Timedelta non convertible
        ax2.bar(data.index, data["Volume"], width=0.8, alpha=0.3, label="Vol quotidien")
        ax2.plot(data["Vol20"], label="Vol Moy20", color="orange")
        ax2.legend()
        st.pyplot(fig2)

        # ——— Signal Clair ———
        signal = generate_signal(data)
        st.subheader("🚦 Signal Clair")
        col = {"ACHETER": "success", "VENDRE": "error", "ATTENDRE": "warning"}[signal]
        st.metric(label="Action à", value=signal, delta="")

        # ——— Backtest ———
        stats = run_backtest(data)
        st.subheader("🔄 Résultats du Backtest")
        st.write(f"- Nombre de trades : **{stats['nb_trades']}**")
        st.write(f"- Taux de succès : **{stats['win_rate']}%**")
        st.write(f"- Gain moyen par trade : **{stats['avg_gain']}%**")
