# 🛠 StoryBot — Telegram-бот для учёта Story‑Point'ов

## Цель проекта
- Упрощённый учёт Story‑Point'ов индивидуальной и командной продуктивности.
- Быстрые отчёты velocity, лидерборды, напоминания через Telegram.
- Интеграция с базой PostgreSQL/SQLite, Docker-окружение, pytest, экспорты CSV/Excel.

## Команды (bash)
- poetry install — установить зависимости
- poetry run bot — запустить Telegram‑бота
- pytest tests/ --maxfail=1 -q — прогнать тесты
- docker-compose up --build — поднять контейнеры
- make export-csv — экспорт статистики

## Структура кода
- bot/ — Telegram‑обработчики, напоминания
- core/ — модели, логика сервисов, аналитика и экспорт
- db/ — подключение, миграции (Alembic)
- integrations/ — плагины (например, Jira)
- tests/ — тесты через pytest

## Code style
- Python 3.12+ (PEP 8 + f‑strings)
- black + isort (авто‑форматирование через CI)
- Типы через typing и type hints

## Workflow
- feature/*, bugfix/* 🡒 PR в main
- PR через GitHub Actions: lint → pytest → build
- Коммиты от Claude: "chore: ..." — автоматом, человек проверяет

## Ограничения
- Не создавать задачи в Jira; только ручной импорт/запись баллов
- Без авторизации пользователей (только Telegram ID)
- Без публичного доступа/финансовых фич

## 🔧 Инструкции específicos Claude
- Если создаёшь файл — очищай временные scratch‑файлы после (`rm tmp-*`)
- При изменении структуры папок — проверяй swagger / openapi
- Пиши понятные commit‑messages, включай chore:, feat: или fix:
- После кода — запускать pytest и black для проверки