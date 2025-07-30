#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telethon import TelegramClient
import asyncio
import logging
from datetime import datetime
from config import API_ID, API_HASH, CHANNEL_IDS, NOTIFICATION_CHAT_ID, SESSION_NAME

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Создаём клиента
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# Глобальные переменные для отслеживания каждого канала
channels_data = {}

def get_channel_inline_link(channel_info):
    """Создаём inline-ссылку на канал (как на скрине)"""
    if hasattr(channel_info, 'username') and channel_info.username:
        return f"[{channel_info.title}](https://t.me/{channel_info.username})"
    else:
        # Для приватных каналов
        channel_id_clean = str(channel_info.id)[4:]  # Убираем -100 из ID
        return f"[{channel_info.title}](tg://resolve?domain=c/{channel_id_clean})"

async def get_channel_participants_count(channel_id):
    """Получаем количество участников канала"""
    try:
        channel = await client.get_entity(channel_id)
        if hasattr(channel, 'participants_count') and channel.participants_count is not None:
            return channel.participants_count
        
        try:
            participants = await client.get_participants(channel, limit=0)
            return participants.total
        except Exception as e:
            logger.warning(f"Не удалось получить точное количество для {channel.title}: {e}")
        
        return None
        
    except Exception as e:
        logger.error(f"Ошибка получения количества участников для {channel_id}: {e}")
        return None

async def get_recent_participants_info(channel_id):
    """Получаем информацию о последних 10 участниках (для больших каналов)"""
    try:
        participants = await client.get_participants(channel_id, limit=10)
        
        recent_users = []
        for i, user in enumerate(participants, 1):
            user_name = user.first_name or "Без имени"
            
            # Умная ссылка: username или tg://user?id=
            if user.username:
                user_link = f"@{user.username}"
            else:
                user_link = f"[Профиль](tg://user?id={user.id})"
            
            user_info = f"{i}. **{user_name}** | {user_link} | ID: `{user.id}`"
            recent_users.append(user_info)
        
        return "\n".join(recent_users)
        
    except Exception as e:
        logger.error(f"Ошибка получения последних участников для {channel_id}: {e}")
        return "❌ Не удалось получить список участников"

async def detailed_participants_check(channel_id):
    """Детальная проверка участников для небольших каналов (до 200)"""
    try:
        channel_data = channels_data[channel_id]
        channel_info = channel_data['info']
        channel_title = channel_info.title
        channel_inline_link = get_channel_inline_link(channel_info)
        
        # Получаем всех участников
        participants = await client.get_participants(channel_id, limit=200)
        current_participants_set = {user.id for user in participants}
        
        last_participants_set = channel_data['last_participants']
        
        if last_participants_set is not None:
            # Кто подписался
            new_users = current_participants_set - last_participants_set
            for user_id in new_users:
                user = next((user for user in participants if user.id == user_id), None)
                if user:
                    user_name = user.first_name or "Без имени"
                    
                    # Ссылка на профиль пользователя
                    if user.username:
                        user_link = f"@{user.username}"
                    else:
                        user_link = f"[Профиль](tg://user?id={user.id})"
                    
                    message = (
                        f"✅ **Новый подписчик!**\n"
                        f"📺 Канал: {channel_inline_link}\n"
                        f"👤 Имя: **{user_name}**\n"
                        f"🔗 Ссылка: {user_link}\n"
                        f"🆔 ID: `{user.id}`\n"
                        f"📊 Всего подписчиков: {len(current_participants_set)}\n"
                        f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}"
                    )
                    await client.send_message(
                        NOTIFICATION_CHAT_ID, 
                        message,
                        parse_mode='markdown',
                        link_preview=False
                    )
                    logger.info(f"✅ [{channel_title}] Новый подписчик: {user_name} (ID: {user.id})")
            
            # Кто отписался
            left_user_ids = last_participants_set - current_participants_set
            if left_user_ids:
                for user_id in left_user_ids:
                    # Ссылка на профиль отписавшегося
                    user_link = f"[Профиль](tg://user?id={user_id})"
                    
                    message = (
                        f"❌ **Отписка**\n"
                        f"📺 Канал: {channel_inline_link}\n"
                        f"🔗 Ссылка: {user_link}\n"
                        f"🆔 ID: `{user_id}`\n"
                        f"📊 Всего подписчиков: {len(current_participants_set)}\n"
                        f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}\n"
                        f"ℹ️ Имя недоступно (пользователь покинул канал)"
                    )
                    await client.send_message(
                        NOTIFICATION_CHAT_ID, 
                        message,
                        parse_mode='markdown',
                        link_preview=False
                    )
                    logger.info(f"❌ [{channel_title}] Отписка: ID {user_id}")
        
        channel_data['last_participants'] = current_participants_set
        return len(current_participants_set)
        
    except Exception as e:
        logger.error(f"Ошибка детальной проверки участников для {channel_id}: {e}")
        return None

async def check_single_channel(channel_id):
    """Проверяем один канал"""
    try:
        channel_data = channels_data[channel_id]
        channel_info = channel_data['info']
        channel_title = channel_info.title
        channel_inline_link = get_channel_inline_link(channel_info)
        
        # Определяем режим работы
        if channel_data['detailed_mode']:
            current_count = await detailed_participants_check(channel_id)
            if current_count is None:
                current_count = await get_channel_participants_count(channel_id)
        else:
            current_count = await get_channel_participants_count(channel_id)
        
        if current_count is None:
            logger.warning(f"⚠️ [{channel_title}] Не удалось получить количество подписчиков")
            return
        
        last_count = channel_data['last_count']
        
        # Проверяем, нужно ли переключить режим
        if current_count >= 200 and channel_data['detailed_mode']:
            channel_data['detailed_mode'] = False
            switch_msg = (
                f"🔄 **Переключение в простой режим**\n"
                f"📺 Канал: {channel_inline_link}\n"
                f"👥 Подписчиков: {current_count} (≥200)\n"
                f"ℹ️ Теперь отслеживаем только количество\n"
                f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}"
            )
            await client.send_message(
                NOTIFICATION_CHAT_ID, 
                switch_msg,
                parse_mode='markdown',
                link_preview=False
            )
            logger.info(f"🔄 [{channel_title}] Переключились в простой режим")
        
        elif current_count < 200 and not channel_data['detailed_mode']:
            channel_data['detailed_mode'] = True
            switch_msg = (
                f"🔄 **Переключение в детальный режим**\n"
                f"📺 Канал: {channel_inline_link}\n"
                f"👥 Подписчиков: {current_count} (<200)\n"
                f"ℹ️ Теперь отслеживаем конкретных пользователей\n"
                f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}"
            )
            await client.send_message(
                NOTIFICATION_CHAT_ID, 
                switch_msg,
                parse_mode='markdown',
                link_preview=False
            )
            logger.info(f"🔄 [{channel_title}] Переключились в детальный режим")
        
        # Отправляем уведомления только для простого режима
        if not channel_data['detailed_mode'] and last_count is not None:
            if current_count > last_count:
                diff = current_count - last_count
                recent_users = await get_recent_participants_info(channel_id)
                
                message = (
                    f"✅ **Новые подписчики: +{diff}**\n"
                    f"📺 Канал: {channel_inline_link}\n"
                    f"📊 Всего подписчиков: {current_count}\n"
                    f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}\n\n"
                    f"👥 **Последние участники:**\n{recent_users}"
                )
                await client.send_message(
                    NOTIFICATION_CHAT_ID, 
                    message,
                    parse_mode='markdown',
                    link_preview=False
                )
                logger.info(f"📈 [{channel_title}] Подписчиков +{diff}, всего: {current_count}")
                
            elif current_count < last_count:
                diff = last_count - current_count
                recent_users = await get_recent_participants_info(channel_id)
                
                message = (
                    f"❌ **Отписки: -{diff}**\n"
                    f"📺 Канал: {channel_inline_link}\n"
                    f"📊 Всего подписчиков: {current_count}\n"
                    f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}\n\n"
                    f"👥 **Последние участники:**\n{recent_users}"
                )
                await client.send_message(
                    NOTIFICATION_CHAT_ID, 
                    message,
                    parse_mode='markdown',
                    link_preview=False
                )
                logger.info(f"📉 [{channel_title}] Подписчиков -{diff}, всего: {current_count}")
        
        # Логируем состояние
        if last_count is None:
            mode_name = "детальный" if channel_data['detailed_mode'] else "простой"
            logger.info(f"🔄 [{channel_title}] Начальное количество: {current_count} ({mode_name} режим)")
        elif current_count == last_count:
            mode_name = "детальный" if channel_data['detailed_mode'] else "простой"
            logger.info(f"📊 [{channel_title}] Без изменений: {current_count} ({mode_name} режим)")
        
        channel_data['last_count'] = current_count
        
    except Exception as e:
        channel_title = channels_data.get(channel_id, {}).get('info', {}).get('title', str(channel_id))
        logger.error(f"❌ [{channel_title}] Ошибка проверки: {e}")

async def check_all_channels_periodically():
    """Проверяем все каналы каждые 30 секунд"""
    while True:
        try:
            # Проверяем все каналы параллельно
            tasks = [check_single_channel(channel_id) for channel_id in channels_data.keys()]
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка при проверке каналов: {e}")
            try:
                error_msg = f"⚠️ **Критическая ошибка мониторинга:**\n`{str(e)}`"
                await client.send_message(
                    NOTIFICATION_CHAT_ID, 
                    error_msg,
                    parse_mode='markdown',
                    link_preview=False
                )
            except:
                pass
        
        await asyncio.sleep(30)

async def main():
    """Главная функция"""
    logger.info("🚀 Запускаем мультиканальный userbot...")
    
    await client.start()
    
    me = await client.get_me()
    logger.info(f"✅ Userbot запущен для аккаунта: {me.first_name} (@{me.username})")
    
    # Инициализируем данные для каждого канала
    successful_channels = []
    failed_channels = []
    
    for channel_id in CHANNEL_IDS:
        try:
            channel_info = await client.get_entity(channel_id)
            initial_count = await get_channel_participants_count(channel_id)
            
            if initial_count is None:
                failed_channels.append(f"❌ **{channel_info.title}** - не удаётся получить количество подписчиков")
                continue
            
            # Определяем режим
            detailed_mode = initial_count < 200
            
            # Сохраняем данные канала
            channels_data[channel_id] = {
                'last_participants': None,
                'detailed_mode': detailed_mode,
                'last_count': None,
                'info': channel_info
            }
            
            mode_name = "детальный" if detailed_mode else "простой"
            mode_emoji = "🔍" if detailed_mode else "📊"
            channel_inline_link = get_channel_inline_link(channel_info)
            
            successful_channels.append(
                f"✅ {channel_inline_link} - {initial_count} подписчиков ({mode_emoji} {mode_name})"
            )
            
            logger.info(f"✅ Канал добавлен: {channel_info.title} ({initial_count} подписчиков, {mode_name} режим)")
            
        except Exception as e:
            failed_channels.append(f"❌ **{channel_id}** - ошибка доступа: {str(e)}")
            logger.error(f"❌ Ошибка инициализации канала {channel_id}: {e}")
    
    if not successful_channels:
        error_msg = "❌ **Не удалось подключиться ни к одному каналу!**"
        await client.send_message(
            NOTIFICATION_CHAT_ID, 
            error_msg,
            parse_mode='markdown',
            link_preview=False
        )
        logger.error("Не удалось подключиться ни к одному каналу!")
        return
    
    # Проверяем куда отправляем уведомления
    try:
        notification_chat = await client.get_entity(NOTIFICATION_CHAT_ID)
        chat_name = getattr(notification_chat, 'title', 'ЛС')
        logger.info(f"📲 Уведомления отправляются в: {chat_name}")
    except Exception as e:
        logger.error(f"❌ Ошибка с чатом уведомлений: {e}")
        return
    
    # Отправляем стартовое сообщение
    start_msg = (
        f"🤖 **Мультиканальный мониторинг запущен!**\n"
        f"🕐 Время запуска: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
        f"⏱ Проверка каждые 30 секунд\n\n"
        f"📺 **Отслеживаемые каналы ({len(successful_channels)}):**\n" +
        "\n".join(successful_channels)
    )
    
    if failed_channels:
        start_msg += f"\n\n⚠️ **Проблемы с каналами:**\n" + "\n".join(failed_channels)
    
    await client.send_message(
        NOTIFICATION_CHAT_ID, 
        start_msg,
        parse_mode='markdown',
        link_preview=False
    )
    
    logger.info(f"✨ Мониторинг {len(successful_channels)} каналов готов к работе!")
    
    task = asyncio.create_task(check_all_channels_periodically())
    
    try:
        await client.run_until_disconnected()
    finally:
        task.cancel()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⛔ Userbot остановлен пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
