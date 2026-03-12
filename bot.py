# BOT DE ALERTAS TRADINGVIEW → TELEGRAM
# Funciona en Railway
# No usa Binance, solo recibe señales y te avisa

from flask import Flask, request
import requests
import os

app = Flask(__name__)

# Variables de entorno (configuradas en Railway)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(message):

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }

    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("Error enviando mensaje:", e)


@app.route("/")
def home():
    return "BOT DE ALERTAS ACTIVO"


@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.json

    pair = data.get("pair", "N/A")
    signal = data.get("signal", "N/A")
    price = data.get("price", "N/A")
    timeframe = data.get("timeframe", "N/A")

    message = f"""
🚨 TRADING ALERT

Par: {pair}
Señal: {signal}
Precio: {price}
Temporalidad: {timeframe}
"""

    print(message)

    send_telegram(message)

    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
