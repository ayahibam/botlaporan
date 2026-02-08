import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ========= ENV =========
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SHEET_ID = os.getenv("SHEET_ID")

# ========= GOOGLE SHEET =========
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

spreadsheet = client.open_by_key(SHEET_ID)

# MASTER SHEET
try:
    data_sheet = spreadsheet.worksheet("DATA")
except:
    data_sheet = spreadsheet.add_worksheet("DATA",1000,5)
    data_sheet.append_row(["NAMA","GOLD","CHAR","SERVER"])

# TOTAL SERVER
try:
    total_sheet = spreadsheet.worksheet("TOTAL_PER_SERVER")
except:
    total_sheet = spreadsheet.add_worksheet("TOTAL_PER_SERVER",1000,3)
    total_sheet.append_row(["SERVER","TOTAL","FORMAT"])

# ========= HELPER =========

def parse_gold(val):

    val = val.upper().strip()

    if val.endswith("M"):
        return int(float(val.replace("M","")) * 1000000)

    return int(val)

def format_gold(n):

    if n >= 1000000:
        return f"{n/1000000:.1f}".rstrip("0").rstrip(".")+"M"

    return str(n)

# ========= HANDLER =========

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if "|" not in text:
        return

    try:

        nama, gold, char, server = [x.strip() for x in text.split("|")]

        gold_val = parse_gold(gold)

        # ===== SAVE MASTER DATA =====
        data_sheet.append_row([nama, gold_val, char, server])

        # ===== TAB PER NAMA (FINAL FIX) =====
        sheet_name = nama.upper()

        try:
            user_sheet = spreadsheet.worksheet(sheet_name)
        except:
            user_sheet = spreadsheet.add_worksheet(sheet_name,1000,5)
            user_sheet.append_row(["NAMA","GOLD","CHAR","SERVER"])

        user_sheet.append_row([
        nama,
        format_gold(gold_val),
        char,
        server
    ])

        # ===== TOTAL PER SERVER =====
        rows = total_sheet.get_all_values()

        server_upper = server.upper()
        found = False

        for i,row in enumerate(rows):

            if row and row[0] == server_upper:

                try:
                    existing = int(row[1])
                except Exception:
                    existing = 0

                total = existing + gold_val
                total_sheet.update_cell(i+1, 2, total)
                total_sheet.update_cell(i+1, 3, format_gold(total))
                found = True
                break

        if not found:
            total_sheet.append_row([server_upper, gold_val, format_gold(gold_val)])

        await update.message.reply_text(
            f"✅ {nama} tercatat: {format_gold(gold_val)} ({server})"
        )

    except Exception as e:
        print("ERROR:", e)

# ========= RUN =========

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(
    MessageHandler(filters.TEXT & (~filters.COMMAND), handler)
)

print("BOT RUNNING...")
app.run_polling()
