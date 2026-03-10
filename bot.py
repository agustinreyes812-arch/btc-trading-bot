import ccxt
import requests
import time
import statistics

# =========================
# CONFIGURACION
# =========================

SYMBOL = "BTC/USDT"
TIMEFRAME = "1m"

TELEGRAM_TOKEN = "TU_TOKEN"
TELEGRAM_CHAT_ID = "TU_CHAT_ID"

exchange = ccxt.binance({
    "enableRateLimit": True
})

# =========================
# TELEGRAM
# =========================

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


# =========================
# VELAS
# =========================

def obtener_velas(limite):

    velas = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=limite)

    return velas


# =========================
# CONTEXTO 2 HORAS
# =========================

def contexto_mercado():

    velas = obtener_velas(120)

    highs = [v[2] for v in velas]
    lows = [v[3] for v in velas]
    closes = [v[4] for v in velas]
    volumes = [v[5] for v in velas]

    maximo = max(highs)
    minimo = min(lows)

    rango = maximo - minimo

    volatilidad = statistics.stdev(closes)

    volumen_prom = statistics.mean(volumes)

    precio = closes[-1]

    tendencia = "NEUTRAL"

    if precio > statistics.mean(closes):
        tendencia = "ALCISTA"

    if precio < statistics.mean(closes):
        tendencia = "BAJISTA"

    return precio, maximo, minimo, volatilidad, volumen_prom, tendencia


# =========================
# MOMENTUM
# =========================

def momentum():

    velas = obtener_velas(5)

    cierre_actual = velas[-1][4]
    cierre_anterior = velas[-2][4]

    cambio_1m = cierre_actual - cierre_anterior
    cambio_5m = cierre_actual - velas[0][4]

    volumen = velas[-1][5]

    return cambio_1m, cambio_5m, volumen


# =========================
# ORDER BOOK
# =========================

def analizar_orderbook():

    book = exchange.fetch_order_book(SYMBOL, limit=50)

    bids = book["bids"]
    asks = book["asks"]

    volumen_bids = sum([b[1] for b in bids])
    volumen_asks = sum([a[1] for a in asks])

    muro_compra = max(bids, key=lambda x: x[1])
    muro_venta = max(asks, key=lambda x: x[1])

    presion = "NEUTRAL"

    if volumen_bids > volumen_asks:
        presion = "COMPRADORES"

    if volumen_asks > volumen_bids:
        presion = "VENDEDORES"

    return presion, muro_compra, muro_venta


# =========================
# OPEN INTEREST
# =========================

def open_interest():

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


# =========================
# FUNDING RATE
# =========================

def funding_rate():

    try:

        url = "https://fapi.binance.com/fapi/v1/fundingRate"

        params = {"symbol": "BTCUSDT", "limit": 1}

        r = requests.get(url, params=params)

        data = r.json()

        return float(data[0]["fundingRate"])

    except:

        return 0


# =========================
# LIQUIDITY SWEEP
# =========================

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


# =========================
# VOLUMEN INSTITUCIONAL
# =========================

def volumen_institucional():

    velas = obtener_velas(30)

    volumenes = [v[5] for v in velas]

    promedio = statistics.mean(volumenes[:-1])
    actual = volumenes[-1]

    return actual > promedio * 2


# =========================
# ZONAS DE LIQUIDACION
# =========================

def zonas_liquidacion():

    velas = obtener_velas(60)

    highs = [v[2] for v in velas]
    lows = [v[3] for v in velas]

    maximo = max(highs)
    minimo = min(lows)

    rango = maximo - minimo

    zona_short = maximo + rango * 0.2
    zona_long = minimo - rango * 0.2

    return zona_short, zona_long


# =========================
# MODELO ESTADISTICO
# =========================

def probabilidad():

    velas = obtener_velas(200)

    closes = [v[4] for v in velas]

    up = 0
    down = 0

    for i in range(1, len(closes)):

        if closes[i] > closes[i-1]:
            up += 1
        else:
            down += 1

    total = up + down

    prob_up = int((up/total)*100)
    prob_down = int((down/total)*100)

    return prob_up, prob_down


# =========================
# PREDICCION FINAL
# =========================

def prediccion():

    cambio_1m, cambio_5m, volumen = momentum()

    prob_up, prob_down = probabilidad()

    sweep_up, sweep_down = detectar_sweep()

    institucion = volumen_institucional()

    score = 0

    if cambio_1m > 0:
        score += 1

    if cambio_5m > 0:
        score += 1

    if prob_up > prob_down:
        score += 1

    if sweep_up:
        score += 1

    if institucion:
        score += 1

    if score >= 3:
        return "ALZA PROBABLE"

    if score <= 2:
        return "BAJA PROBABLE"

    return "NEUTRAL"


# =========================
# REPORTE
# =========================

def generar_reporte():

    precio, maximo, minimo, volatilidad, volumen_prom, tendencia = contexto_mercado()

    cambio_1m, cambio_5m, volumen = momentum()

    presion, muro_compra, muro_venta = analizar_orderbook()

    oi_actual, oi_cambio = open_interest()

    funding = funding_rate()

    sweep_up, sweep_down = detectar_sweep()

    institucional = volumen_institucional()

    zona_short, zona_long = zonas_liquidacion()

    prob_up, prob_down = probabilidad()

    pred = prediccion()

    mensaje = f"""

BTC FUTURES RADAR

Precio: {precio}

Tendencia 2H: {tendencia}

Prob subida: {prob_up}%
Prob bajada: {prob_down}%

Predicción: {pred}

Momentum 1m: {cambio_1m}
Momentum 5m: {cambio_5m}

Funding: {funding}

Open Interest: {oi_actual}
Cambio OI: {oi_cambio}

Sweep arriba: {sweep_up}
Sweep abajo: {sweep_down}

Volumen institucional: {institucional}

Presión orderbook: {presion}

Muro compra: {muro_compra}
Muro venta: {muro_venta}

Zona liquidación shorts: {zona_short}
Zona liquidación longs: {zona_long}

"""

    enviar_telegram(mensaje)


# =========================
# LOOP
# =========================

print("BOT DE TRADING INICIADO")

while True:

    try:

        generar_reporte()

        time.sleep(30)

    except Exception as e:

        print("Error:", e)

        time.sleep(30)
