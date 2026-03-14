
import os
import json
import base64
from datetime import date
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests

load_dotenv()

TG_TOKEN = os.getenv("TG_BOT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# In-memory storage (runtime only)
users = {}

def get_user(user_id):
    if user_id not in users:
        users[user_id] = {
            "goal": None,
            "days": {}
        }
    return users[user_id]

def today_key():
    return str(date.today())

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот для подсчета калорий.

"
        "Команды:
"
        "/setgoal 2000 — установить дневную норму
"
        "/status — показать текущий прогресс

"
        "Отправь фото еды и/или описание — я оценю калории."
    )

async def setgoal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Используй: /setgoal 2000")
        return

    goal = int(context.args[0])
    user = get_user(update.effective_user.id)
    user["goal"] = goal

    await update.message.reply_text(f"🎯 Дневная цель установлена: {goal} ккал")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    today = today_key()
    eaten = user["days"].get(today, 0)
    goal = user["goal"]

    if goal is None:
        await update.message.reply_text("Сначала установи цель: /setgoal 2000")
        return

    left = goal - eaten

    await update.message.reply_text(
        f"📊 Сегодня:
"
        f"Съедено: {eaten} ккал
"
        f"Цель: {goal} ккал
"
        f"Осталось: {left} ккал"
    )

def estimate_calories_with_ai(text, image_bytes=None):
    if not OPENAI_API_KEY:
        # fallback simple guess
        return 500

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    content = [{"type": "text", "text": f"Estimate calories for: {text}. Respond with number only."}]

    if image_bytes:
        img_base64 = base64.b64encode(image_bytes).decode()
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}
        })

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": content
            }
        ]
    }

    r = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=60
    )

    try:
        text = r.json()["choices"][0]["message"]["content"]
        return int("".join(filter(str.isdigit, text)))
    except:
        return 500

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)

    calories = estimate_calories_with_ai(update.message.text)

    today = today_key()
    user["days"][today] = user["days"].get(today, 0) + calories

    await update.message.reply_text(f"🍽 Добавлено ~{calories} ккал")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)

    photo = update.message.photo[-1]
    file = await photo.get_file()
    image_bytes = await file.download_as_bytearray()

    caption = update.message.caption or "food"

    calories = estimate_calories_with_ai(caption, image_bytes)

    today = today_key()
    user["days"][today] = user["days"].get(today, 0) + calories

    await update.message.reply_text(f"📷 Оценка: ~{calories} ккал добавлено")

def main():
    app = Application.builder().token(TG_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setgoal", setgoal))
    app.add_handler(CommandHandler("status", status))

    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
