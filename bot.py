# requirements (add to requirements.txt):
# python-telegram-bot==20.7
# python-dotenv==1.0.0

from dotenv import load_dotenv
load_dotenv()

import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SECRET_WORD = "АЙДОНЯ"

questions = [
    ("Геодезический прибор, измеряющий расстояние/углы/высоты. Замена теодолиту.", "ТАХЕОМЕТР"),
    ("Базовый чертежный инструмент в AutoCAD.", "ЛИНЕЙКА"),
    ("При помощи него геодезисты делают аэрофотосъёмку.", "ДРОН"),
    ("Устройство обработки края ткани, чтобы не осыпалась.", "ОВЕРЛОК"),
    ("Материал, получаемый из цемента, воды и песка.", "БЕТОН"),
    ("Удерживает морское судно при дноуглубительных работах.", "ЯКОРЬ"),
]

progress = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    progress[user_id] = 0
    await update.message.reply_text(
        "Привет! Это кроссворд-бот.\n"
        "Отгадай 6 слов, чтобы открыть зашифрованное слово.\n\n"
        f"Вопрос №1:\n{questions[0][0]}"
    )

async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in progress:
        await update.message.reply_text("Напиши /start чтобы начать.")
        return

    step = progress[user_id]

    if step < 0 or step >= len(questions):
        await update.message.reply_text("Ошибка прогресса. Напиши /start чтобы начать заново.")
        progress[user_id] = 0
        return

    question_text, correct_answer = questions[step]
    user_answer = update.message.text.strip().upper()

    if user_answer != correct_answer:
        await update.message.reply_text("Неверно! Попробуй ещё раз.")
        return

    progress[user_id] += 1

    if progress[user_id] == len(questions):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Показать зашифрованное слово", callback_data="show_secret")]
        ])
        await update.message.reply_text("Верно! Все ответы отгаданы! 🎉", reply_markup=keyboard)
        return

    next_q = questions[progress[user_id]][0]
    await update.message.reply_text(
        f"Верно!\n\nВопрос №{progress[user_id] + 1}:\n{next_q}"
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if progress.get(user_id, 0) < len(questions):
        await query.message.reply_text("Сначала отгадай все слова!")
        return

    await query.message.reply_text(f"🔑 Зашифрованное слово:\n👉 {SECRET_WORD}")

    image_path = "reward.png"
    if os.path.exists(image_path):
        try:
            with open(image_path, "rb") as f:
                await query.message.reply_photo(photo=f, caption="Ваша награда 🎉")
        except Exception as e:
            logger.exception("Ошибка при отправке изображения")
            await query.message.reply_text("⚠ Ошибка при отправке изображения.")
    else:
        await query.message.reply_text("⚠ Картинка reward.png не найдена.")

def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        logger.error("BOT_TOKEN не найден. Создайте .env с BOT_TOKEN=...")
        raise SystemExit("BOT_TOKEN не найден. Бот остановлен.")

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, answer))
    application.add_handler(CallbackQueryHandler(button))

    logger.info("Bot started.")
    application.run_polling()

if __name__ == "__main__":
    main()
