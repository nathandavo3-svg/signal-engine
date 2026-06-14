from flask import Flask, jsonify
import yfinance as yf
import pandas as pd
import numpy as np
import os

app = Flask(__name__)

# -----------------------
# INDICATORS
# -----------------------

def rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def atr(df, period=14):
    high_low = df["High"] - df["Low"]
    high_close = np.abs(df["High"] - df["Close"].shift())
    low_close = np.abs(df["Low"] - df["Close"].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def get_data(symbol):
    df = yf.download(symbol, period="5d", interval="15m")
    df = df.dropna()
    df["RSI"] = rsi(df["Close"])
    df["ATR"] = atr(df)
    df["MA20"] = df["Close"].rolling(20).mean()
    df["MA50"] = df["Close"].rolling(50).mean()
    return df


# -----------------------
# SIGNAL ENGINE
# -----------------------

def generate_signal(df):

    latest = df.iloc[-1]

    price = float(latest["Close"])
    rsi_val = float(latest["RSI"])
    atr_val = float(latest["ATR"])
    ma20 = float(latest["MA20"])
    ma50 = float(latest["MA50"])

    confidence = 50
    signal = "NO TRADE"

    # TREND
    if ma20 > ma50:
        confidence += 15
        trend = "UP"
    else:
        confidence += 15
        trend = "DOWN"

    # MOMENTUM
    if 40 < rsi_val < 65:
        confidence += 15

    # SIGNAL LOGIC
    if ma20 > ma50 and rsi_val > 45:
        signal = "BUY"
    elif ma20 < ma50 and rsi_val < 55:
        signal = "SELL"
    else:
        signal = "NO TRADE"

    # SL / TP (ATR based)
    if signal == "BUY":
        sl = price - (atr_val * 1.5)
        tp = price + (atr_val * 3)
    elif signal == "SELL":
        sl = price + (atr_val * 1.5)
        tp = price - (atr_val * 3)
    else:
        sl = tp = None

    confidence = min(max(confidence, 40), 90)

    return {
        "price": price,
        "rsi": rsi_val,
        "trend": trend,
        "signal": signal,
        "confidence": confidence,
        "stop_loss": sl,
        "take_profit": tp
    }


# -----------------------
# ROUTES
# -----------------------

@app.route("/")
def home():
    return jsonify({"status": "online"})


@app.route("/signals/gbpusd")
def gbpusd():
    df = get_data("GBPUSD=X")
    return jsonify(generate_signal(df))


@app.route("/signals/xauusd")
def xauusd():
    df = get_data("XAUUSD=X")
    return jsonify(generate_signal(df))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
