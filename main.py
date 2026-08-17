import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ==========================================
# ترفند گول زدن رندر (ساخت یک وب‌سرور فیک)
# ==========================================
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/plain')
        self.end_headers()
        self.wfile.write(b"Jarvis is alive!")

def run_dummy_server():
    # رندر یک پورت به ما می‌ده، اگر نداد از 10000 استفاده می‌کنیم
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

# وب‌سرور فیک رو تو یک نخ (Thread) جداگانه روشن می‌کنیم
threading.Thread(target=run_dummy_server, daemon=True).start()

# ==========================================
# کدهای اصلی ربات جارویس
# ==========================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
system_prompt = """
تو «جارویس» هستی؛ یک دستیار هوشمند، حرفه‌ای و همه‌کاره برای یک مدرس زبان انگلیسی و آلمانی.
وظایف اصلی تو عبارتند از:
۱. مدیریت برنامه‌های کلاسی: باید کلاس‌های زبان‌آموزان (نام، روز، ساعت، و زبان مربوطه) را به خاطر بسپاری. اگر من گفتم کلاسی را اضافه، حذف یا جابجا کن، آن را در حافظه‌ات ویرایش کن و برنامه جدیدِ هفته را به صورت یک لیست مرتب به من نشان بده.
۲. سازمان‌دهی کارها: کمک به مدیریت کارهای روزانه و زمان‌بندی شخصی من.
۳. تولید محتوای آموزشی: نوشتن متن‌های آموزشی، تمرین‌های گرامری، داستان‌های کوتاه، کوئیزها و متریال‌های آموزشی برای زبان‌های انگلیسی و آلمانی (از سطح A1 تا C2) با بالاترین کیفیت.
۴. ایده‌پردازی: پیشنهاد روش‌های تدریس خلاقانه، بازی‌های کلاسی و موضوعات جذاب برای بحث آزاد.
۵. تصحیح و ترجمه: کمک به بررسی، اصلاح و ترجمه متن‌ها.

لحن تو باید محترمانه، دوستانه و بسیار کارآمد باشد. هر بار که تغییری در برنامه کلاسی می‌دهی، تایید کن و وضعیت جدید را گزارش بده.
"""
model = genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=system_prompt)
user_chats = {}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_chats[user_id] = model.start_chat(history=[])
    welcome_text = (
        "سلام! من جارویس هستم، دستیار شخصی و آموزشی شما. 🤖\n\n"
        "شما می‌تونید برنامه کلاس‌هاتون رو به من بگید تا مدیریت کنم، "
        "یا برای تولید محتوا، طراحی تمرین و ایده‌پردازی زبان انگلیسی و آلمانی از من کمک بگیرید."
    )
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text
    if user_id not in user_chats:
        user_chats[user_id] = model.start_chat(history=[])
    chat_session = user_chats[user_id]
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    try:
        response = chat_session.send_message(user_text)
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"خطایی رخ داد. جزئیات خطا: {e}")

if __name__ == '__main__':
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling(drop_pending_updates=True)

