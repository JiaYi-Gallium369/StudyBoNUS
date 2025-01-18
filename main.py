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
    ["SoC", "UPCOMING"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text("Choose an option: ", reply_markup=reply_markup)
    if update.message.text == "SoC":
        SoC(update, context)

def SoC(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.chat_id
    drive_file_url = "https://drive.google.com/file/d/1cY6yrE8o6Io-w8ufLQgT2Nt7Um9PWkxp/view"
    response = requests.get(drive_file_url)
    if response.status_code == 200:
        with open("temp.pdf", "wb") as pdf_file:
            pdf_file.write(response.content)
        
        # Send the PDF to the user
        context.bot.send_document(chat_id=chat_id, document=open("temp.pdf", "rb"))
    else:
        update.message.reply_text("Failed to fetch the file from Google Drive.")

def notes(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Do it yourself la')

def main() -> None:
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("notes", notes))
    dispatcher.add_handler(CommandHandler("SoC", SoC))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()