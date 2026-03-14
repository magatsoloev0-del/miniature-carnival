
# Telegram Calorie Bot

Бот считает калории по фото или текстовому описанию еды.

## Функции
- установка дневной нормы калорий
- учет съеденного
- анализ фото еды
- хранение данных в памяти (runtime)

## Установка

1. Установить Python 3.13

2. Установить зависимости

pip install -r requirements.txt

3. Создать .env файл

TG_BOT_API_KEY=your_token

(опционально)

OPENAI_API_KEY=your_openai_key

4. Запуск

python main.py

## Команды

/start
/setgoal 2000
/status
