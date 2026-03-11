import ccxt
import requests
import time
import statistics
import math
import os

# =========================
# CONFIGURACION
# =========================

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

if not API_KEY or not API_SECRET:
    raise Exception("API KEYS NO CONFIGURADAS")

SYMBOL = "BTC/USDT"
TIMEFRAME = "1m"

TRADE_SIZE = 0.001

STOP_LOSS = 0.0015
TAKE_PROFIT = 0.003

LEVERAGE = 5

TELEGRAM_TOKEN = "TU_TOKEN"
TELEGRAM_CHAT_ID = "TU_CHAT_ID"

# =========================
# CONEXION BINANCE
# =========================

exchange = ccxt.binance({
    "apiKey": API_KEY,
    "secret": API_SECRET,
    "enableRateLimit": True,
})

exchange.options["defaultType"] = "future"

exchange.set_leverage(LEVERAGE, SYMBOL)

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
# PRECIO
# =========================

def precio():

    ticker = exchange.fetch_ticker(SYMBOL)

    return ticker["last"]


# =========================
# VELAS
# =========================

def velas(n):

    return exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=n)


# =========================
# CONTEXTO 2 HORAS
# =========================

def contexto():

    v = velas(120)

    closes = [x[4] for x in v]

    precio_actual = closes[-1]

    media = statistics.mean(closes)

    if precio_actual > media:
        tendencia = "ALCISTA"

    elif precio_actual < media:
        tendencia = "BAJISTA"

    else:
        tendencia = "NEUTRAL"

    return precio_actual, tendencia


# =========================
# MOMENTUM
# =========================

def modelo_momentum():

    v = velas(6)

    c1 = v[-1][4] - v[-2][4]
    c5 = v[-1][4] - v[0][4]

    if c1 > 0 and c5 > 0:
        return "LONG"

    if c1 < 0 and c5 < 0:
        return "SHORT"

    return "NEUTRAL"


# =========================
# ORDERBOOK
# =========================

def modelo_orderbook():

    book = exchange.fetch_order_book(SYMBOL, limit=100)

    bids = book["bids"]
    asks = book["asks"]

    vol_bids = sum([b[1] for b in bids])
    vol_asks = sum([a[1] for a in asks])

    if vol_bids > vol_asks:
        return "LONG"

    if vol_asks > vol_bids:
        return "SHORT"

    return "NEUTRAL"


# =========================
# MICRO MOVIMIENTO
# =========================

def micro_movimiento():

    v = velas(3)

    p1 = v[-2][4]
    p2 = v[-1][4]

    cambio = (p2 - p1) / p1

    if cambio > 0.0015:
        return "UP"

    if cambio < -0.0015:
        return "DOWN"

    return "NONE"


# =========================
# MODELO ESTADISTICO
# =========================

def modelo_estadistico():

    v = velas(300)

    closes = [x[4] for x in v]

    cambios = []

    for i in range(1, len(closes)):
        cambios.append(closes[i] - closes[i-1])

    media = statistics.mean(cambios)
    dev = statistics.stdev(cambios)

    ultimo = cambios[-1]

    z = (ultimo - media) / dev if dev != 0 else 0

    prob_up = 1 / (1 + math.exp(-z))
    prob_down = 1 - prob_up

    if prob_up > 0.6:
        return "LONG", int(prob_up * 100)

    if prob_down > 0.6:
        return "SHORT", int(prob_down * 100)

    return "NEUTRAL", 50


# =========================
# ESTIMADOR DE MOVIMIENTO
# =========================

def estimar_movimiento():

    v = velas(120)

    highs = [x[2] for x in v]
    lows = [x[3] for x in v]
    closes = [x[4] for x in v]
    vols = [x[5] for x in v]

    precio_actual = closes[-1]

    rangos = []

    for i in range(len(highs)):
        rangos.append(highs[i] - lows[i])

    atr = statistics.mean(rangos)

    volatilidad = atr / precio_actual

    impulso = (closes[-1] - closes[-10]) / closes[-10]

    vol_actual = vols[-1]
    vol_prom = statistics.mean(vols)

    factor_vol = vol_actual / vol_prom

    movimiento = abs(volatilidad * 2 + impulso * factor_vol)

    porcentaje = movimiento * 100

    if porcentaje < 0.15:
        tipo = "SIN MOVIMIENTO"
    elif porcentaje < 0.5:
        tipo = "MICRO SCALP"
    elif porcentaje < 2:
        tipo = "SCALPING MEDIO"
    elif porcentaje < 5:
        tipo = "MOVIMIENTO FUERTE"
    else:
        tipo = "MOVIMIENTO GRANDE"

    return round(porcentaje, 2), tipo


# =========================
# VERIFICAR POSICION
# =========================

def hay_posicion():

    posiciones = exchange.fetch_positions()

    for p in posiciones:

        if p["symbol"] == "BTC/USDT":

            if float(p["contracts"]) != 0:
                return True

    return False


# =========================
# MOTOR DE DECISION
# =========================

def decision():

    votos_long = 0
    votos_short = 0

    m1 = modelo_momentum()
    m2 = modelo_orderbook()
    m3, prob = modelo_estadistico()

    micro = micro_movimiento()

    modelos = [m1, m2, m3]

    for m in modelos:

        if m == "LONG":
            votos_long += 1

        if m == "SHORT":
            votos_short += 1

    if micro == "UP":
        votos_long += 1

    if micro == "DOWN":
        votos_short += 1

    if votos_long >= 2 and prob > 60:
        return "LONG"

    if votos_short >= 2 and prob > 60:
        return "SHORT"

    return "NONE"


# =========================
# OPERACIONES
# =========================

def abrir_long():

    p = precio()

    sl = p * (1 - STOP_LOSS)
    tp = p * (1 + TAKE_PROFIT)

    exchange.create_market_buy_order(SYMBOL, TRADE_SIZE)

    exchange.create_order(
        SYMBOL,
        "STOP_MARKET",
        "sell",
        TRADE_SIZE,
        None,
        {"stopPrice": sl}
    )

    exchange.create_order(
        SYMBOL,
        "TAKE_PROFIT_MARKET",
        "sell",
        TRADE_SIZE,
        None,
        {"stopPrice": tp}
    )

    enviar(f"LONG ABIERTO\nPrecio: {p}\nSL: {sl}\nTP: {tp}")


def abrir_short():

    p = precio()

    sl = p * (1 + STOP_LOSS)
    tp = p * (1 - TAKE_PROFIT)

    exchange.create_market_sell_order(SYMBOL, TRADE_SIZE)

    exchange.create_order(
        SYMBOL,
        "STOP_MARKET",
        "buy",
        TRADE_SIZE,
        None,
        {"stopPrice": sl}
    )

    exchange.create_order(
        SYMBOL,
        "TAKE_PROFIT_MARKET",
        "buy",
        TRADE_SIZE,
        None,
        {"stopPrice": tp}
    )

    enviar(f"SHORT ABIERTO\nPrecio: {p}\nSL: {sl}\nTP: {tp}")


# =========================
# REPORTE
# =========================

def reporte():

    precio_actual, tendencia = contexto()

    señal = decision()

    mov, tipo = estimar_movimiento()

    msg = f"""
BTC QUANT ENGINE

Precio: {precio_actual}

Tendencia: {tendencia}

Movimiento esperado: {mov} %

Tipo de oportunidad: {tipo}

Señal: {señal}
"""

    print(msg)

    return señal


# =========================
# LOOP PRINCIPAL
# =========================

print("BOT DE TRADING CUANTITATIVO INICIADO")

while True:

    try:

        señal = reporte()

        if señal == "LONG" and not hay_posicion():

            abrir_long()

            time.sleep(120)

        elif señal == "SHORT" and not hay_posicion():

            abrir_short()

            time.sleep(120)

        time.sleep(30)

    except Exception as e:

        print("Error:", e)

        enviar(f"ERROR BOT: {e}")

        time.sleep(30)
