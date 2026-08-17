import os
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ---------------------------
# تنظیمات و کلیدهای API
# ---------------------------
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    print("خطا: کلیدهای API تنظیم نشده‌اند (TELEGRAM_TOKEN یا GEMINI_API_KEY).")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name='gemini-1.5-flash')

# حافظه‌ی هر کاربر (chat history) در حافظه‌ی موقت برنامه نگهداری می‌شود
user_chats = {}

# ---------------------------
# پرامپت سیستمی جارویس
# ---------------------------
system_prompt = """
تو «جارویس» هستی؛ دستیار هوشمند، حرفه‌ای و همه‌کاره یک مدرس زبان انگلیسی و آلمانی.
وظایف اصلی تو:
۱. مدیریت برنامه‌های کلاسی (حفظ کردن، اضافه، حذف و جابجایی زمان‌ها)
۲. سازمان‌دهی کارهای روزانه
۳. تولید محتوای آموزشی (انگلیسی و آلمانی از سطح A1 تا C2)
۴. ایده‌پردازی، طراحی کوئیز و تصحیح متن‌ها
لطفاً لحنت محترمانه و دوستانه باشد و هر تغییری در برنامه‌ها دادی، برنامه جدید را نشان بده.
"""

# ---------------------------
# هندلرها
# ---------------------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_chats[user_id] = model.start_chat(history=[
        {"role": "user", "parts": [system_prompt]},
        {"role": "model", "parts": ["آماده‌ام طبق دستورات شما برنامه‌ها و محتوا را مدیریت کنم."]}
    ])
    await update.message.reply_text("سلام! من جارویس هستم. منتظر برنامه‌های کلاسی تو هستم.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    if user_id not in user_chats:
        user_chats[user_id] = model.start_chat(history=[
            {"role": "user", "parts": [system_prompt]},
            {"role": "model", "parts": ["آماده کارم."]}
        ])

    chat_session = user_chats[user_id]
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    try:
        response = chat_session.send_message(user_text)
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"خطا در ارتباط با هوش مصنوعی: {e}")


# ---------------------------
# اجرای برنامه (Webhook mode برای Render)
# ---------------------------
if __name__ == '__main__':
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    PORT = int(os.environ.get("PORT", 10000))
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")

    if not RENDER_URL:
        print("خطا: RENDER_EXTERNAL_URL تنظیم نشده است.")
        print("مطمئن شو که نوع سرویس در Render روی 'Web Service' تنظیم شده، نه 'Background Worker'.")
        exit(1)

    WEBHOOK_URL = f"{RENDER_URL}/{TELEGRAM_TOKEN}"
    print(f"در حال راه‌اندازی جارویس با webhook در آدرس: {WEBHOOK_URL}")

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TELEGRAM_TOKEN,
        webhook_url=WEBHOOK_URL,
        drop_pending_updates=True,
    )
