import os
import ccxt

print("BOT INICIADO")

api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")

exchange = ccxt.binance({
    "apiKey": api_key,
    "secret": api_secret,
    "enableRateLimit": True,
    "options": {
        "defaultType": "future"   # MUY IMPORTANTE
    }
})

try:
    balance = exchange.fetch_balance()
    print("CONEXION EXITOSA")
    print(balance)

except Exception as e:
    print("ERROR:", e)
