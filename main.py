from flask import Flask, jsonify
import yfinance as yf
import pandas as pd
import numpy as np
import os

app = Flask(__name__)

def get_data(symbol):
    data = yf.download(symbol, period="5d", interval="15m")
    data = data.dropna()
    return data

@app.route("/")
def home():
    return jsonify({"status": "online", "message": "signal engine running"})

@app.route("/signals")
def signals():

    gbp = get_data("GBPUSD=X")
    xau = get_data("XAUUSD=X")

    gbp_price = float(gbp["Close"].iloc[-1])
    xau_price = float(xau["Close"].iloc[-1])

    return jsonify({
        "GBPUSD": gbp_price,
        "XAUUSD": xau_price
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
