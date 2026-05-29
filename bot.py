import os
from dotenv import load_dotenv
from google import genai
from google.genai import types, errors
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = "You are a Gen Z teenager. Use gen z slang, be casual, use emojis sometimes, say things like 'no cap', 'lowkey', 'fr fr', 'slay', 'it's giving', 'vibe check', 'bussin', etc. Keep answers short and chill."
MODEL = "gemini-2.5-flash"

user_histories = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я Gemini-бот. Напиши мне что-нибудь.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    if user_id not in user_histories:
        user_histories[user_id] = []

    user_histories[user_id].append(
        types.Content(role="user", parts=[types.Part(text=user_text)])
    )

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=user_histories[user_id],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
            ),
        )

        reply = response.text

        user_histories[user_id].append(
            types.Content(role="model", parts=[types.Part(text=reply)])
        )

        if len(user_histories[user_id]) > 20:
            user_histories[user_id] = user_histories[user_id][-20:]

        await update.message.reply_text(reply)

    except errors.ClientError as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            # Убираем последнее сообщение пользователя из истории чтобы не дублировалось
            user_histories[user_id].pop()
            await update.message.reply_text("⚠️ Превышен лимит запросов. Попробуй через минуту.")
        else:
            user_histories[user_id].pop()
            await update.message.reply_text(f"❌ Ошибка: {e}")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_histories.pop(user_id, None)
    await update.message.reply_text("История очищена.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()