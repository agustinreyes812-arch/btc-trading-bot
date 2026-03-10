import ccxt
import requests
import time
import statistics
import math

SYMBOL = "BTC/USDT"
TIMEFRAME = "1m"

TELEGRAM_TOKEN = "TU_TOKEN"
TELEGRAM_CHAT_ID = "TU_CHAT_ID"

exchange = ccxt.binance({"enableRateLimit": True})

# =========================
# TELEGRAM
# =========================

def enviar(msg):

    url=f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    data={
        "chat_id":TELEGRAM_CHAT_ID,
        "text":msg
    }

    try:
        requests.post(url,data=data)
    except:
        pass


# =========================
# VELAS
# =========================

def velas(n):

    return exchange.fetch_ohlcv(SYMBOL,TIMEFRAME,limit=n)


# =========================
# CONTEXTO
# =========================

def contexto():

    v=velas(120)

    closes=[x[4] for x in v]

    precio=closes[-1]

    media=statistics.mean(closes)

    if precio>media:
        tendencia="ALCISTA"
    elif precio<media:
        tendencia="BAJISTA"
    else:
        tendencia="NEUTRAL"

    return precio,tendencia


# =========================
# MOMENTUM MODEL
# =========================

def modelo_momentum():

    v=velas(6)

    c1=v[-1][4]-v[-2][4]
    c5=v[-1][4]-v[0][4]

    if c1>0 and c5>0:
        return "LONG"

    if c1<0 and c5<0:
        return "SHORT"

    return "NEUTRAL"


# =========================
# ORDERBOOK MODEL
# =========================

def modelo_orderbook():

    book=exchange.fetch_order_book(SYMBOL,limit=100)

    bids=book["bids"]
    asks=book["asks"]

    vol_bids=sum([b[1] for b in bids])
    vol_asks=sum([a[1] for a in asks])

    if vol_bids>vol_asks:
        return "LONG"

    if vol_asks>vol_bids:
        return "SHORT"

    return "NEUTRAL"


# =========================
# SWEEP LIQUIDEZ
# =========================

def sweep():

    v=velas(15)

    highs=[x[2] for x in v]
    lows=[x[3] for x in v]

    if highs[-1]>max(highs[:-1]):
        return "SHORT_LIQUIDATED"

    if lows[-1]<min(lows[:-1]):
        return "LONG_LIQUIDATED"

    return "NONE"


# =========================
# MODELO LIQUIDEZ
# =========================

def modelo_liquidez():

    s=sweep()

    if s=="SHORT_LIQUIDATED":
        return "LONG"

    if s=="LONG_LIQUIDATED":
        return "SHORT"

    return "NEUTRAL"


# =========================
# MODELO ESTADISTICO
# =========================

def modelo_estadistico():

    v=velas(300)

    closes=[x[4] for x in v]

    cambios=[]

    for i in range(1,len(closes)):
        cambios.append(closes[i]-closes[i-1])

    media=statistics.mean(cambios)

    dev=statistics.stdev(cambios)

    ultimo=cambios[-1]

    z=(ultimo-media)/dev if dev!=0 else 0

    prob_up=1/(1+math.exp(-z))

    prob_down=1-prob_up

    if prob_up>0.6:
        return "LONG",int(prob_up*100)

    if prob_down>0.6:
        return "SHORT",int(prob_down*100)

    return "NEUTRAL",50


# =========================
# MAPA LIQUIDACIONES
# =========================

def mapa_liquidaciones():

    v=velas(120)

    highs=[x[2] for x in v]
    lows=[x[3] for x in v]

    maximo=max(highs)
    minimo=min(lows)

    rango=maximo-minimo

    zona_shorts=maximo+rango*0.25
    zona_longs=minimo-rango*0.25

    return zona_shorts,zona_longs


# =========================
# RANDOM FOREST SIMPLE
# =========================

def decision():

    votos_long=0
    votos_short=0

    m1=modelo_momentum()
    m2=modelo_orderbook()
    m3=modelo_liquidez()
    m4,prob=modelo_estadistico()

    modelos=[m1,m2,m3,m4]

    for m in modelos:

        if m=="LONG":
            votos_long+=1

        if m=="SHORT":
            votos_short+=1

    if votos_long>=3:
        señal="LONG FUERTE"

    elif votos_short>=3:
        señal="SHORT FUERTE"

    else:
        señal="SIN SEÑAL"

    return señal,prob


# =========================
# REPORTE
# =========================

def reporte():

    precio,tendencia=contexto()

    señal,prob=decision()

    zona_shorts,zona_longs=mapa_liquidaciones()

    msg=f"""

BTC QUANT ENGINE

Precio: {precio}

Tendencia: {tendencia}

SEÑAL: {señal}

Probabilidad modelo: {prob}%

Zona liquidación shorts: {zona_shorts}

Zona liquidación longs: {zona_longs}

"""

    enviar(msg)


print("BOT CUANTITATIVO INICIADO")

while True:

    try:

        reporte()

        time.sleep(30)

    except Exception as e:

        print(e)
        time.sleep(30)
