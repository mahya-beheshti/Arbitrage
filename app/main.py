from app.database import init_db
from fastapi import FastAPI, Response  # type: ignore
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST  # type: ignore
import asyncio
import os
from app.exchanges import get_nobitex_price, get_wallex_price, check_markets
from app.notifier import TelegramNotifier
import traceback


app = FastAPI()

telegram_notifier = TelegramNotifier()


@app.get("/")
async def root():
    return {"message": "Hello World"}


async def market_polling_loop(interval_seconds: int):
    """Background loop that polls markets and notifies the Telegram notifier."""
    print(f"🔁 Market polling loop started, interval={interval_seconds}s")
    try:
        while True:
            if telegram_notifier.chat_ids:
                try:
                    result = check_markets()
                    if asyncio.iscoroutine(result):
                        result = await result
                    # send to notifier
                    await telegram_notifier.notify(result)
                except Exception:
                    # keep loop alive on errors
                    traceback.print_exc()
            await asyncio.sleep(interval_seconds)
    except asyncio.CancelledError:
        print("🔴 Market polling loop cancelled")


@app.on_event("startup")
async def on_startup():
    # Initialize the database
    init_db()

    # read interval from env or default to 20s
    interval = int(os.getenv("POLL_INTERVAL_SECONDS", "20"))

    # start telegram bot in background
    asyncio.create_task(telegram_notifier.run_async())

    # start polling loop
    app.state._market_task = asyncio.create_task(market_polling_loop(interval))


@app.on_event("shutdown")
async def on_shutdown():
    # cancel background polling
    task = getattr(app.state, "_market_task", None)
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    # stop telegram bot gracefully
    try:
        await telegram_notifier.application.updater.stop()
        await telegram_notifier.application.stop()
    except Exception:
        pass


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
