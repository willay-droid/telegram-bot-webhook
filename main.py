import os
import json
import base64
import gspread
from flask import Flask, request
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, ContextTypes
from telegram.ext import Application, ApplicationBuilder

app = Flask(__name__)

# === SETUP GOOGLE SHEET ===
credentials_json = base64.b64decode(os.environ["GOOGLE_CREDENTIALS_BASE64"])
creds_dict = json.loads(credentials_json)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
worksheet = client.open("ACTIVE_DEVICE_INFO_JATIMSEL_TIM").worksheet("ACTIVE_DEVICE_INFO_JATIMSEL_TIM")

# === TELEGRAM SETUP ===
BOT_TOKEN = os.environ["TOKEN_BOT"]
bot = Bot(token=BOT_TOKEN)

application = ApplicationBuilder().token(BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot Helpdesk aktif. Gunakan /port CODE atau /portid PORT_ID.")

async def get_port(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Gunakan format: /port CODE")
        return
    code = context.args[0].strip().upper()
    records = worksheet.get_all_records()
    result = next((row for row in records if row.get("CODE", "").upper() == code), None)
    if result:
        await update.message.reply_text(f"PORT_ID: {result.get('PORT_ID')}\nTARGET_ID: {result.get('TARGET_ID')}")
    else:
        await update.message.reply_text("Data tidak ditemukan.")

async def get_portid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Gunakan format: /portid PORT_ID")
        return
    pid = context.args[0].strip().upper()
    records = worksheet.get_all_records()
    result = next((row for row in records if row.get("PORT_ID", "").upper() == pid), None)
    if result:
        await update.message.reply_text(f"PORT_NUMBER: {result.get('PORT_NUMBER')}\nNAME_NE: {result.get('NAME_NE')}")
    else:
        await update.message.reply_text("Data tidak ditemukan.")

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("port", get_port))
application.add_handler(CommandHandler("portid", get_portid))

# === FLASK ROUTE UNTUK WEBHOOK ===
@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    application.update_queue.put(update)
    return "OK"