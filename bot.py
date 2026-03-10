import ccxt
import requests
import time
import statistics

# =============================
# CONFIGURACION
# =============================

SYMBOL = "BTC/USDT"
TIMEFRAME = "1m"

TELEGRAM_TOKEN = "TU_TOKEN"
TELEGRAM_CHAT_ID = "TU_CHAT_ID"

exchange = ccxt.binance()

# =============================
# TELEGRAM
# =============================

def enviar_telegram(mensaje):

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensaje
        }

        requests.post(url, data=data)

    except:
        pass

# =============================
# OBTENER VELAS
# =============================

def obtener_velas():

    velas = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=120)

    return velas

# =============================
# ANALISIS CONTEXTO 2 HORAS
# =============================

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

    precio_actual = closes[-1]

    return {
        "max": max_2h,
        "min": min_2h,
        "rango": rango,
        "volumen": volumen_promedio,
        "volatilidad": volatilidad,
        "precio": precio_actual
    }

# =============================
# ANALISIS TACTICO
# =============================

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

# =============================
# ORDER BOOK PROFUNDO
# =============================

def analizar_orderbook():

    orderbook = exchange.fetch_order_book(SYMBOL, limit=50)

    bids = orderbook["bids"]
    asks = orderbook["asks"]

    volumen_bids = sum([b[1] for b in bids])
    volumen_asks = sum([a[1] for a in asks])

    muro_compra = max(bids, key=lambda x: x[1])
    muro_venta = max(asks, key=lambda x: x[1])

    return {
        "bids": volumen_bids,
        "asks": volumen_asks,
        "muro_compra": muro_compra,
        "muro_venta": muro_venta
    }

# =============================
# OPEN INTEREST ACTUAL
# =============================

def obtener_open_interest():

    try:

        url = "https://fapi.binance.com/fapi/v1/openInterest"

        params = {"symbol": "BTCUSDT"}

        r = requests.get(url, params=params)

        data = r.json()

        return float(data["openInterest"])

    except:

        return 0

# =============================
# OPEN INTEREST HISTORICO
# =============================

def obtener_open_interest_historial():

    try:

        url = "https://fapi.binance.com/futures/data/openInterestHist"

        params = {
            "symbol": "BTCUSDT",
            "period": "5m",
            "limit": 2
        }

        r = requests.get(url, params=params)

        data = r.json()

        actual = float(data[-1]["sumOpenInterest"])
        anterior = float(data[-2]["sumOpenInterest"])

        cambio = actual - anterior

        return actual, cambio

    except:

        return 0, 0

# =============================
# FUNDING RATE
# =============================

def obtener_funding():

    try:

        url = "https://fapi.binance.com/fapi/v1/fundingRate"

        params = {
            "symbol": "BTCUSDT",
            "limit": 1
        }

        r = requests.get(url, params=params)

        data = r.json()

        return float(data[0]["fundingRate"])

    except:

        return 0

# =============================
# MOTOR DE DECISION
# =============================

def generar_senal():

    contexto = analisis_contexto()

    tactico = analisis_tactico()

    orderbook = analizar_orderbook()

    oi_actual, oi_cambio = obtener_open_interest_historial()

    funding = obtener_funding()

    precio = contexto["precio"]

    cerca_min = precio <= contexto["min"] + contexto["rango"] * 0.2

    cerca_max = precio >= contexto["max"] - contexto["rango"] * 0.2

    presion_compra = orderbook["bids"] > orderbook["asks"]

    presion_venta = orderbook["asks"] > orderbook["bids"]

    momentum_up = tactico["cambio_1m"] > 0 and tactico["cambio_5m"] > 0

    momentum_down = tactico["cambio_1m"] < 0 and tactico["cambio_5m"] < 0

    oi_subiendo = oi_cambio > 0

    # LONG

    if cerca_min and presion_compra and momentum_up and oi_subiendo:

        mensaje = f"""
POSIBLE LONG BTC

Precio: {precio}

Contexto: soporte 2h
Momentum: alcista
Compradores dominan orderbook

Open Interest: {oi_actual}
Cambio OI: {oi_cambio}

Funding: {funding}

Muro compra: {orderbook['muro_compra']}
"""

        enviar_telegram(mensaje)

    # SHORT

    elif cerca_max and presion_venta and momentum_down and oi_subiendo:

        mensaje = f"""
POSIBLE SHORT BTC

Precio: {precio}

Contexto: resistencia 2h
Momentum: bajista
Vendedores dominan orderbook

Open Interest: {oi_actual}
Cambio OI: {oi_cambio}

Funding: {funding}

Muro venta: {orderbook['muro_venta']}
"""

        enviar_telegram(mensaje)

# =============================
# LOOP PRINCIPAL
# =============================

print("BOT INICIADO")

while True:

    try:

        generar_senal()

        time.sleep(30)

    except Exception as e:

        print("Error:", e)

        time.sleep(30)
