import ccxt
import os

print("INICIANDO PRUEBA BINANCE")

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

print("API KEY:", API_KEY[:6] if API_KEY else "None")

exchange = ccxt.binance({
    "apiKey": API_KEY,
    "secret": API_SECRET,
    "enableRateLimit": True
})

exchange.options["defaultType"] = "future"

try:

    balance = exchange.fetch_balance()

    print("CONEXION EXITOSA")
    print(balance["USDT"])

except Exception as e:

    print("ERROR:")
    print(e)
