import logging
import csv
from datetime import datetime
import gspread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.constants import ParseMode
from oauth2client.service_account import ServiceAccountCredentials

# Ganti dengan token dari BotFather
TOKEN = '7238211926:AAFIEXE_Htq71HmkMYodMFX-ICthsIXiAK0'

# Setup kredensial Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Akses spreadsheet dan worksheet
sheet_url = "https://docs.google.com/spreadsheets/d/1KUI_8JeLixhcz19wEuo_mOzysjTjtlYIK1R0Zd1y_Do/edit"
worksheet = client.open_by_url(sheet_url).worksheet("ACTIVE_DEVICE_INFO_JATIMSEL_TIM")

# Fungsi log pencarian
def log_search(username: str, key: str, result: str):
    with open("log.csv", mode="a", newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), username, key, result])

# /start
async def startt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🖐️ *Selamat datang di Bot Helpdesk!*\n\n"
        "Bot ini membantu kamu mengecek data dari Google Spreadsheet.\n\n"
        "*Perintah yang tersedia:*\n"
        "`/port <CODE>` – Cek PORT_ID dan TARGET_ID dari CODE\n"
        "`/portid <PORT_ID>` – Cek PORT_NUMBER dan NAME_NE dari PORT_ID\n"
        "`/ipbb <IP_BB>` – Cek MERK, VLAN_BROADBAND dan VLAN_VOICE dari IP_BB\n"
        "`/log` – Lihat log pencarian terakhir\n"
        "`/help` – Tampilkan panduan ini kapan saja\n\n"
        "Contoh: `/port A123` atau `/portid P-001`"
    )
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

# /help
async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "*Panduan Bot Helpdesk*\n\n"
        "`/port <CODE>` – Cek PORT_ID dan TARGET_ID dari CODE\n"
        "`/portid <PORT_ID>` – Cek PORT_NUMBER dan NAME_NE dari PORT_ID\n"
        "`/ipbb <IP_BB>` – Cek MERK, VLAN_BROADBAND dan VLAN_VOICE dari IP_BB\n"
        "`/log` – Lihat 5 log pencarian terakhir\n\n"
        "Contoh: `/port A123` atau `/portid P-001`"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

# /log
async def show_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open("log.csv", "r", encoding="utf-8") as file:
            lines = file.readlines()[-5:]

        if not lines:
            await update.message.reply_text("Belum ada log pencarian.")
            return

        log_text = "*Log Terakhir:*\n"
        for line in lines:
            waktu, user, key, hasil = line.strip().split(",", 3)
            log_text += f"- `{waktu}` oleh *{user}*: `{key}` → {hasil}\n"

        await update.message.reply_text(log_text, parse_mode=ParseMode.MARKDOWN)

    except FileNotFoundError:
        await update.message.reply_text("Log belum tersedia.")

# /port <CODE>
async def get_port(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = user.username or f"{user.first_name} {user.last_name or ''}".strip()

    if len(context.args) != 1:
        await update.message.reply_text("Gunakan format: /port CODE")
        return

    code_input = context.args[0].strip().upper()
    try:
        records = worksheet.get_all_records()
        result = next((row for row in records if row.get("CODE", "").upper() == code_input), None)

        if result:
            port_id = result.get("PORT_ID", "-")
            target_id = result.get("TARGET_ID", "-")
            response = (
                f"📦 Hasil untuk CODE {code_input}:\n"
                f"PORT_ID: {port_id}\n"
                f"TARGET_ID: {target_id}"
            )
        else:
            response = f"Kode '{code_input}' tidak ditemukan."

        log_search(username, code_input, response)
        await update.message.reply_text(response)

    except Exception as e:
        error_msg = f"Terjadi kesalahan: {e}"
        log_search(username, code_input, error_msg)
        await update.message.reply_text(error_msg)

# /portid <PORT_ID>
async def get_by_port_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = user.username or f"{user.first_name} {user.last_name or ''}".strip()

    if len(context.args) != 1:
        await update.message.reply_text("Gunakan format: /portid PORT_ID")
        return

    port_id_input = context.args[0].strip().upper()
    try:
        records = worksheet.get_all_records()
        result = next((row for row in records if row.get("PORT_ID", "").upper() == port_id_input), None)

        if result:
            port_number = result.get("PORT_NUMBER", "-")
            name_ne = result.get("NAME_NE", "-")
            response = (
                f"🔍 Hasil untuk PORT_ID {port_id_input}:\n"
                f"PORT_NUMBER: {port_number}\n"
                f"NAME_NE: {name_ne}"
            )
        else:
            response = f"PORT_ID '{port_id_input}' tidak ditemukan."

        log_search(username, port_id_input, response)
        await update.message.reply_text(response)

    except Exception as e:
        error_msg = f"Terjadi kesalahan: {e}"
        log_search(username, port_id_input, error_msg)
        await update.message.reply_text(error_msg)

# /ipbb <IP_BB>
async def get_by_ipbb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = user.username or f"{user.first_name} {user.last_name or ''}".strip()

    if len(context.args) != 1:
        await update.message.reply_text("Gunakan format: /ipbb IP_ADDRESS")
        return

    ip_input = context.args[0].strip()
    try:
        records = worksheet.get_all_records()
        result = next((row for row in records if row.get("IP_BB", "").strip() == ip_input), None)

        if result:
            name_gpon = result.get("NAME_NE", "-")
            merk = result.get("MERK", "-")
            vlan_bb = result.get("VLAN_BROADBAND", "-")
            vlan_voice = result.get("VLAN_VOICE", "-")
            response = (
                f"🌐 Hasil untuk IP_BB {ip_input}:\n"
                f"HOSTNAME: {name_gpon}\n"
                f"MERK: {merk}\n"
                f"VLAN_BROADBAND: {vlan_bb}\n"
                f"VLAN_VOICE: {vlan_voice}"
            )
        else:
            response = f"IP_BB '{ip_input}' tidak ditemukan."

        log_search(username, ip_input, response)
        await update.message.reply_text(response)

    except Exception as e:
        error_msg = f"Terjadi kesalahan: {e}"
        log_search(username, ip_input, error_msg)
        await update.message.reply_text(error_msg)

async def get_sto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) != 1:
        await update.message.reply_text("Gunakan format: /sto NAMA_STO")
        return

    sto_input = context.args[0].strip().upper()
    records = worksheet.get_all_records()

    # Ambil semua pasangan unik (NAME_NE, VENDOR) dengan STO yang sesuai
    seen = set()
    unique_results = []

    for row in records:
        if row.get("STO", "").strip().upper() == sto_input:
            name = row.get("NAME_NE", "-").strip()
            vendor = row.get("VENDOR", "-").strip()
            key = (name, vendor)
            if key not in seen:
                seen.add(key)
                unique_results.append(key)

    if unique_results:
        response = f"📍 *Perangkat di STO {sto_input}* ({len(unique_results)} hasil unik):\n"
        for i, (name, vendor) in enumerate(unique_results[:20], 1):
            response += f"{i}. {name}  _{vendor}_\n"
    else:
        response = f"Tidak ditemukan perangkat untuk STO '{sto_input}'."

    await update.message.reply_text(response, parse_mode="Markdown")

# Jalankan bot
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", startt))
    app.add_handler(CommandHandler("help", show_help))
    app.add_handler(CommandHandler("log", show_log))
    app.add_handler(CommandHandler("port", get_port))
    app.add_handler(CommandHandler("portid", get_by_port_id))
    app.add_handler(CommandHandler("ipbb", get_by_ipbb))
    app.add_handler(CommandHandler("sto", get_sto))
    app.run_polling()

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
