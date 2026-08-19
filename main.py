import os
import asyncio
import logging
from threading import Thread
from flask import Flask
import ccxt.async_support as ccxt
import pandas as pd
import ta
import numpy as np
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Flask Keep-Alive
app = Flask('')
@app.route('/')
def home():
    return "Crypto Signal Pro+ Bot is Running 24/7!"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# Configuration
TELEGRAM_TOKEN = "8982651587:AAFdVu5qARVO6aXgvUwC6f2QL1TquDFSqqY" 
PAIRS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
SENT_SIGNALS = {}

exchange = ccxt.binance({'options': {'defaultType': 'future'}, 'enableRateLimit': True})

# --- SMC & MARKET STRUCTURE ENGINE ---
def detect_swings(df, window=5):
    """Detects swing highs and lows for BOS/CHoCH."""
    df['swing_high'] = df['high'][(df['high'].shift(window) < df['high']) & (df['high'].shift(-window) < df['high'])]
    df['swing_low'] = df['low'][(df['low'].shift(window) > df['low']) & (df['low'].shift(-window) > df['low'])]
    return df

def analyze_market_structure(df):
    """Checks for simple BOS/CHoCH and FVG."""
    # FVG Detection
    df['fvg_bull'] = (df['low'].shift(-1) > df['high'].shift(1))
    df['fvg_bear'] = (df['high'].shift(-1) < df['low'].shift(1))
    
    # Simple Liquidity Sweep logic
    df['liq_sweep_buy'] = (df['low'] < df['low'].shift(1)) & (df['close'] > df['low'].shift(1))
    df['liq_sweep_sell'] = (df['high'] > df['high'].shift(1)) & (df['close'] < df['high'].shift(1))
    
    return df

async def fetch_and_analyze(symbol):
    timeframes = ['4h', '1h', '15m', '5m']
    data = {}
    
    for tf in timeframes:
        ohlcv = await exchange.fetch_ohlcv(symbol, tf, limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df = detect_swings(df)
        df = analyze_market_structure(df)
        
        # Add basic indicators
        df['EMA_200'] = ta.trend.ema_indicator(df['close'], window=200)
        df['RSI'] = ta.momentum.rsi(df['close'], window=14)
        data[tf] = df
        
    return data

async def get_signal(symbol):
    data = await fetch_and_analyze(symbol)
    if not data: return None
    
    # Current data points
    curr_15m = data['15m'].iloc[-1]
    curr_4h = data['4h'].iloc[-1]
    
    # Strategy: Confluence of 4H Trend + 15m Signal
    trend_4h = "BULLISH" if curr_4h['close'] > curr_4h['EMA_200'] else "BEARISH"
    
    # LONG CONDITIONS
    if trend_4h == "BULLISH" and curr_15m['liq_sweep_buy'] and curr_15m['fvg_bull']:
        return {
            'symbol': symbol,
            'direction': "LONG 🟢",
            'reasons': ["4H Bullish Trend Alignment", "15m Liquidity Sweep", "15m Bullish FVG Detected"]
        }
    
    # SHORT CONDITIONS
    elif trend_4h == "BEARISH" and curr_15m['liq_sweep_sell'] and curr_15m['fvg_bear']:
        return {
            'symbol': symbol,
            'direction': "SHORT 🔴",
            'reasons': ["4H Bearish Trend Alignment", "15m Liquidity Sweep", "15m Bearish FVG Detected"]
        }
        
    return None

# --- TELEGRAM BOT ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Crypto Signal Pro+ Active. Monitoring market structure 24/7.")

async def market_scanner(app):
    while True:
        try:
            for symbol in PAIRS:
                signal = await get_signal(symbol)
                if signal:
                    signal_key = f"{symbol}_{signal['direction']}"
                    if signal_key not in SENT_SIGNALS:
                        SENT_SIGNALS[signal_key] = True
                        message = f"🚨 **{signal['direction']}** - {signal['symbol']}\n\nAnalysis:\n" + "\n".join([f"• {r}" for r in signal['reasons']])
                        for chat_id in app.user_data.keys():
                            await app.bot.send_message(chat_id=chat_id, text=message)
            await asyncio.sleep(60)
        except Exception as e:
            logging.error(f"Scanner error: {e}")
            await asyncio.sleep(10)

if __name__ == '__main__':
    keep_alive()
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    loop = asyncio.get_event_loop()
    loop.create_task(market_scanner(application))
    application.run_polling()
