from sqlite3 import IntegrityError
import requests
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from typing import Optional
from datetime import datetime, timedelta
from app.database import SessionLocal, Opportunity
from app.metrics import (
    LAST_DIFF,
    NOBITEX_SUCCESS,
    NOBITEX_FAILURE,
    NOBITEX_RESPONSE_TIME,
    WALLEX_SUCCESS,
    WALLEX_FAILURE,
    WALLEX_RESPONSE_TIME,
    ARB_OPPORTUNITY_FOUND,
)


nobitex_symbols = [
    "BTC",
    "ETH",
    "LTC",
    "USDT",
    "XRP",
    "BCH",
    "BNB",
    "EOS",
    "XLM",
    "ETC",
    "TRX",
    "DOGE",
    "UNI",
    "DAI",
    "LINK",
    "DOT",
    "AAVE",
    "ADA",
    "SHIB",
    "FTM",
    "MATIC",
    "AXS",
    "MANA",
    "SAND",
    "AVAX",
    "MKR",
    "GMT",
    "USDC",
    "CHZ",
    "GRT",
    "CRV",
    "BAND",
    "COMP",
    "EGLD",
    "HBAR",
    "GAL",
    "WBTC",
    "IMX",
    "ONE",
    "GLM",
    "ENS",
    "BTT",
    "SUSHI",
    "LDO",
    "ATOM",
    "ZRO",
    "STORJ",
    "ANT",
    "AEVO",
    "FLOKI",
    "RSR",
    "API3",
    "XMR",
    "OM",
    "RDNT",
    "MAGIC",
    "T",
    "NOT",
    "CVX",
    "XTZ",
    "FIL",
    "UMA",
    "BABYDOGE",
    "SSV",
    "DAO",
    "BLUR",
    "EGALA",
    "GMX",
    "FLOW",
    "W",
    "CVC",
    "NMR",
    "SKL",
    "SNT",
    "BAT",
    "TRB",
    "WLD",
    "SOL",
    "QNT",
    "FET",
    "AGIX",
    "LPT",
    "SLP",
    "MEME",
    "BAL",
    "TON",
    "SNX",
    "1INCH",
    "RNDR",
    "AGLD",
    "NEAR",
    "WOO",
    "MDT",
    "LRC",
    "BICO",
    "NFT",
    "ARB",
    "CELR",
    "DYDX",
    "APT",
    "ALGO",
    "MASK",
    "OMG",
    "APE",
    "ENJ",
]


class CurrencyInfo(BaseModel):
    best_buy: float
    best_sell: float
    latest: Optional[float]
    time: datetime


class ArbitrageOpportunity(BaseModel):
    wallex_price: CurrencyInfo
    nobitex_price: CurrencyInfo
    unit: str
    diff: float
    diff_percentage: float
    direction: str  # "buy on X, sell on Y"


@NOBITEX_RESPONSE_TIME.time()
def get_nobitex_price(
    srcCurrency: str = "btc", dstCurrency: str = "rls"
) -> CurrencyInfo:
    try:
        url = f"https://apiv2.nobitex.ir/market/stats?srcCurrency={srcCurrency}&dstCurrency={dstCurrency}"
        response = requests.get(url)
        data = response.json()

        if data.get("status") != "ok" or "stats" not in data:
            raise ValueError(f"Invalid Nobitex response: {data}")

        stats = data["stats"][f"{srcCurrency}-{dstCurrency}"]
        NOBITEX_SUCCESS.inc()
        return CurrencyInfo(
            best_buy=float(stats["bestBuy"]),
            best_sell=float(stats["bestSell"]),
            latest=float(stats["latest"]),
            time=datetime.now(),
        )
    except Exception:
        NOBITEX_FAILURE.inc()
        raise


@WALLEX_RESPONSE_TIME.time()
def get_wallex_price(symbol: str = "BTCTMN") -> CurrencyInfo:
    load_dotenv()
    api_key = os.getenv("WALLEX_API_KEY")
    try:
        url = f"https://api.wallex.ir/v1/trades?symbol={symbol}"
        headers = {"x-api-key": api_key} if api_key else {}
        result = requests.get(url, headers=headers)
        data = result.json()

        if not data["success"]:
            raise ValueError(f"Invalid Wallex response: {data}")

        latest_trades = data["result"]["latestTrades"]
        if not latest_trades:
            print(data)
            print(symbol)
            raise ValueError("No trades returned")

        latest_price = float(latest_trades[0]["price"])

        buy_prices = [float(t["price"]) for t in latest_trades if t["isBuyOrder"]]
        sell_prices = [float(t["price"]) for t in latest_trades if not t["isBuyOrder"]]

        best_buy = max(buy_prices) if buy_prices else latest_price
        best_sell = min(sell_prices) if sell_prices else latest_price
        WALLEX_SUCCESS.inc()
        return CurrencyInfo(
            best_buy=best_buy,
            best_sell=best_sell,
            latest=latest_price,
            time=datetime.now(),
        )
    except Exception:
        WALLEX_FAILURE.inc()
        raise


def find_opportunity(
    buy_price: float,
    sell_price: float,
    nobitex_info: CurrencyInfo,
    wallex_info: CurrencyInfo,
    unit: str,
    direction: str,
) -> Optional[ArbitrageOpportunity]:
    diff = sell_price - buy_price
    diff_percentage = diff / buy_price * 100

    if diff_percentage > 0.5:  # 0.5% threshold
        return ArbitrageOpportunity(
            wallex_price=wallex_info,
            nobitex_price=nobitex_info,
            unit=unit,
            diff=diff,
            diff_percentage=diff_percentage,
            direction=direction,
        )
    return None


def check_for_opportunity(srcCurrency: str = "BTC"):
    wallex_symbol = f"{srcCurrency.upper()}TMN"
    wallex_info = get_wallex_price(wallex_symbol)

    nobitex_info = get_nobitex_price(srcCurrency.lower(), "rls")

    # convert to TMN
    nobitex_info.best_buy /= 10
    nobitex_info.best_sell /= 10
    nobitex_info.latest = (nobitex_info.latest or 0) / 10

    # Option 1: Buy on Nobitex, sell on Wallex
    opp1 = find_opportunity(
        buy_price=nobitex_info.best_sell,
        sell_price=wallex_info.best_buy,
        nobitex_info=nobitex_info,
        wallex_info=wallex_info,
        unit=srcCurrency.upper(),
        direction="Buy on Nobitex → Sell on Wallex",
    )

    # Option 2: Buy on Wallex, sell on Nobitex
    opp2 = find_opportunity(
        buy_price=wallex_info.best_sell,
        sell_price=nobitex_info.best_buy,
        nobitex_info=nobitex_info,
        wallex_info=wallex_info,
        unit=srcCurrency.upper(),
        direction="Buy on Wallex → Sell on Nobitex",
    )

    opportunities = [opp for opp in [opp1, opp2] if opp]
    if not opportunities:
        return {"message": "No arbitrage opportunity found."}

    return opportunities


def get_wallex_markets():
    url = "https://api.wallex.ir/hector/web/v1/markets"
    load_dotenv()
    api_key = os.getenv("WALLEX_API_KEY")
    headers = {"x-api-key": api_key} if api_key else {}
    response = requests.get(url, headers=headers)

    data = response.json()
    symbols = []
    for d in data["result"]["markets"]:
        symbol = d["symbol"]
        if symbol.endswith("TMN"):
            symbols.append(symbol.replace("TMN", ""))
    return symbols


def check_markets():
    # wallex_markets = get_wallex_markets()
    # nobitex_markets = nobitex_symbols
    common_markets = ["BTC", "ETH", "LTC", "USDT", "XRP", "BCH", "BNB"]
    print(common_markets)

    opportunities = []
    for market in common_markets[:10]:
        try:
            result = check_for_opportunity(market)
            if isinstance(result, list):
                opportunities += result
        except Exception as e:
            print(f"Error checking {market}: {str(e)}")

    if not opportunities:
        print("❌ No arbitrage opportunities found in checked markets.")
        return []
    print(opportunities)
    db = SessionLocal()
    new_opps = []
    try:
        for opp in opportunities:
            pair = opp.unit
            direction = opp.direction
            if opp.direction == "Buy on Nobitex → Sell on Wallex":
                buy_price = opp.nobitex_price.best_sell
                sell_price = opp.wallex_price.best_buy
            else:
                buy_price = opp.wallex_price.best_sell
                sell_price = opp.nobitex_price.best_buy
            diffrence = opp.diff
            buy_exchange, sell_exchange = direction.split(" → ")
            diff_percent = round(opp.diff_percentage, 3)

            # Check if similar record exists recently
            exists = (
                db.query(Opportunity)
                .filter(
                    Opportunity.pair == pair,
                    Opportunity.buy_exchange == buy_exchange,
                    Opportunity.sell_exchange == sell_exchange,
                    Opportunity.difference_percent == diff_percent,
                    Opportunity.sell_price == sell_price,
                    Opportunity.buy_price == buy_price,
                    Opportunity.diffrence == diffrence
                )
                .first()
            )

            if not exists:
                db_opp = Opportunity(
                    pair=pair,
                    buy_exchange=buy_exchange,
                    sell_exchange=sell_exchange,
                    sell_price=sell_price,
                    buy_price=buy_price,
                    diffrence=diffrence,
                    difference_percent=diff_percent,
                )
                db.add(db_opp)
                try:
                    db.commit()
                    new_opps.append(opp)
                    LAST_DIFF.labels(currency=pair).set(opp.diff)

                except IntegrityError:
                    db.rollback()
                    print(f"Race condition detected for {pair}. Rolled back insert.")
                except Exception as commit_error:
                    db.rollback()
                    print(f"Commit error for {pair}: {commit_error}")

        if new_opps:
            ARB_OPPORTUNITY_FOUND.inc(len(new_opps))
        else:
            print("⚠️ No *new* opportunities found this round.")

    except Exception as e:
        print(f"Database error: {e}")
        db.rollback()
    finally:
        db.close()

    return new_opps
