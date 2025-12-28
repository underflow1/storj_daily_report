# Пример конфигурационного файла
# Скопируйте этот файл в config.py и заполните реальными значениями

# Токен Telegram бота для отправки картинки
# Получить токен можно у @BotFather в Telegram
TELEGRAM_BOT_TOKEN = "your_bot_token_here"

# ID чата для отправки картинки
# Можно узнать у @userinfobot или через API
TELEGRAM_CHAT_ID = "your_chat_id_here"

# API роуты для опроса нод
# Список эндпоинтов которые будут опрашиваться у каждой ноды
API_ROUTES = [
    '/api/sno',
    # '/api/sno/satellites',
    '/api/sno/estimated-payout'
]

# Путь к шаблону SVG
TEMPLATE_PATH = "templates/default/index.svg"

