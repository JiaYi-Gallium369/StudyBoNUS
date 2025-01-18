import os
import httpx

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, CallbackQueryHandler

from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_fixed
import logging
from typing import List

load_dotenv()
TELEGRAM_BOT_TOKEN = "8122445200:AAF6Kh0kqdQyS-y-Y1wfrQ_6EsxiaiVCNVU"

def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
    ["A", "B"],
    ["C", "D"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text("Choose an option: ", reply_markup=reply_markup)


def notes(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Do it yourself la')

def main() -> None:
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("notes", notes))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()