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
# VELAS
# =============================

def obtener_velas(limite=200):

    velas = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=limite)

    return velas


# =============================
# CONTEXTO 2H
# =============================

def analisis_contexto():

    velas = obtener_velas(120)

    highs = [v[2] for v in velas]
    lows = [v[3] for v in velas]
    volumes = [v[5] for v in velas]
    closes = [v[4] for v in velas]

    max_2h = max(highs)
    min_2h = min(lows)

    rango = max_2h - min_2h

    volatilidad = statistics.stdev(closes)

    volumen_promedio = statistics.mean(volumes)

    precio = closes[-1]

    return {
        "max": max_2h,
        "min": min_2h,
        "rango": rango,
        "volumen": volumen_promedio,
        "volatilidad": volatilidad,
        "precio": precio
    }


# =============================
# MOMENTUM
# =============================

def analisis_tactico():

    velas = obtener_velas(5)

    cierre_actual = velas[-1][4]
    cierre_anterior = velas[-2][4]

    cambio_1m = cierre_actual - cierre_anterior

    cambio_5m = cierre_actual - velas[0][4]

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

    return volumen_bids, volumen_asks, muro_compra, muro_venta


# =============================
# OPEN INTEREST
# =============================

def obtener_open_interest():

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

        params = {"symbol": "BTCUSDT", "limit": 1}

        r = requests.get(url, params=params)

        data = r.json()

        return float(data[0]["fundingRate"])

    except:

        return 0


# =============================
# SWEEP
# =============================

def detectar_sweep():

    velas = obtener_velas(10)

    highs = [v[2] for v in velas]
    lows = [v[3] for v in velas]

    ultimo_high = highs[-1]
    ultimo_low = lows[-1]

    max_prev = max(highs[:-1])
    min_prev = min(lows[:-1])

    sweep_up = ultimo_high > max_prev
    sweep_down = ultimo_low < min_prev

    return sweep_up, sweep_down


# =============================
# VOLUMEN ANOMALO
# =============================

def detectar_volumen():

    velas = obtener_velas(30)

    volumenes = [v[5] for v in velas]

    promedio = statistics.mean(volumenes[:-1])

    actual = volumenes[-1]

    return actual > promedio * 2


# =============================
# SQUEEZE
# =============================

def detectar_squeeze():

    velas = obtener_velas(3)

    precio_actual = velas[-1][4]
    precio_anterior = velas[-2][4]

    oi_actual, oi_cambio = obtener_open_interest()

    movimiento = precio_actual - precio_anterior

    if movimiento > 0 and oi_cambio < 0:
        return "SHORT SQUEEZE"

    if movimiento < 0 and oi_cambio < 0:
        return "LONG SQUEEZE"

    return "NINGUNO"


# =============================
# ZONAS LIQUIDACION
# =============================

def zonas_liquidacion():

    velas = obtener_velas(50)

    highs = [v[2] for v in velas]
    lows = [v[3] for v in velas]

    maximo = max(highs)
    minimo = min(lows)

    rango = maximo - minimo

    zona_short = maximo + rango * 0.15
    zona_long = minimo - rango * 0.15

    return zona_short, zona_long


# =============================
# DIVERGENCIA PRECIO VS OI
# =============================

def divergencia_precio_oi():

    velas = obtener_velas(3)

    precio_actual = velas[-1][4]
    precio_anterior = velas[-2][4]

    oi_actual, oi_cambio = obtener_open_interest()

    movimiento = precio_actual - precio_anterior

    if movimiento > 0 and oi_cambio < 0:
        return "Subida por cierre de shorts"

    if movimiento < 0 and oi_cambio < 0:
        return "Caída por cierre de longs"

    if movimiento > 0 and oi_cambio > 0:
        return "Nuevos longs entrando"

    if movimiento < 0 and oi_cambio > 0:
        return "Nuevos shorts entrando"

    return "Neutral"


# =============================
# MODELO ESTADISTICO
# =============================

def modelo_probabilidad():

    velas = obtener_velas(200)

    closes = [v[4] for v in velas]

    subidas = 0
    bajadas = 0

    for i in range(1, len(closes)):

        if closes[i] > closes[i-1]:
            subidas += 1
        else:
            bajadas += 1

    total = subidas + bajadas

    prob_up = int((subidas / total) * 100)
    prob_down = int((bajadas / total) * 100)

    return prob_up, prob_down


# =============================
# MOTOR PRINCIPAL
# =============================

def generar_reporte():

    contexto = analisis_contexto()

    tactico = analisis_tactico()

    bids, asks, muro_compra, muro_venta = analizar_orderbook()

    oi_actual, oi_cambio = obtener_open_interest()

    funding = obtener_funding()

    sweep_up, sweep_down = detectar_sweep()

    volumen = detectar_volumen()

    squeeze = detectar_squeeze()

    zona_short, zona_long = zonas_liquidacion()

    divergencia = divergencia_precio_oi()

    prob_up, prob_down = modelo_probabilidad()

    precio = contexto["precio"]

    mensaje = f"""

BTC MARKET RADAR

Precio actual: {precio}

Probabilidad subida: {prob_up}%
Probabilidad bajada: {prob_down}%

Funding: {funding}

Open Interest: {oi_actual}
Cambio OI: {oi_cambio}

Sweep arriba: {sweep_up}
Sweep abajo: {sweep_down}

Volumen institucional: {volumen}

Squeeze: {squeeze}

Divergencia: {divergencia}

Zona liquidacion shorts: {zona_short}
Zona liquidacion longs: {zona_long}

Muro compra: {muro_compra}
Muro venta: {muro_venta}

"""

    enviar_telegram(mensaje)


# =============================
# LOOP
# =============================

print("BOT INICIADO")

while True:

    try:

        generar_reporte()

        time.sleep(30)

    except Exception as e:

        print("Error:", e)

        time.sleep(30)
