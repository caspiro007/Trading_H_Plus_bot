
import os
import json
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

with open("bot_data.json", "r", encoding="utf-8") as f:
    bot_data = json.load(f)

def get_main_menu():
    return [["مناهج الإنجليزي", "مناهج الحاسوب"],
            ["مناهج التمهيدي", "المناهج الملحقة"],
            ["للتواصل معنا"]]

def get_admin_menu():
    return [["إضافة ملفات", "عرض الملفات"], ["رجوع"]]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    context.user_data.clear()
    menu = get_main_menu()

    if user_id == ADMIN_ID:
        menu.append(["لوحة التحكم"])

    markup = ReplyKeyboardMarkup(menu, resize_keyboard=True)
    await update.message.reply_text("مرحباً بك في البوت", reply_markup=markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if text == "رجوع":
        await start(update, context)
        return

    if text == "لوحة التحكم" and user_id == ADMIN_ID:
        markup = ReplyKeyboardMarkup(get_admin_menu(), resize_keyboard=True)
        await update.message.reply_text("لوحة التحكم:", reply_markup=markup)
        return

    if text in ["إضافة ملفات", "عرض الملفات"] and user_id == ADMIN_ID:
        await update.message.reply_text(f"ميزة '{text}' تحت التطوير.")
        return

    # متابعة تسلسل الأزرار
    level = context.user_data.get("level", 1)
    current = context.user_data.get("path", [])

    if level == 1 and text in bot_data:
        context.user_data["path"] = [text]
        context.user_data["level"] = 2
        markup = ReplyKeyboardMarkup([[k] for k in bot_data[text].keys()] + [["رجوع"]], resize_keyboard=True)
        await update.message.reply_text("اختر القسم:", reply_markup=markup)
    elif level == 2 and len(current) == 1 and text in bot_data[current[0]]:
        context.user_data["path"].append(text)
        context.user_data["level"] = 3
        markup = ReplyKeyboardMarkup([[k] for k in bot_data[current[0]][text].keys()] + [["رجوع"]], resize_keyboard=True)
        await update.message.reply_text("اختر نوع المحتوى:", reply_markup=markup)
    elif level == 3 and len(current) == 2 and text in bot_data[current[0]][current[1]]:
        context.user_data["path"].append(text)
        context.user_data["level"] = 4
        markup = ReplyKeyboardMarkup([[k] for k in bot_data[current[0]][current[1]][text].keys()] + [["رجوع"]], resize_keyboard=True)
        await update.message.reply_text("اختر الصف:", reply_markup=markup)
    elif level == 4 and len(current) == 3:
        current_path = bot_data
        for key in context.user_data["path"]:
            current_path = current_path[key]
        if text in current_path:
            files = current_path[text]
            if files:
                for f in files:
                    file_id = f["file_id"]
                    file_name = f.get("file_name", "")
                    file_type = f.get("type", "document")
                    if file_type == "document":
                        await update.message.reply_document(file_id, caption=file_name)
                    elif file_type == "audio":
                        await update.message.reply_audio(file_id, caption=file_name)
                    elif file_type == "video":
                        await update.message.reply_video(file_id, caption=file_name)
                    elif file_type == "photo":
                        await update.message.reply_photo(file_id, caption=file_name)
                    else:
                        await update.message.reply_document(file_id, caption=file_name)
                return
            else:
                await update.message.reply_text("لا توجد ملفات.")
        else:
            await update.message.reply_text("لا توجد ملفات لهذا الخيار.")
    else:
        await update.message.reply_text("يرجى اختيار خيار من القائمة.")

# لتخزين الملفات التي يرسلها الأدمن
pending_files = {}

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.username != ADMIN_USERNAME:
        return  # تجاهل أي ملفات من غير الأدمن

    msg = update.message
    file = msg.document or msg.audio or msg.video or (msg.photo[-1] if msg.photo else None)
    file_type = 'document' if msg.document else 'audio' if msg.audio else 'video' if msg.video else 'photo'

    if not file:
        await msg.reply_text("الملف غير مدعوم.")
        return

    file_id = file.file_id
    file_name = getattr(file, 'file_name', 'بدون اسم')

    # خزّن مؤقتاً
    pending_files[user.id] = {
        "file_id": file_id,
        "file_name": file_name,
        "type": file_type
    }

    await msg.reply_text(
        "تم استلام الملف بنجاح!\nالرجاء إرسال مسار الحفظ (مثال: مناهج الإنجليزي > سمارت إنجلش > الصوتيات > الصف الأول)"
    )

    async def handle_path_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in pending_files:
        return

    path_text = update.message.text.strip()
    levels = [lvl.strip() for lvl in path_text.split(">")]

    if len(levels) != 4:
        await update.message.reply_text("يرجى إدخال المسار بدقة يتكون من 4 مستويات مفصولة بـ '>'")
        return

    # جهّز البيانات
    file_data = pending_files.pop(user.id)
    current = bot_data
    for level in levels[:-1]:
        current = current.setdefault(level, {})
    final_level = levels[-1]
    current.setdefault(final_level, []).append(file_data)

    # احفظ في الملف
    save_bot_data()

    await update.message.reply_text("تم حفظ الملف بنجاح!")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Document.ALL | filters.Audio.ALL | filters.Video.ALL | filters.PHOTO, handle_file))
app.add_handler(MessageHandler(filters.TEXT & filters.User(username=ADMIN_USERNAME), handle_path_input))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
