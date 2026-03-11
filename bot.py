import ccxt
import os

print("INICIANDO DIAGNOSTICO BINANCE...")

# =========================
# CARGAR VARIABLES
# =========================

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

print("Verificando variables...")

if API_KEY:
    print("API KEY detectada:", API_KEY[:6] + "******")
else:
    print("ERROR: API KEY no encontrada")

if API_SECRET:
    print("API SECRET detectada:", API_SECRET[:6] + "******")
else:
    print("ERROR: API SECRET no encontrada")

# =========================
# CONEXION BINANCE
# =========================

try:

    exchange = ccxt.binance({
        "apiKey": API_KEY,
        "secret": API_SECRET,
        "enableRateLimit": True
    })

    exchange.options["defaultType"] = "future"

    print("Intentando conectar con Binance...")

    balance = exchange.fetch_balance()

    print("CONEXION EXITOSA")

    if "USDT" in balance:
        print("Balance USDT:", balance["USDT"])

except Exception as e:

    print("ERROR CONECTANDO A BINANCE:")
    print(e)

# =========================
# PROBAR MERCADO
# =========================

try:

    ticker = exchange.fetch_ticker("BTC/USDT")

    print("Precio BTC:", ticker["last"])

except Exception as e:

    print("ERROR OBTENIENDO PRECIO:")
    print(e)

print("DIAGNOSTICO TERMINADO")
