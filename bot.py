import requests
import time
import pandas as pd

SYMBOL = "BTCUSDT"

def get_price():

    url = "https://api.binance.com/api/v3/ticker/price"
    data = requests.get(url, params={"symbol":SYMBOL}).json()

    return float(data["price"])


def momentum_check():

    prices = []

    for i in range(10):
        prices.append(get_price())
        time.sleep(5)

    df = pd.Series(prices)

    change = (df.iloc[-1] - df.iloc[0]) / df.iloc[0] * 100

    return change


def detect_move():

    momentum = momentum_check()

    if momentum > 0.15:
        print("Possible LONG move incoming", momentum)

    elif momentum < -0.15:
        print("Possible SHORT move incoming", momentum)

while True:

    detect_move()

    time.sleep(30)
