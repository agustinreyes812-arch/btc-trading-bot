import ccxt
import requests
import time
import pandas as pd

TOKEN = "8603402885:AAFS9FWZvf-9syRTCnqLAEIwLALUGM9rVcc"
CHAT_ID = "1252957275"

exchange = ccxt.binance({
    "enableRateLimit": True
})

def enviar(msg):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": msg
    }

    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Error Telegram:", e)


enviar("🚀 Bot de trading iniciado y monitoreando mercado")

pares = [
"BTC/USDT","ETH/USDT","BNB/USDT","SOL/USDT","XRP/USDT",
"ADA/USDT","DOGE/USDT","AVAX/USDT","LINK/USDT","MATIC/USDT",
"LTC/USDT","ATOM/USDT","UNI/USDT","APT/USDT","NEAR/USDT",
"FTM/USDT","OP/USDT","ARB/USDT","INJ/USDT","SUI/USDT"
]


def rsi(df, period=14):

    delta = df["close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return rsi


def analizar(par):

    candles = exchange.fetch_ohlcv(par, "1m", limit=120)

    df = pd.DataFrame(
        candles,
        columns=["time","open","high","low","close","volume"]
    )

    df["RSI"] = rsi(df)

    ultimo = df.iloc[-1]

    max20 = df["high"].tail(20).max()
    min20 = df["low"].tail(20).min()

    rango = max20 - min20

    elasticidad = (rango / ultimo["close"]) * 100

    vol_avg = df["volume"].tail(30).mean()
    vol_now = ultimo["volume"]

    volumen_fuerte = vol_now > vol_avg * 2
    squeeze = elasticidad < 0.18

    if ultimo["high"] > max20 and ultimo["close"] < max20:

        enviar(f"""
🎯 LIQUIDITY SWEEP SHORT

{par}

Precio {round(ultimo['close'],2)}
RSI {round(ultimo['RSI'],2)}
Elasticidad {round(elasticidad,3)}%
""")


    if ultimo["low"] < min20 and ultimo["close"] > min20:

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


    if vol_now > vol_avg * 3 and elasticidad < 0.15:

        enviar(f"""
🐋 POSIBLE ENTRADA INSTITUCIONAL

{par}

Volumen extremo detectado

Precio {round(ultimo['close'],2)}
RSI {round(ultimo['RSI'],2)}
Elasticidad {round(elasticidad,3)}%
""")


ultimo_reporte = time.time()

while True:

    try:

        for par in pares:

            analizar(par)
            time.sleep(1)

        if time.time() - ultimo_reporte > 3600:

            enviar("📊 Bot activo y monitoreando mercado")
            ultimo_reporte = time.time()

    except Exception as e:

        print("Error:", e)

    time.sleep(15)
