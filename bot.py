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

def enviar_telegram(msg):

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg
    }

    try:
        requests.post(url, data=data)
    except:
        pass


# =========================
# OBTENER VELAS
# =========================

def velas(l):

    return exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=l)


# =========================
# CONTEXTO 2H
# =========================

def contexto():

    v = velas(120)

    highs = [x[2] for x in v]
    lows = [x[3] for x in v]
    closes = [x[4] for x in v]

    maximo = max(highs)
    minimo = min(lows)

    precio = closes[-1]

    media = statistics.mean(closes)

    tendencia = "NEUTRAL"

    if precio > media:
        tendencia = "ALCISTA"

    if precio < media:
        tendencia = "BAJISTA"

    return precio, maximo, minimo, tendencia


# =========================
# MOMENTUM
# =========================

def momentum():

    v = velas(5)

    cierre_actual = v[-1][4]
    cierre_prev = v[-2][4]

    cambio_1m = cierre_actual - cierre_prev
    cambio_5m = cierre_actual - v[0][4]

    return cambio_1m, cambio_5m


# =========================
# ORDERBOOK
# =========================

def orderbook():

    book = exchange.fetch_order_book(SYMBOL, limit=100)

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

        return 0,0


# =========================
# FUNDING
# =========================

def funding():

    try:

        url = "https://fapi.binance.com/fapi/v1/fundingRate"

        params = {"symbol":"BTCUSDT","limit":1}

        r = requests.get(url, params=params)

        data = r.json()

        return float(data[0]["fundingRate"])

    except:

        return 0


# =========================
# SWEEP
# =========================

def sweep():

    v = velas(10)

    highs = [x[2] for x in v]
    lows = [x[3] for x in v]

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

    v = velas(30)

    volumenes = [x[5] for x in v]

    promedio = statistics.mean(volumenes[:-1])
    actual = volumenes[-1]

    return actual > promedio * 2


# =========================
# TRAMPAS
# =========================

def trampas():

    v = velas(6)

    highs = [x[2] for x in v]
    lows = [x[3] for x in v]
    closes = [x[4] for x in v]

    bull_trap = False
    bear_trap = False

    if highs[-1] > max(highs[:-1]) and closes[-1] < closes[-2]:
        bull_trap = True

    if lows[-1] < min(lows[:-1]) and closes[-1] > closes[-2]:
        bear_trap = True

    return bull_trap, bear_trap


# =========================
# DIVERGENCIA PRECIO VS OI
# =========================

def divergencia():

    v = velas(3)

    precio_actual = v[-1][4]
    precio_prev = v[-2][4]

    oi_actual, oi_cambio = open_interest()

    mov = precio_actual - precio_prev

    if mov > 0 and oi_cambio < 0:
        return "SHORTS CERRANDO"

    if mov < 0 and oi_cambio < 0:
        return "LONGS CERRANDO"

    if mov > 0 and oi_cambio > 0:
        return "NUEVOS LONGS"

    if mov < 0 and oi_cambio > 0:
        return "NUEVOS SHORTS"

    return "NEUTRAL"


# =========================
# MAPA LIQUIDACIONES
# =========================

def mapa_liquidaciones():

    v = velas(80)

    highs = [x[2] for x in v]
    lows = [x[3] for x in v]

    maximo = max(highs)
    minimo = min(lows)

    rango = maximo - minimo

    zona_liq_short = maximo + rango * 0.25
    zona_liq_long = minimo - rango * 0.25

    return zona_liq_short, zona_liq_long


# =========================
# MODELO PROBABILIDAD
# =========================

def probabilidad():

    v = velas(200)

    closes = [x[4] for x in v]

    up = 0
    down = 0

    for i in range(1,len(closes)):

        if closes[i] > closes[i-1]:
            up += 1
        else:
            down += 1

    total = up + down

    prob_up = int((up/total)*100)
    prob_down = int((down/total)*100)

    return prob_up, prob_down


# =========================
# MOTOR DE PREDICCION
# =========================

def prediccion():

    c1,c5 = momentum()

    prob_up,prob_down = probabilidad()

    swu, swd = sweep()

    inst = volumen_institucional()

    score = 0

    if c1 > 0:
        score += 1

    if c5 > 0:
        score += 1

    if prob_up > prob_down:
        score += 1

    if swu:
        score += 1

    if inst:
        score += 1

    if score >= 4:
        return "FUERTE ALZA"

    if score == 3:
        return "ALZA PROBABLE"

    if score <= 2:
        return "BAJA PROBABLE"

    return "NEUTRAL"


# =========================
# REPORTE
# =========================

def reporte():

    precio,maximo,minimo,tendencia = contexto()

    c1,c5 = momentum()

    presion,muro_compra,muro_venta = orderbook()

    oi_actual,oi_cambio = open_interest()

    fund = funding()

    swu,swd = sweep()

    inst = volumen_institucional()

    bull,bear = trampas()

    div = divergencia()

    liq_short,liq_long = mapa_liquidaciones()

    prob_up,prob_down = probabilidad()

    pred = prediccion()

    msg = f"""

BTC FUTURES INTEL

Precio: {precio}

Tendencia 2H: {tendencia}

Predicción: {pred}

Prob subida: {prob_up}%
Prob bajada: {prob_down}%

Momentum 1m: {c1}
Momentum 5m: {c5}

Funding: {fund}

Open Interest: {oi_actual}
Cambio OI: {oi_cambio}

Divergencia: {div}

Sweep arriba: {swu}
Sweep abajo: {swd}

Volumen institucional: {inst}

Bull trap: {bull}
Bear trap: {bear}

Presión orderbook: {presion}

Muro compra: {muro_compra}
Muro venta: {muro_venta}

Zona liquidación shorts: {liq_short}
Zona liquidación longs: {liq_long}

"""

    enviar_telegram(msg)


# =========================
# LOOP
# =========================

print("BOT PROFESIONAL INICIADO")

while True:

    try:

        reporte()

        time.sleep(30)

    except Exception as e:

        print("Error:",e)

        time.sleep(30)
