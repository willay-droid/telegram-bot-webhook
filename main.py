import os
import json
import base64
import gspread
from flask import Flask, request
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.ext import Application, ApplicationBuilder

app = Flask(__name__)

# === SETUP GOOGLE SHEET ===
credentials_json = base64.b64decode(os.environ["GOOGLE_CREDENTIALS_BASE64"])
creds_dict = json.loads(credentials_json)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
# DEBUG: Tampilkan semua spreadsheet yang bisa dilihat oleh service account
print("📄 Spreadsheet yang bisa diakses oleh Service Account:")
try:
    spreadsheet_list = client.openall()
    for sheet in spreadsheet_list:
        print("🔹", sheet.title)
except Exception as e:
    print("❌ Gagal menampilkan daftar spreadsheet:", e)
worksheet = client.open("ID_SLOT_PORT").worksheet("ACTIVE_DEVICE_INFO_JATIMSEL_TIM")

# === TELEGRAM SETUP ===
BOT_TOKEN = os.environ["TOKEN_BOT"]
bot = Bot(token=BOT_TOKEN)

application = ApplicationBuilder().token(BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot Helpdesk aktif. Gunakan /port CODE atau /portid PORT_ID.")

async def get_port(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) != 1:
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
    if not context.args or len(context.args) != 1:
        await update.message.reply_text("Gunakan format: /portid PORT_ID")
        return
    pid = context.args[0].strip().upper()
    records = worksheet.get_all_records()
    result = next((row for row in records if row.get("PORT_ID", "").upper() == pid), None)
    if result:
        await update.message.reply_text(f"PORT_NUMBER: {result.get('PORT_NUMBER')}\nNAME_NE: {result.get('NAME_NE')}")
    else:
        await update.message.reply_text("Data tidak ditemukan.")

async def get_ipbb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) != 1:
        await update.message.reply_text("Gunakan format: /ipbb IP_BB")
        return
    ipbb = context.args[0].strip().upper()
    records = worksheet.get_all_records()
    result = next((row for row in records if row.get("IP_BB", "").upper() == ipbb), None)
    if result:
        await update.message.reply_text(f"HOSTNAME: {result.get('NAME_NE')}\nMERK: {result.get('MERK')}\nVLAN_BROADBAND: {result.get('VLAN_BROADBAND')}\nVLAN_VOICE: {result.get('VLAN_VOICE')}")
    else:
        await update.message.reply_text("Data tidak ditemukan.")

async def get_sto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) != 1:
        await update.message.reply_text("Gunakan format: /sto STO")
        return

    sto_input = context.args[0].strip().upper()
    records = worksheet.get_all_records()
    matches = [row for row in records if row.get("STO", "").upper() == sto_input]

    if matches:
        response = f"📍 *Hasil untuk STO {sto_input}* ({len(matches)} hasil):\n"
        for i, row in enumerate(matches[:20], 1):  # batasi 20 hasil teratas
            response += f"{i}. {row.get('NAME_NE', '-')}\n"
        await update.message.reply_text(response, parse_mode="Markdown")
    else:
        await update.message.reply_text(f"Tidak ditemukan NAME_NE untuk STO '{sto_input}'.")

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("port", get_port))
application.add_handler(CommandHandler("portid", get_portid))
application.add_handler(CommandHandler("ipbb", get_ipbb))
application.add_handler(CommandHandler("sto", get_sto))

# === FLASK ROUTE UNTUK WEBHOOK ===
@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    application.update_queue.put(update)
    return "OK"

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
