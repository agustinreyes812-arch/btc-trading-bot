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
# ANALISIS CONTEXTO (2H)
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
# ORDER BOOK
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
# OPEN INTEREST
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
# DETECTOR SWEEP
# =============================

def detectar_sweep():

    velas = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=10)

    lows = [v[3] for v in velas]
    highs = [v[2] for v in velas]

    ultimo_low = lows[-1]
    ultimo_high = highs[-1]

    min_anterior = min(lows[:-1])
    max_anterior = max(highs[:-1])

    sweep_abajo = ultimo_low < min_anterior
    sweep_arriba = ultimo_high > max_anterior

    return sweep_abajo, sweep_arriba

# =============================
# DETECTOR VOLUMEN ANOMALO
# =============================

def detectar_volumen_anomalo():

    velas = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=30)

    volumenes = [v[5] for v in velas]

    volumen_actual = volumenes[-1]

    volumen_promedio = sum(volumenes[:-1]) / (len(volumenes) - 1)

    return volumen_actual > volumen_promedio * 2

# =============================
# DETECTOR SQUEEZE
# =============================

def detectar_squeeze():

    velas = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=3)

    precio_actual = velas[-1][4]
    precio_anterior = velas[-2][4]

    movimiento = precio_actual - precio_anterior

    oi_actual, oi_cambio = obtener_open_interest_historial()

    if movimiento > 0 and oi_cambio < 0:

        return "SHORT SQUEEZE"

    if movimiento < 0 and oi_cambio < 0:

        return "LONG SQUEEZE"

    return "NONE"

# =============================
# ZONAS DE LIQUIDACION
# =============================

def detectar_zonas_liquidacion():

    velas = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=50)

    highs = [v[2] for v in velas]
    lows = [v[3] for v in velas]

    maximo = max(highs)
    minimo = min(lows)

    rango = maximo - minimo

    zona_liq_shorts = maximo + rango * 0.15
    zona_liq_longs = minimo - rango * 0.15

    return zona_liq_shorts, zona_liq_longs

# =============================
# MOTOR DE PROBABILIDAD
# =============================

def calcular_probabilidad(presion_compra, presion_venta, volumen_anomalo, sweep_abajo, sweep_arriba):

    score_long = 0
    score_short = 0

    if presion_compra:
        score_long += 1

    if presion_venta:
        score_short += 1

    if volumen_anomalo:
        score_long += 1
        score_short += 1

    if sweep_abajo:
        score_long += 2

    if sweep_arriba:
        score_short += 2

    total = score_long + score_short

    if total == 0:
        return 50, 50

    prob_long = int((score_long / total) * 100)
    prob_short = int((score_short / total) * 100)

    return prob_long, prob_short

# =============================
# MOTOR DE DECISION
# =============================

def generar_senal():

    contexto = analisis_contexto()

    tactico = analisis_tactico()

    orderbook = analizar_orderbook()

    oi_actual, oi_cambio = obtener_open_interest_historial()

    funding = obtener_funding()

    sweep_abajo, sweep_arriba = detectar_sweep()

    volumen_anomalo = detectar_volumen_anomalo()

    squeeze = detectar_squeeze()

    zona_short, zona_long = detectar_zonas_liquidacion()

    precio = contexto["precio"]

    presion_compra = orderbook["bids"] > orderbook["asks"]

    presion_venta = orderbook["asks"] > orderbook["bids"]

    prob_long, prob_short = calcular_probabilidad(
        presion_compra,
        presion_venta,
        volumen_anomalo,
        sweep_abajo,
        sweep_arriba
    )

    mensaje = f"""
BTC MARKET RADAR

Precio actual: {precio}

Probabilidad LONG: {prob_long}%
Probabilidad SHORT: {prob_short}%

Funding Rate: {funding}

Open Interest: {oi_actual}
Cambio OI: {oi_cambio}

Sweep abajo: {sweep_abajo}
Sweep arriba: {sweep_arriba}

Volumen institucional: {volumen_anomalo}

Squeeze detectado: {squeeze}

Zona liquidacion shorts: {zona_short}
Zona liquidacion longs: {zona_long}

Muro compra: {orderbook['muro_compra']}
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
