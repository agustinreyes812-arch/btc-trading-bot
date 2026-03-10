import ccxt
import requests
import time
import statistics

# CONFIGURACION
SYMBOL = "BTC/USDT"
TIMEFRAME = "1m"

TELEGRAM_TOKEN = "TU_TOKEN_TELEGRAM"
TELEGRAM_CHAT_ID = "TU_CHAT_ID"

exchange = ccxt.binance()

# -----------------------------
# TELEGRAM
# -----------------------------

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje
    }
    try:
        requests.post(url, data=data)
    except:
        pass

# -----------------------------
# DATOS DE MERCADO
# -----------------------------

def obtener_velas():
    velas = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=120)
    return velas

# -----------------------------
# ANALISIS CONTEXTO (2 HORAS)
# -----------------------------

def analisis_contexto():

    velas = obtener_velas()

    highs = [v[2] for v in velas]
    lows = [v[3] for v in velas]
    volumes = [v[5] for v in velas]
    closes = [v[4] for v in velas]

    max_2h = max(highs)
    min_2h = min(lows)

    rango = max_2h - min_2h

    volatilidad = statistics.stdev(closes)
    volumen_promedio = statistics.mean(volumes)

    return {
        "max": max_2h,
        "min": min_2h,
        "rango": rango,
        "volumen": volumen_promedio,
        "volatilidad": volatilidad,
        "precio": closes[-1]
    }

# -----------------------------
# ANALISIS TACTICO (1-5 MIN)
# -----------------------------

def analisis_tactico():

    velas = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=5)

    cierre_actual = velas[-1][4]
    cierre_anterior = velas[-2][4]

    cambio_1m = cierre_actual - cierre_anterior

    cierre_5m = velas[0][4]

    cambio_5m = cierre_actual - cierre_5m

    volumen_actual = velas[-1][5]

    return {
        "cambio_1m": cambio_1m,
        "cambio_5m": cambio_5m,
        "volumen": volumen_actual
    }

# -----------------------------
# ORDER BOOK
# -----------------------------

def analizar_orderbook():

    orderbook = exchange.fetch_order_book(SYMBOL)

    bids = orderbook["bids"][:10]
    asks = orderbook["asks"][:10]

    volumen_bids = sum([b[1] for b in bids])
    volumen_asks = sum([a[1] for a in asks])

    return {
        "bids": volumen_bids,
        "asks": volumen_asks
    }

# -----------------------------
# OPEN INTEREST
# -----------------------------

def obtener_open_interest():

    try:

        url = "https://fapi.binance.com/fapi/v1/openInterest"
        params = {"symbol": "BTCUSDT"}

        r = requests.get(url, params=params)
        data = r.json()

        return float(data["openInterest"])

    except:
        return 0

# -----------------------------
# FUNDING RATE
# -----------------------------

def obtener_funding():

    try:

        url = "https://fapi.binance.com/fapi/v1/fundingRate"
        params = {"symbol": "BTCUSDT", "limit": 1}

        r = requests.get(url, params=params)
        data = r.json()

        return float(data[0]["fundingRate"])

    except:
        return 0

# -----------------------------
# MOTOR DE DECISION
# -----------------------------

def generar_senal():

    contexto = analisis_contexto()
    tactico = analisis_tactico()
    orderbook = analizar_orderbook()
    open_interest = obtener_open_interest()
    funding = obtener_funding()

    precio = contexto["precio"]

    cerca_min = precio <= contexto["min"] + contexto["rango"] * 0.2
    cerca_max = precio >= contexto["max"] - contexto["rango"] * 0.2

    presion_compra = orderbook["bids"] > orderbook["asks"]
    presion_venta = orderbook["asks"] > orderbook["bids"]

    momentum_up = tactico["cambio_1m"] > 0 and tactico["cambio_5m"] > 0
    momentum_down = tactico["cambio_1m"] < 0 and tactico["cambio_5m"] < 0

    if cerca_min and presion_compra and momentum_up:

        mensaje = f"""
POSIBLE LONG BTC

Precio: {precio}

Contexto: cerca soporte 2h
Momentum: alcista
OrderBook: compradores dominan

Open Interest: {open_interest}
Funding: {funding}
"""

        enviar_telegram(mensaje)

    elif cerca_max and presion_venta and momentum_down:

        mensaje = f"""
POSIBLE SHORT BTC

Precio: {precio}

Contexto: cerca resistencia 2h
Momentum: bajista
OrderBook: vendedores dominan

Open Interest: {open_interest}
Funding: {funding}
"""

        enviar_telegram(mensaje)

# -----------------------------
# LOOP PRINCIPAL
# -----------------------------

print("Bot iniciado...")

while True:

    try:

        generar_senal()

        time.sleep(30)

    except Exception as e:

        print("Error:", e)
        time.sleep(30)
