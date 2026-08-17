import os
import asyncio
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# گرفتن کلیدها
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    print("خطا: کلیدهای تلگرام یا جمینای پیدا نشد! لطفا در تنظیمات Render آنها را وارد کنید.")
    exit(1)

# تنظیمات جمینای
genai.configure(api_key=GEMINI_API_KEY)
# استفاده از gemini-1.5-flash که سریع‌ترین مدل برای چت‌بات‌ها است
model = genai.GenerativeModel(model_name='gemini-1.5-flash')
user_chats = {}

system_prompt = """
تو «جارویس» هستی؛ یک دستیار هوشمند، حرفه‌ای و همه‌کاره برای یک مدرس زبان انگلیسی و آلمانی.
وظایف اصلی تو:
۱. مدیریت برنامه‌های کلاسی: باید کلاس‌های زبان‌آموزان (نام، روز، ساعت، و زبان مربوطه) را به خاطر بسپاری.
۲. تولید محتوای آموزشی: نوشتن تمرین‌های گرامری، داستان‌های کوتاه، و متریال‌های آموزشی برای انگلیسی و آلمانی (A1 تا C2).
۳. ایده‌پردازی: پیشنهاد روش‌های تدریس خلاقانه.
"""

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_chats[user_id] = model.start_chat(history=[
        {"role": "user", "parts": [system_prompt]},
        {"role": "model", "parts": ["متوجه شدم. من جارویس هستم. منتظر دستورات کلاسی و آموزشی شما هستم."]}
    ])
    await update.message.reply_text("سلام! من جارویس هستم. چه کلاسی رو می‌خوای اضافه کنی؟")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text
    
    if user_id not in user_chats:
        user_chats[user_id] = model.start_chat(history=[
            {"role": "user", "parts": [system_prompt]},
            {"role": "model", "parts": ["متوجه شدم. آماده کارم."]}
        ])
        
    chat_session = user_chats[user_id]
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    try:
        response = chat_session.send_message(user_text)
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text("ارتباط با مغز جمینای قطع شد. لطفاً دوباره تلاش کن.")
        print(f"Error: {e}")

# اجرای ساده و بدون دردسر با drop_pending_updates
if __name__ == '__main__':
    # این دستور تضمین می‌کند که کدهای قبلی در تلگرام گیر نکنند
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("شروع اجرای جارویس...")
    # استفاده از حلقه ساده‌تر برای جلوگیری از ارور Conflict
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
