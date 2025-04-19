
import os
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

with open("bot_data.json", "r", encoding="utf-8") as f:
    bot_data = json.load(f)

def get_main_menu():
    return [["مناهج الإنجليزي", "مناهج الحاسوب"],
            ["مناهج التمهيدي", "المناهج الملحقة"],
            ["للتواصل معنا"]]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    menu = get_main_menu()

    if user_id == ADMIN_ID:
        menu.append(["لوحة التحكم"])

    markup = ReplyKeyboardMarkup(menu, resize_keyboard=True)
    await update.message.reply_text("مرحباً بك في البوت", reply_markup=markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_text(f"تم اختيار: {text}")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
