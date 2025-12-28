# Инструкция по установке

## Системные зависимости

```bash
apt-get update && apt-get install -y python3 python3-venv fonts-ubuntu librsvg2-bin
```

## Установка Python зависимостей

```bash
# Создание виртуального окружения
python3 -m venv venv

# Активация виртуального окружения
source venv/bin/activate

# Обновление pip
pip install --upgrade pip

# Установка зависимостей
pip install -r requirements.txt
```

## Настройка

1. Скопируйте `config.example.py` в `config.py`
2. Заполните в `config.py`:
   - `TELEGRAM_BOT_TOKEN` - токен бота Telegram
   - `TELEGRAM_CHAT_ID` - ID чата для отправки отчетов
   - `NODES_FILE` - путь к файлу со списком нод (по умолчанию `nodes.txt`)
3. Создайте файл со списком нод (например, `nodes.txt`):
   - Формат: одна нода на строку в формате `host:port`
   - Примеры:
     ```
     node101:11101
     192.168.1.100:14002
     [2001:db8::1]:14002
     ```

## Запуск

```bash
# Запуск генерации отчета (автоматически использует venv)
./run.py

# Или с явной активацией venv
source venv/bin/activate && python3 run.py
```

## Структура проекта

- `run.py` - главный скрипт для запуска
- `lib/` - модули проекта:
  - `poll_all_nodes.py` - асинхронный опрос всех нод
  - `generate_from_svg.py` - генерация SVG из шаблона
  - `svg_to_png.py` - конвертация SVG в PNG
  - `telegram_sender.py` - отправка в Telegram
- `templates/default/index.svg` - SVG шаблон карточки
- `config.example.py` - пример конфигурации
- `requirements.txt` - Python зависимости

