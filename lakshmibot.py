# LakshmiBot - Crypto & Stock Price Alert Telegram Bot using JSON + Yahoo Finance

import os
import json
import requests
import pytz
from telegram import Update, BotCommand
from telegram.ext import Updater, CommandHandler, CallbackContext
from apscheduler.schedulers.background import BackgroundScheduler

# === CONFIGURATION ===
BOT_TOKEN = '8317306198:AAHKt893X7pV_-C4bt7mBEr9DW5rtncPHpU'
ALERT_FILE = 'alerts.json'

# === INIT STORAGE ===
if not os.path.exists(ALERT_FILE):
    with open(ALERT_FILE, 'w') as f:
        json.dump({}, f)

def load_alerts():
    with open(ALERT_FILE, 'r') as f:
        return json.load(f)

def save_alerts(data):
    with open(ALERT_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# === PRICE FETCHING ===
def get_crypto_price(symbol='bitcoin'):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=inr"
    try:
        res = requests.get(url).json()
        return res[symbol]['inr']
    except:
        return None

def get_stock_price(symbol='RELIANCE.NS'):
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
    try:
        res = requests.get(url).json()
        return res['quoteResponse']['result'][0]['regularMarketPrice']
    except:
        return None

# === COMMAND HANDLERS ===
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "🙏 Welcome to LakshmiBot!\n"
        "Use /price <symbol> to get live prices.\n"
        "Use /alert <symbol> <price> to set a price alert.\n"
        "Example:\n"
        "/price bitcoin\n"
        "/price RELIANCE.NS\n"
        "/alert bitcoin 3000000\n"
        "/alert ASHOKLEY.NS 200"
    )

def price(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text("Usage: /price bitcoin or /price RELIANCE.NS")
        return

    symbol = context.args[0].lower()

    if '.' in symbol:  # Stock
        p = get_stock_price(symbol.upper())
    else:
        p = get_crypto_price(symbol)

    if p:
        update.message.reply_text(f"💹 Current price of {symbol.upper()} is ₹{p:,.2f}")
    else:
        hint = ""
        if '.' not in symbol:
            hint = "\nIf you're looking for a stock, try using the full symbol like `ASHOKLEY.NS` or `TCS.BO`."
        update.message.reply_text(f"❌ Could not fetch price for {symbol}.{hint}")

def alert(update: Update, context: CallbackContext):
    if len(context.args) < 2:
        update.message.reply_text("Usage: /alert <symbol> <target_price>")
        return

    symbol = context.args[0].lower()
    try:
        target = float(context.args[1])
    except:
        update.message.reply_text("❌ Invalid price format")
        return

    user_id = str(update.message.chat_id)
    alerts = load_alerts()
    alerts.setdefault(user_id, []).append({'symbol': symbol, 'target': target})
    save_alerts(alerts)

    update.message.reply_text(f"✅ Alert set for {symbol.upper()} at ₹{target:,.2f}")

def myalerts(update: Update, context: CallbackContext):
    user_id = str(update.message.chat_id)
    alerts = load_alerts().get(user_id, [])
    if not alerts:
        update.message.reply_text("You have no active alerts.")
        return

    msg = "🔔 Your Active Alerts:\n"
    for a in alerts:
        msg += f"- {a['symbol'].upper()} at ₹{a['target']:,.2f}\n"
    update.message.reply_text(msg)

# === ALERT CHECKER ===
def check_alerts():
    alerts = load_alerts()
    changed = False

    for user_id, user_alerts in list(alerts.items()):
        for alert in list(user_alerts):
            symbol = alert['symbol']
            target = alert['target']
            price = get_crypto_price(symbol) if '.' not in symbol else get_stock_price(symbol.upper())

            if price and price >= target:
                context.bot.send_message(chat_id=int(user_id),
                    text=f"🎉 {symbol.upper()} has reached ₹{price:,.2f} (Target: ₹{target:,.2f})")
                alerts[user_id].remove(alert)
                changed = True

    if changed:
        save_alerts(alerts)

# === MAIN ===
def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('price', price))
    dp.add_handler(CommandHandler('alert', alert))
    dp.add_handler(CommandHandler('myalerts', myalerts))

    updater.bot.set_my_commands([
        BotCommand('price', 'Get current price'),
        BotCommand('alert', 'Set a price alert'),
        BotCommand('myalerts', 'View your alerts')
    ])

    # Background scheduler (fixed timezone)
    scheduler = BackgroundScheduler(timezone=pytz.utc)
    scheduler.add_job(lambda: check_alerts_wrapper(updater), 'interval', seconds=60)
    scheduler.start()

    print("LakshmiBot is running...")
    updater.start_polling()
    updater.idle()

# Workaround for apscheduler
def check_alerts_wrapper(updater):
    global context
    context = updater.bot
    check_alerts()

if __name__ == '__main__':
    main()
