
import json
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# تحميل البيانات
DATA_FILE = "bot_data.json"
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        bot_data = json.load(f)
else:
    bot_data = {}

def save_bot_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(bot_data, f, ensure_ascii=False, indent=2)

# إعدادات
ADMIN_USERNAME = "Trading_House_Plus_bot"
pending_files = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.username == ADMIN_USERNAME:
        await update.message.reply_text("مرحباً بك في لوحة تحكم الأدمن.")
    else:
        await update.message.reply_text("مرحباً بك! اختر من القائمة.")

# استلام الملفات من الأدمن
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.username != ADMIN_USERNAME:
        return

    msg = update.message
    file = msg.document or msg.audio or msg.video or (msg.photo[-1] if msg.photo else None)
    file_type = 'document' if msg.document else 'audio' if msg.audio else 'video' if msg.video else 'photo'

    if not file:
        await msg.reply_text("الملف غير مدعوم.")
        return

    file_id = file.file_id
    file_name = getattr(file, 'file_name', 'بدون اسم')

    pending_files[user.id] = {
        "file_id": file_id,
        "file_name": file_name,
        "type": file_type
    }

    await msg.reply_text("تم استلام الملف بنجاح!\nالرجاء إرسال مسار الحفظ (مثال: مناهج الإنجليزي > سمارت إنجلش > الصوتيات > الصف الأول)")

# حفظ الملف بناء على المسار
async def handle_path_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in pending_files:
        return

    path_text = update.message.text.strip()
    levels = [lvl.strip() for lvl in path_text.split(">")]

    if len(levels) != 4:
        await update.message.reply_text("يرجى إدخال المسار بدقة يتكون من 4 مستويات مفصولة بـ '>'")
        return

    file_data = pending_files.pop(user.id)
    current = bot_data
    for level in levels[:-1]:
        current = current.setdefault(level, {})
    final_level = levels[-1]
    current.setdefault(final_level, []).append(file_data)
    save_bot_data()

    await update.message.reply_text("تم حفظ الملف بنجاح!")

def main():
    token = os.getenv("BOT_TOKEN")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.Audio.ALL | filters.Video.ALL | filters.PHOTO, handle_file))
    app.add_handler(MessageHandler(filters.TEXT & filters.User(username=ADMIN_USERNAME), handle_path_input))
    app.run_polling()

if __name__ == "__main__":
    main()
