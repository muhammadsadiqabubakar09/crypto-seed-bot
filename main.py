import os
import logging
from threading import Thread
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from mnemonic import Mnemonic

app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bot is running live!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host='0.0.0.0', port=port)

# Replace with your actual Telegram Bot Token
TOKEN "8824351762:AAFxLiRKCr1ZVPxL8_b8reHTyZyhjmHu1b8""

mnemo = Mnemonic("english")

def generate_mnemonic(words_count: int) -> str:
    if words_count == 12:
        return mnemo.generate(strength=128)
    elif words_count == 24:
        return mnemo.generate(strength=256)
    return ""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [['Generate 12 Words', 'Generate 24 Words']]
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Welcome! Please select an option below to generate a 12 or 24-word seed phrase with a valid BIP-39 checksum:",
        reply_markup=markup
    )

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if user_text == 'Generate 12 Words':
        seed_phrase = generate_mnemonic(12)
        response = f"**12-Word Seed Phrase:**\n\n`{seed_phrase}`\n\n*This mnemonic includes a valid BIP-39 checksum on the 12th word.*"
        await update.message.reply_text(response, parse_mode="Markdown")
    elif user_text == 'Generate 24 Words':
        seed_phrase = generate_mnemonic(24)
        response = f"**24-Word Seed Phrase:**\n\n`{seed_phrase}`\n\n*This mnemonic includes a valid BIP-39 checksum on the 24th word.*"
        await update.message.reply_text(response, parse_mode="Markdown")

if __name__ == '__main__':
    Thread(target=run_flask).start()
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))
    print("Bot is running...")
    app.run_polling()
