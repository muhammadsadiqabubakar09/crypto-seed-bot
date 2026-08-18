import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from bip_utils import Bip39MnemonicGenerator, Bip39WordsNum

# Saka Telegram Bot Token dinka na gaskiya a nan
TOKEN = "PASTE_YOUR_BOT_TOKEN_HERE"

# Engine na samar da BIP-39 Mnemonic Seed Phrase
def generate_mnemonic(words_count: int) -> str:
    if words_count == 12:
        return Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_12)
    elif words_count == 24:
        return Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_24)
    return ""

# Command Handler na /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [['Generate 12 Words', 'Generate 24 Words']]
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "Welcome! Please select an option below to generate a 12 or 24-word seed phrase with a valid BIP-39 checksum:",
        reply_markup=markup
    )

# Message/Button Handler
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    if user_text == 'Generate 12 Words':
        seed_phrase = generate_mnemonic(12)
        response = (
            f"**12-Word Seed Phrase:**\n\n"
            f"`{seed_phrase}`\n\n"
            f"*This mnemonic includes a valid BIP-39 checksum on the 12th word.*"
        )
        await update.message.reply_text(response, parse_mode="Markdown")

    elif user_text == 'Generate 24 Words':
        seed_phrase = generate_mnemonic(24)
        response = (
            f"**24-Word Seed Phrase:**\n\n"
            f"`{seed_phrase}`\n\n"
            f"*This mnemonic includes a valid BIP-39 checksum on the 24th word.*"
        )
        await update.message.reply_text(response, parse_mode="Markdown")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))

    print("Bot is running...")
    app.run_polling()
