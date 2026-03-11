import os
import ccxt

print("INICIO DIAGNOSTICO")

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

print("API_KEY:", API_KEY)
print("API_SECRET:", API_SECRET)

exchange = ccxt.binance({
    "apiKey": API_KEY,
    "secret": API_SECRET,
    "enableRateLimit": True
})

try:
    balance = exchange.fetch_balance()
    print("CONEXION EXITOSA")
    print(balance)

except Exception as e:
    print("ERROR BINANCE:")
    print(e)
