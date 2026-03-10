import ccxt
import requests
import time
import statistics
import math

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
# CONTEXTO
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

    v = velas(6)

    cambio1 = v[-1][4] - v[-2][4]
    cambio5 = v[-1][4] - v[0][4]

    return cambio1, cambio5


# =========================
# ORDER BOOK
# =========================

def orderbook():

    book = exchange.fetch_order_book(SYMBOL, limit=100)

    bids = book["bids"]
    asks = book["asks"]

    vol_bids = sum([b[1] for b in bids])
    vol_asks = sum([a[1] for a in asks])

    if vol_bids > vol_asks:
        return "COMPRADORES"

    if vol_asks > vol_bids:
        return "VENDEDORES"

    return "NEUTRAL"


# =========================
# SWEEP LIQUIDEZ
# =========================

def sweep():

    v = velas(15)

    highs = [x[2] for x in v]
    lows = [x[3] for x in v]

    if highs[-1] > max(highs[:-1]):

        return "LIQUIDAR SHORTS"

    if lows[-1] < min(lows[:-1]):

        return "LIQUIDAR LONGS"

    return "NINGUNO"


# =========================
# ZONAS INSTITUCIONALES
# =========================

def zonas_institucionales():

    v = velas(80)

    highs = [x[2] for x in v]
    lows = [x[3] for x in v]

    zona_alta = max(highs)
    zona_baja = min(lows)

    return zona_alta, zona_baja


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
# ABSORCION
# =========================

def absorcion():

    v = velas(5)

    precios = [x[4] for x in v]
    vols = [x[5] for x in v]

    cambio = abs(precios[-1] - precios[0])

    volumen = sum(vols)

    if cambio < 10 and volumen > statistics.mean(vols)*3:

        return True

    return False


# =========================
# MARKET MAKER TRAP
# =========================

def manipulacion():

    v = velas(7)

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

    ultimo = cambios[-1]

    z = (ultimo-media)/desviacion if desviacion != 0 else 0

    prob_up = 1/(1+math.exp(-z))

    prob_down = 1-prob_up

    return int(prob_up*100), int(prob_down*100)


# =========================
# MOTOR DE DECISION
# =========================

def decision():

    c1,c5 = momentum()

    presion = orderbook()

    inst = volumen_institucional()

    absorb = absorcion()

    bull,bear = manipulacion()

    prob_up,prob_down = modelo_ml()

    score = 0

    if c1 > 0:
        score += 1

    if c5 > 0:
        score += 1

    if presion == "COMPRADORES":
        score += 1

    if inst:
        score += 1

    if absorb:
        score += 1

    if prob_up > prob_down:
        score += 1

    if bull:
        score -= 2

    if bear:
        score += 2

    if score >= 5:
        return "ENTRADA LONG"

    if score <= 1:
        return "ENTRADA SHORT"

    return "SIN SEÑAL"


# =========================
# REPORTE
# =========================

def reporte():

    precio,tendencia = contexto()

    presion = orderbook()

    sw = sweep()

    zona_alta,zona_baja = zonas_institucionales()

    inst = volumen_institucional()

    absorb = absorcion()

    bull,bear = manipulacion()

    prob_up,prob_down = modelo_ml()

    señal = decision()

    msg = f"""

BTC QUANT RADAR

Precio: {precio}

Tendencia 2H: {tendencia}

SEÑAL: {señal}

Prob subida: {prob_up}%
Prob bajada: {prob_down}%

Presión mercado: {presion}

Sweep liquidez: {sw}

Volumen institucional: {inst}

Absorción: {absorb}

Bull trap: {bull}
Bear trap: {bear}

Zona institucional alta: {zona_alta}
Zona institucional baja: {zona_baja}

"""

    enviar(msg)


print("BOT CUANTITATIVO ACTIVO")

while True:

    try:

        reporte()

        time.sleep(30)

    except Exception as e:

        print(e)

        time.sleep(30)
