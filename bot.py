import ccxt
import requests
import time
import pandas as pd

TOKEN = "8603402885:AAFS9FWZvf-9syRTCnqLAEIwLALUGM9rVcc"
CHAT_ID = "1252957275"

exchange = ccxt.binance()

def enviar(msg):

    url=f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data={
        "chat_id":CHAT_ID,
        "text":msg
    }

    try:
        requests.post(url,data=data)
    except:
        print("Error telegram")


enviar("🚀 Bot institucional iniciado y monitoreando mercado")


pares = [
"BTC/USDT","ETH/USDT","BNB/USDT","SOL/USDT","XRP/USDT",
"ADA/USDT","DOGE/USDT","AVAX/USDT","LINK/USDT","MATIC/USDT",
"LTC/USDT","ATOM/USDT","UNI/USDT","APT/USDT","NEAR/USDT",
"FTM/USDT","OP/USDT","ARB/USDT","INJ/USDT","SUI/USDT"
]


def rsi(df,period=14):

    delta=df["close"].diff()

    gain=delta.clip(lower=0)
    loss=-delta.clip(upper=0)

    avg_gain=gain.rolling(period).mean()
    avg_loss=loss.rolling(period).mean()

    rs=avg_gain/avg_loss

    rsi=100-(100/(1+rs))

    return rsi



def analizar(par):

    candles=exchange.fetch_ohlcv(par,"1m",limit=120)

    df=pd.DataFrame(
        candles,
        columns=["time","open","high","low","close","volume"]
    )

    df["RSI"]=rsi(df)

    ultimo=df.iloc[-1]

    max20=df["high"].tail(20).max()
    min20=df["low"].tail(20).min()

    rango=max20-min20

    elasticidad=(rango/ultimo["close"])*100

    vol_avg=df["volume"].tail(30).mean()
    vol_now=ultimo["volume"]

    volumen_fuerte=vol_now>vol_avg*2

    squeeze=elasticidad<0.18


    if ultimo["high"]>max20 and ultimo["close"]<max20:

        enviar(f"""
🎯 LIQUIDITY SWEEP SHORT

{par}

Precio {round(ultimo['close'],2)}
RSI {round(ultimo['RSI'],2)}
Elasticidad {round(elasticidad,3)}%
""")


    if ultimo["low"]<min20 and ultimo["close"]>min20:

        enviar(f"""
🎯 LIQUIDITY SWEEP LONG

{par}

Precio {round(ultimo['close'],2)}
RSI {round(ultimo['RSI'],2)}
Elasticidad {round(elasticidad,3)}%
""")


    if squeeze and volumen_fuerte:

        enviar(f"""
⚡ VOLATILITY SQUEEZE

{par}

Compresión detectada
Movimiento fuerte posible

Precio {round(ultimo['close'],2)}
RSI {round(ultimo['RSI'],2)}
Elasticidad {round(elasticidad,3)}%
""")


    if vol_now>vol_avg*3 and elasticidad<0.15:

        enviar(f"""
🐋 POSIBLE ENTRADA INSTITUCIONAL

{par}

Volumen extremo detectado

Precio {round(ultimo['close'],2)}
RSI {round(ultimo['RSI'],2)}
Elasticidad {round(elasticidad,3)}%
""")


def libro_ordenes(par):

    try:

        orderbook=exchange.fetch_order_book(par)

        bids=orderbook["bids"][:10]
        asks=orderbook["asks"][:10]

        bid_vol=sum([b[1] for b in bids])
        ask_vol=sum([a[1] for a in asks])

        if bid_vol>ask_vol*2:

            enviar(f"""
🐋 PARED DE COMPRA DETECTADA

{par}

Presión compradora fuerte
Posible rebote
""")


        if ask_vol>bid_vol*2:

            enviar(f"""
🐋 PARED DE VENTA DETECTADA

{par}

Presión vendedora fuerte
Posible caída
""")

    except:
        pass



def detectar_explosion(par):

    try:

        candles=exchange.fetch_ohlcv(par,"1m",limit=60)

        df=pd.DataFrame(
            candles,
            columns=["time","open","high","low","close","volume"]
        )

        cambio=(df["close"].iloc[-1]-df["close"].iloc[-5])/df["close"].iloc[-5]*100

        vol_actual=df["volume"].iloc[-1]
        vol_promedio=df["volume"].tail(20).mean()

        rango=df["high"].tail(20).max()-df["low"].tail(20).min()
        precio=df["close"].iloc[-1]

        volatilidad=(rango/precio)*100

        if vol_actual>vol_promedio*2 and volatilidad<0.25 and abs(cambio)>0.4:

            enviar(f"""
🚨 POSIBLE EXPLOSIÓN DE PRECIO

{par}

Cambio 5m: {round(cambio,2)} %

Precio actual: {round(precio,2)}
""")

    except:
        pass



ultimo_reporte=time.time()


while True:

    try:

        for par in pares:

            analizar(par)

            libro_ordenes(par)

            detectar_explosion(par)

            time.sleep(1)


        if time.time()-ultimo_reporte>3600:

            enviar("📊 Bot activo y monitoreando mercado")

            ultimo_reporte=time.time()

    except Exception as e:

        print(e)

    time.sleep(15)
