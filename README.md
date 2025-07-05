# Team Velocity Bot

Телеграм-бот для отслеживания Story Points и повышения прозрачности работы команды разработчиков.

## Возможности

- 📊 Добавление Story Points с описанием выполненных задач
- 📈 Просмотр личной статистики по Story Points
- 🏆 Лидерборд команды
- 👥 Управление командами и участниками

## Технологии

- **Python 3.12** - Современный и производительный язык программирования
- **python-telegram-bot** - API для взаимодействия с Telegram Bot API
- **SQLAlchemy** - Мощный ORM для работы с базами данных
- **PostgreSQL** - Надежная реляционная база данных
- **Docker** - Контейнеризация для простого деплоя
- **Poetry** - Управление зависимостями Python
- **Alembic** - Миграции базы данных
- **Pytest** - Тестирование

## Установка

### Предварительные требования

- Docker
- Docker Compose

### Запуск

1. Клонировать репозиторий
```bash
git clone <repository-url>
cd team-velocity
```

2. Создать файл .env с настройками окружения (на основе .env.example)
```bash
cp .env.example .env
```

3. Заполнить .env файл необходимыми данными
```
# Telegram Bot Configuration
TELEGRAM_TOKEN=your_telegram_bot_token_here

# Database Configuration
DATABASE_URL=postgresql://storybot:storybot_password@postgres:5432/storybot
```

4. Запустить с помощью Docker Compose
```bash
docker compose up -d
```

## Команды бота

- `/start` - Главное меню
- Добавить Story Points - Записать выполненную работу
- Моя статистика - Посмотреть свои результаты
- Лидерборд - Топ участников

## Формат добавления Story Points

```
<количество> <описание задачи>
```

Примеры:
- `5 Реализовал API для пользователей`
- `3 Написал тесты для модуля`
- `8 Рефакторинг базы данных`

## Разработка

### Структура проекта

```
team-velocity/
├── bot/                # Код телеграм бота
├── core/               # Основная бизнес-логика
│   ├── models.py       # Модели данных
│   └── services.py     # Сервисные функции
├── db/                 # Конфигурация базы данных
├── tests/              # Тесты
├── docker-compose.yml  # Docker конфигурация
├── Dockerfile          # Инструкции для сборки контейнера
├── pyproject.toml      # Poetry зависимости
└── entrypoint.sh       # Скрипт инициализации
```

### Тестирование

Для запуска тестов используйте:

```bash
./run_tests.sh
```

Тесты используют отдельную in-memory SQLite базу данных для изоляции от рабочих данных.

## База данных

База данных содержит следующие таблицы:

- **users** - Информация о пользователях
- **story_points** - Записи о выполненных задачах
- **teams** - Команды
- **team_members** - Участники команд

Доступ к базе данных через Adminer:
- URL: http://localhost:8080
- Система: PostgreSQL
- Сервер: postgres
- Пользователь: storybot
- Пароль: storybot_password
- База данных: storybot
