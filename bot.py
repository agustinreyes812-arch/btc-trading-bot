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

    precio = closes[-1]

    media = statistics.mean(closes)

    tendencia = "NEUTRAL"

    if precio > media:
        tendencia = "ALCISTA"

    if precio < media:
        tendencia = "BAJISTA"

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

    return presion, bids, asks


# =========================
# DETECTOR DE BALLENAS
# =========================

def detectar_ballenas():

    presion, bids, asks = orderbook()

    whale_buy = None
    whale_sell = None

    for b in bids:

        if b[1] > 50:   # tamaño grande BTC
            whale_buy = b
            break

    for a in asks:

        if a[1] > 50:
            whale_sell = a
            break

    return whale_buy, whale_sell


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
# FUNDING RATE
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

    if highs[-1] > max(highs[:-1]):
        return "SWEEP SHORTS"

    if lows[-1] < min(lows[:-1]):
        return "SWEEP LONGS"

    return "NINGUNO"


# =========================
# VOLUMEN INSTITUCIONAL
# =========================

def volumen_institucional():

    v = velas(30)

    vols = [x[5] for x in v]

    promedio = statistics.mean(vols[:-1])

    if vols[-1] > promedio * 2:
        return True

    return False


# =========================
# MANIPULACION
# =========================

def manipulacion():

    c1, c5 = momentum()

    inst = volumen_institucional()

    if abs(c1) > 50 and inst:
        return "POSIBLE MANIPULACION"

    return "NORMAL"


# =========================
# PROBABILIDAD
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

    return int(up/total*100), int(down/total*100)


# =========================
# PREDICCION
# =========================

def prediccion():

    c1,c5 = momentum()

    prob_up,prob_down = probabilidad()

    sweep_signal = sweep()

    inst = volumen_institucional()

    score = 0

    if c1 > 0:
        score += 1

    if c5 > 0:
        score += 1

    if prob_up > prob_down:
        score += 1

    if sweep_signal == "SWEEP SHORTS":
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

    precio,tendencia = contexto()

    presion,bids,asks = orderbook()

    whale_buy,whale_sell = detectar_ballenas()

    oi,oi_cambio = open_interest()

    fund = funding()

    sweep_signal = sweep()

    inst = volumen_institucional()

    manip = manipulacion()

    prob_up,prob_down = probabilidad()

    pred = prediccion()

    msg = f"""

BTC FUTURES AI RADAR

Precio: {precio}

Tendencia 2H: {tendencia}

Predicción: {pred}

Prob subida: {prob_up}%
Prob bajada: {prob_down}%

Funding: {fund}

Open Interest: {oi}
Cambio OI: {oi_cambio}

Sweep: {sweep_signal}

Volumen institucional: {inst}

Manipulación: {manip}

Ballena compra: {whale_buy}

Ballena venta: {whale_sell}

Presión del mercado: {presion}

"""

    enviar_telegram(msg)


# =========================
# LOOP
# =========================

print("BOT CUANTITATIVO INICIADO")

while True:

    try:

        reporte()

        time.sleep(30)

    except Exception as e:

        print("Error:", e)

        time.sleep(30)
