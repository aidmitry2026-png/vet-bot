import os
import asyncio
from anthropic import Anthropic
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

client = Anthropic()
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")

SYSTEM_PROMPT = """Ты — Мила, дружелюбный ИИ-регистратор ветеринарной клиники «Лапки и хвостики».
Ты общаешься на русском языке, вежливо и с заботой.

Твои задачи:
- Запись на приём (узнай: имя хозяина, кличку и вид животного, причину, дату и время)
- Информация о клинике: пн-пт 9:00-20:00, сб-вс 10:00-18:00, ул. Зелёная 42
- Стоимость услуг: первичный приём 1500₽, повторный 1000₽, вакцинация 800-2000₽, УЗИ 2000₽
- Врачи: Иванова А.С. (терапевт), Петров М.О. (хирург), Соколова Е.И. (дерматолог)
- При серьёзных симптомах — рекомендуй срочный визит

Когда клиент завершает запись — обязательно напиши ЗАПИСЬ ПОДТВЕРЖДЕНА и перечисли все данные."""

user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🐾 Добро пожаловать в клинику «Лапки и хвостики»!\n\n"
        "Я Мила — ваш персональный помощник. Помогу записаться к врачу, "
        "расскажу о наших услугах и врачах.\n\n"
        "Чем могу помочь вашему питомцу?"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    if user_id not in user_sessions:
        user_sessions[user_id] = []

    user_sessions[user_id].append({"role": "user", "content": user_text})

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=user_sessions[user_id]
    )

    reply = response.content[0].text
    user_sessions[user_id].append({"role": "assistant", "content": reply})

    await update.message.reply_text(reply)

    if "ЗАПИСЬ ПОДТВЕРЖДЕНА" in reply and ADMIN_CHAT_ID:
        user_name = update.effective_user.full_name
        username = update.effective_user.username or "нет"
        admin_msg = (
            f"📋 НОВАЯ ЗАПИСЬ\n\n"
            f"👤 Клиент: {user_name} (@{username})\n"
            f"💬 Детали:\n{reply}"
        )
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_msg)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
