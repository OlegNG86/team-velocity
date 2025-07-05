import asyncio
import logging
from datetime import datetime
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

from core.models import User, StoryPoint
from db.database import get_session
from core.services import StoryPointService, UserService

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class StoryBot:
    def __init__(self, token: str):
        self.token = token
        self.user_service = UserService()
        self.story_service = StoryPointService()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        if not user:
            return

        self.user_service.get_or_create_user(
            telegram_id=str(user.id),
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )

        keyboard = [
            [InlineKeyboardButton("📊 Добавить Story Points", callback_data="add_points")],
            [InlineKeyboardButton("📈 Моя статистика", callback_data="my_stats")],
            [InlineKeyboardButton("🏆 Лидерборд", callback_data="leaderboard")],
            [InlineKeyboardButton("📋 Помощь", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"Привет, {user.first_name}! 👋\n\n"
            "Я StoryBot - помогу тебе отслеживать Story Points.\n"
            "Выбери действие:",
            reply_markup=reply_markup
        )

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()

        if query.data == "add_points":
            await query.edit_message_text(
                "Введи количество Story Points и описание задачи:\n"
                "Например: 5 Реализовал API для пользователей"
            )
            context.user_data['waiting_for_points'] = True

        elif query.data == "my_stats":
            await self.show_user_stats(query, context)

        elif query.data == "leaderboard":
            await self.show_leaderboard(query, context)

        elif query.data == "help":
            await self.show_help(query, context)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if context.user_data.get('waiting_for_points'):
            await self.process_story_points(update, context)
            context.user_data['waiting_for_points'] = False

    async def process_story_points(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        if not user:
            return

        text = update.message.text.strip()
        
        try:
            parts = text.split(' ', 1)
            if len(parts) < 2:
                await update.message.reply_text(
                    "❌ Неверный формат! Используй: <количество> <описание>\n"
                    "Например: 5 Реализовал API для пользователей"
                )
                return

            points = float(parts[0])
            description = parts[1]

            if points <= 0:
                await update.message.reply_text("❌ Количество Story Points должно быть положительным!")
                return

            self.story_service.add_story_point(
                telegram_id=str(user.id),
                points=points,
                description=description
            )

            await update.message.reply_text(
                f"✅ Добавлено {points} Story Points!\n"
                f"📝 Описание: {description}"
            )

        except ValueError:
            await update.message.reply_text(
                "❌ Неверный формат числа! Используй: <количество> <описание>\n"
                "Например: 5 Реализовал API для пользователей"
            )

    async def show_user_stats(self, query, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = query.from_user
        stats = self.story_service.get_user_stats(str(user.id))
        
        if not stats:
            await query.edit_message_text("📊 У тебя пока нет записей Story Points.")
            return

        total_points = stats.get('total_points', 0)
        total_tasks = stats.get('total_tasks', 0)
        avg_points = stats.get('avg_points', 0)
        
        text = (
            f"📊 Твоя статистика:\n\n"
            f"🎯 Всего Story Points: {total_points}\n"
            f"📋 Всего задач: {total_tasks}\n"
            f"📈 Среднее за задачу: {avg_points:.1f}\n"
        )
        
        await query.edit_message_text(text)

    async def show_leaderboard(self, query, context: ContextTypes.DEFAULT_TYPE) -> None:
        leaderboard = self.story_service.get_leaderboard(limit=10)
        
        if not leaderboard:
            await query.edit_message_text("🏆 Лидерборд пока пуст.")
            return

        text = "🏆 Лидерборд (последние 30 дней):\n\n"
        
        for i, entry in enumerate(leaderboard, 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            name = entry.get('name', 'Пользователь')
            points = entry.get('points', 0)
            text += f"{emoji} {name}: {points} SP\n"
        
        await query.edit_message_text(text)

    async def show_help(self, query, context: ContextTypes.DEFAULT_TYPE) -> None:
        help_text = (
            "📋 Справка по командам:\n\n"
            "• /start - Главное меню\n"
            "• Добавить Story Points - Записать выполненную работу\n"
            "• Моя статистика - Посмотреть свои результаты\n"
            "• Лидерборд - Топ участников\n\n"
            "💡 Формат добавления Story Points:\n"
            "<количество> <описание задачи>\n\n"
            "Примеры:\n"
            "• 5 Реализовал API для пользователей\n"
            "• 3 Написал тесты для модуля\n"
            "• 8 Рефакторинг базы данных"
        )
        await query.edit_message_text(help_text)

    def run(self) -> None:
        application = Application.builder().token(self.token).build()

        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CallbackQueryHandler(self.button_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        logger.info("Starting StoryBot...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_TOKEN environment variable is required")
    
    bot = StoryBot(token)
    bot.run()


if __name__ == "__main__":
    main()