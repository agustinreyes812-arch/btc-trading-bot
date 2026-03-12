from flask import Flask, request
import requests
import os

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    requests.post(url, json=payload)


@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.json

    symbol = data.get("symbol")
    price = data.get("price")
    signal = data.get("signal")
    movement = data.get("movement")

    message = f"""
BTC TRADING BOT

Activo: {symbol}
Precio: {price}

Señal: {signal}
Movimiento esperado: {movement}%

Tipo: MICRO SCALPING
"""

    send_telegram(message)

    return {"status": "ok"}


@app.route("/")
def home():
    return "BOT ONLINE"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
