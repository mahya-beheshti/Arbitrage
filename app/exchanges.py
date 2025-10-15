from datetime import datetime
import requests
from pydantic import BaseModel
from dotenv import load_dotenv
import os

class CurrencyInfo(BaseModel):
    best_buy: float
    best_sell: float
    latest: float
    time: datetime


def get_nobitex_price(
    srcCurrency: str = "btc", dstCurrency: str = "rls"
) -> CurrencyInfo:
    url = f"https://apiv2.nobitex.ir/market/stats?srcCurrency={srcCurrency}&dstCurrency={dstCurrency}"
    response = requests.get(url)
    data = response.json()

    # handle potential errors
    if data.get("status") != "ok" or "stats" not in data:
        raise ValueError(f"Invalid response: {data}")
    
    stats = data["stats"][f"{srcCurrency}-{dstCurrency}"]
    return CurrencyInfo(
        best_buy=float(stats["bestBuy"]),
        best_sell=float(stats["bestSell"]),
        latest=float(stats["latest"]),
        time=datetime.now(),
    )


def get_wallex_price(symbol: str = "BTCUSDT")-> CurrencyInfo:
    try:
        load_dotenv()
    except:
        raise ValueError("env not loaded")
    api_key = os.getenv('WALLEX_API_KEY')

    url = f"https://api.wallex.ir/v1/trades?symbol={symbol}"
    headers = {"x-api-key": api_key} if api_key else {}
    result = requests.get(url, headers=headers)
    data = result.json()

    if not data['success']:
        raise ValueError(f"Invalid response: {data}")

    latest_trades = data["result"]["latestTrades"]
    wallex_info = CurrencyInfo(
    )
    return wallex_info
