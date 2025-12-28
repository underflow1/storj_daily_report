# Инструкция по установке

## Системные зависимости

### 1. Python 3 и venv
```bash
apt-get update
apt-get install -y python3 python3-venv
```

### 2. Шрифт Ubuntu (для SVG)
```bash
apt-get install -y fonts-ubuntu
```

### 3. librsvg2-bin (для конвертации SVG в PNG)
```bash
apt-get install -y librsvg2-bin
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

## Запуск

```bash
# Активация виртуального окружения
source venv/bin/activate

# Запуск генерации отчета
python3 generate_daily_report.py
```

## Структура проекта

- `generate_daily_report.py` - главный скрипт
- `poll_all_nodes.py` - асинхронный опрос всех нод
- `generate_from_svg.py` - генерация SVG из шаблона
- `svg_to_png.py` - конвертация SVG в PNG
- `telegram_sender.py` - отправка в Telegram
- `templates/default/index.svg` - SVG шаблон карточки
- `nodes.txt` - список нод для опроса (формат: `host:port`)

