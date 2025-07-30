# Пример конфигурации для Telegram Channel Monitor
# Скопируй этот файл в config.py и заполни своими данными

# Настройки бота
API_ID = 12345678  # Получи на https://my.telegram.org
API_HASH = "your_api_hash_here"  # Получи на https://my.telegram.org

# Список каналов для отслеживания (ID или username)
# Можно указывать через запятую: ID, username или смешанно
CHANNEL_IDS = [
    -1001234567890,     # ID канала (начинается с -100)
    "@your_channel",    # Username канала
    # Добавь больше каналов по необходимости
]

# ID группы/чата, куда отправляем уведомления
NOTIFICATION_CHAT_ID = "@your_username"  # Твой "username" или ID чата (если id, то без кавычек)

# Сессия (имя файла сессии)
SESSION_NAME = "userbot_session"
