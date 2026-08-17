import os
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# گرفتن کلیدها از تنظیمات رندر
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# تنظیمات جمینای
genai.configure(api_key=GEMINI_API_KEY)

# ساختار دادن به مغز ربات برای مدیریت کلاس‌ها و تولید محتوا
system_prompt = """
تو «جارویس» هستی؛ یک دستیار هوشمند، حرفه‌ای و همه‌کاره برای یک مدرس زبان انگلیسی و آلمانی.
وظایف اصلی تو عبارتند از:
۱. مدیریت برنامه‌های کلاسی: باید کلاس‌های زبان‌آموزان (نام، روز، ساعت، و زبان مربوطه) را به خاطر بسپاری. اگر من گفتم کلاسی را اضافه، حذف یا جابجا کن، آن را در حافظه‌ات ویرایش کن و برنامه جدیدِ هفته را به صورت یک لیست مرتب به من نشان بده.
۲. سازمان‌دهی کارها: کمک به مدیریت کارهای روزانه و زمان‌بندی شخصی من.
۳. تولید محتوای آموزشی: نوشتن متن‌های آموزشی، تمرین‌های گرامری، داستان‌های کوتاه، کوئیزها و متریال‌های آموزشی برای زبان‌های انگلیسی و آلمانی (از سطح A1 تا C2) با بالاترین کیفیت.
۴. ایده‌پردازی: پیشنهاد روش‌های تدریس خلاقانه، بازی‌های کلاسی و موضوعات جذاب برای بحث آزاد (Free Discussion).
۵. تصحیح و ترجمه: کمک به بررسی، اصلاح و ترجمه متن‌ها.

لحن تو باید محترمانه، دوستانه و بسیار کارآمد باشد. هر بار که تغییری در برنامه کلاسی می‌دهی، تایید کن و وضعیت جدید را گزارش بده.
"""

model = genai.GenerativeModel(
    model_name='gemini-1.5-pro',
    system_instruction=system_prompt
)

# یک دیکشنری برای نگهداری حافظه مکالمات هر کاربر
user_chats = {}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # وقتی ربات استارت می‌شود، یک حافظه جدید و خالی برای شما ساخته می‌شود
    user_chats[user_id] = model.start_chat(history=[])
    
    welcome_text = (
        "سلام! من جارویس هستم، دستیار شخصی و آموزشی شما. 🤖\n\n"
        "شما می‌تونید برنامه کلاس‌هاتون رو به من بگید تا مدیریت کنم (مثلا: فردا ساعت ۵ با علی کلاس آلمانی دارم)، "
        "یا برای تولید محتوا، طراحی تمرین و ایده‌پردازی زبان انگلیسی و آلمانی از من کمک بگیرید.\n\n"
        "چه کاری می‌تونم براتون انجام بدم؟"
    )
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text
    
    # اگر ربات ری‌استارت شده بود و کاربری پیام داد، سریع یک حافظه برایش می‌سازیم
    if user_id not in user_chats:
        user_chats[user_id] = model.start_chat(history=[])
        
    chat_session = user_chats[user_id]
    
    # نمایش وضعیت "در حال تایپ..." در تلگرام
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    try:
        # ارسال پیام به همراه حافظه قبلی به جمینای
        response = chat_session.send_message(user_text)
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"خطایی رخ داد. لطفا دوباره تلاش کنید.\nجزئیات خطا: {e}")

if __name__ == '__main__':
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
