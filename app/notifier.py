import inspect
import logging
import os
from typing import Optional
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from app.exchanges import check_markets

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


class TelegramNotifier:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("TELEGRAM_TOKEN")
        if not self.api_key:
            raise ValueError("TELEGRAM_TOKEN not found in .env file or environment")

        self.interval_seconds = 20
        self.chat_ids: set[int] = set()

        self.application = (
            ApplicationBuilder().token(self.api_key).concurrent_updates(True).build()
        )

        self.application.add_handler(CommandHandler("start", self.start))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Triggered when user sends /start"""
        chat_id = update.effective_chat.id
        self.chat_ids.add(chat_id)
        await context.bot.send_message(chat_id=chat_id, text="سلام! 🤖")

    async def run_async(self):
        """Non-blocking async runner for FastAPI"""
        print("🤖 Telegram bot started (async)...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()

    async def notify(self, opportunities):
        """Send notifications for a list of ArbitrageOpportunity objects.

        This method is intended to be called by an external scheduler/background task.
        It will deduplicate already-seen opportunities.
        """
        if not opportunities:
            return

        for opp in opportunities:
            if opp.direction =='Buy on Nobitex → Sell on Wallex':
                buy_price = opp.nobitex_price.best_sell
                sell_price = opp.wallex_price.best_buy
            else:
                buy_price = opp.wallex_price.best_sell
                sell_price = opp.nobitex_price.best_buy

            msg = (
                f"💰 *فرصت آربیتراژ جدید یافت شد!*\n\n"
                f"🪙 ارز: `{opp.unit}/TMN`\n"
                f"⏰ زمان کشف: {opp.wallex_price.time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"🏦 قیمت خرید : {buy_price:,.0f}\n"
                f"🏦 قیمت فروش : {sell_price:,.0f}\n\n"
                f"📈 اختلاف: {opp.diff:,.0f} تومان\n"
                f"📊 درصد اختلاف: {opp.diff_percentage:.2f}%\n"
                f"🔁 مسیر: {opp.direction}"
            )

            for chat_id in self.chat_ids:
                try:
                    await self.application.bot.send_message(
                        chat_id=chat_id, text=msg, parse_mode="Markdown"
                    )
                except Exception:
                    logging.exception("Failed to send opportunity message")
