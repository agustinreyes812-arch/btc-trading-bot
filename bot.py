import ccxt
import requests
import time
import statistics
import math

# =========================
# CONFIG
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

def enviar(msg):

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
# VELAS
# =========================

def velas(n):

    return exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=n)


# =========================
# CONTEXTO 2H
# =========================

def contexto():

    v = velas(120)

    closes = [x[4] for x in v]

    precio = closes[-1]

    media = statistics.mean(closes)

    if precio > media:
        tendencia = "ALCISTA"
    elif precio < media:
        tendencia = "BAJISTA"
    else:
        tendencia = "NEUTRAL"

    return precio, tendencia


# =========================
# MOMENTUM
# =========================

def momentum():

    v = velas(5)

    c1 = v[-1][4] - v[-2][4]
    c5 = v[-1][4] - v[0][4]

    return c1, c5


# =========================
# ORDERBOOK
# =========================

def orderbook():

    book = exchange.fetch_order_book(SYMBOL, limit=100)

    bids = book["bids"]
    asks = book["asks"]

    vol_bids = sum([b[1] for b in bids])
    vol_asks = sum([a[1] for a in asks])

    presion = "NEUTRAL"

    if vol_bids > vol_asks:
        presion = "COMPRADORES"

    if vol_asks > vol_bids:
        presion = "VENDEDORES"

    return presion


# =========================
# OPEN INTEREST
# =========================

def open_interest():

    try:

        url = "https://fapi.binance.com/futures/data/openInterestHist"

        params = {
            "symbol":"BTCUSDT",
            "period":"5m",
            "limit":2
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
# SWEEP
# =========================

def sweep():

    v = velas(12)

    highs = [x[2] for x in v]
    lows = [x[3] for x in v]

    if highs[-1] > max(highs[:-1]):
        return "SHORT_LIQUIDITY"

    if lows[-1] < min(lows[:-1]):
        return "LONG_LIQUIDITY"

    return "NONE"


# =========================
# VOLUMEN INSTITUCIONAL
# =========================

def volumen_institucional():

    v = velas(30)

    vols = [x[5] for x in v]

    promedio = statistics.mean(vols[:-1])

    return vols[-1] > promedio * 2


# =========================
# MACHINE LEARNING SIMPLE
# =========================

def modelo_ml():

    v = velas(300)

    closes = [x[4] for x in v]

    cambios = []

    for i in range(1,len(closes)):

        cambios.append(closes[i] - closes[i-1])

    media = statistics.mean(cambios)

    desviacion = statistics.stdev(cambios)

    ultimo_cambio = cambios[-1]

    z = (ultimo_cambio - media) / desviacion if desviacion != 0 else 0

    prob_up = 1 / (1 + math.exp(-z))

    prob_down = 1 - prob_up

    return round(prob_up*100), round(prob_down*100)


# =========================
# MOTOR PREDICCION
# =========================

def prediccion():

    c1,c5 = momentum()

    prob_up,prob_down = modelo_ml()

    presion = orderbook()

    inst = volumen_institucional()

    score = 0

    if c1 > 0:
        score += 1

    if c5 > 0:
        score += 1

    if prob_up > prob_down:
        score += 1

    if presion == "COMPRADORES":
        score += 1

    if inst:
        score += 1

    if score >= 4:
        return "LONG SCALP"

    if score <= 2:
        return "SHORT SCALP"

    return "NEUTRAL"


# =========================
# REPORTE
# =========================

def reporte():

    precio,tendencia = contexto()

    presion = orderbook()

    oi,oi_cambio = open_interest()

    sw = sweep()

    inst = volumen_institucional()

    prob_up,prob_down = modelo_ml()

    pred = prediccion()

    msg = f"""

BTC AI TRADING RADAR

Precio: {precio}

Tendencia 2H: {tendencia}

Predicción: {pred}

Prob subida (ML): {prob_up}%
Prob bajada (ML): {prob_down}%

Presión orderbook: {presion}

Sweep liquidez: {sw}

Open Interest: {oi}
Cambio OI: {oi_cambio}

Volumen institucional: {inst}

"""

    enviar(msg)


# =========================
# LOOP
# =========================

print("BOT AI TRADING INICIADO")

while True:

    try:

        reporte()

        time.sleep(30)

    except Exception as e:

        print("Error:",e)

        time.sleep(30)
