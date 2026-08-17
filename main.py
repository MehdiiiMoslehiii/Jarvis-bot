import os
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# دریافت اطلاعات از سرور رندر
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
PORT = int(os.environ.get("PORT", 10000))

# تنظیمات اتصال به مغز جمینای (سازگار با تمامی نسخه‌ها)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name='gemini-pro')
user_chats = {}

# دستورالعمل‌های جارویس
system_prompt = """
تو «جارویس» هستی؛ دستیار هوشمند و همه‌کاره یک مدرس زبان انگلیسی و آلمانی.
وظایف اصلی تو:
۱. مدیریت برنامه‌های کلاسی (حفظ کردن، اضافه، حذف و جابجایی زمان‌ها)
۲. سازمان‌دهی کارهای روزانه
۳. تولید محتوای آموزشی (انگلیسی و آلمانی از سطح A1 تا C2)
۴. ایده‌پردازی، طراحی کوئیز و تصحیح متن‌ها
لطفاً لحنت محترمانه و دوستانه باشد و هر تغییری در برنامه‌ها دادی، برنامه جدید را نشان بده.
"""

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # اعمال شخصیت جارویس به صورت مستقیم در حافظه (بدون ارور)
    user_chats[user_id] = model.start_chat(history=[
        {"role": "user", "parts": [system_prompt]},
        {"role": "model", "parts": ["متوجه شدم. من جارویس هستم و آماده‌ام طبق دستورات شما برنامه‌ها و محتوا را مدیریت کنم."]}
    ])
    
    await update.message.reply_text("سلام! من جارویس هستم، دستیار شخصی و آموزشی شما. 🤖\nبرنامه‌هاتون رو به من بگید.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text
    
    if user_id not in user_chats:
        user_chats[user_id] = model.start_chat(history=[
            {"role": "user", "parts": [system_prompt]},
            {"role": "model", "parts": ["آماده دریافت دستورات هستم."]}
        ])
        
    chat_session = user_chats[user_id]
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    try:
        response = chat_session.send_message(user_text)
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"یک لحظه دچار مشکل شدم. جزئیات: {e}")

if __name__ == '__main__':
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # -----------------------------------------------------------------
    # راه حل قطعی و نهایی: استفاده از Webhook به جای Polling
    # با این کار ارور Conflict کلا غیرممکن می‌شود!
    # -----------------------------------------------------------------
    if RENDER_EXTERNAL_URL:
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TELEGRAM_TOKEN,
            webhook_url=f"{RENDER_EXTERNAL_URL}/{TELEGRAM_TOKEN}"
        )
    else:
        app.run_polling(drop_pending_updates=True)
