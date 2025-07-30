# Telegram Channel Monitor - Быстрый запуск на Ubuntu

Простой userbot для мониторинга подписок и отписок на Telegram-канале.

## 🚀 Установка за 5 минут

### 1. Подготовка системы (обязательно!)

```bash
# Обновляем систему
apt update

# Устанавливаем необходимые пакеты
apt install python3.10-venv git nano
```

### 2. Скачиваем проект

```bash
git clone https://github.com/aiveg/telegram-channel-monitor.git
cd telegram-channel-monitor
```

### 3. Создаем виртуальное окружение (важно!)

```bash
# Удаляем старое окружение если есть
rm -rf venv

# Создаем новое виртуальное окружение
python3 -m venv venv

# ОБЯЗАТЕЛЬНО активируем окружение
source venv/bin/activate

# Устанавливаем зависимости
pip install -r requirements.txt
```

**Проверь что всё установилось:**
```bash
# Должен показать путь к python в venv
which python
# Результат должен быть: /root/telegram-channel-monitor/venv/bin/python
```

### 4. Настраиваем конфиг

```bash
cp config.example.py config.py
nano config.py
```

Заполни в `config.py`:
- `API_ID` и `API_HASH` (получи на [my.telegram.org](https://my.telegram.org))
- `CHANNEL_ID` (ID твоего канала)
- `NOTIFICATION_CHAT_ID` (ID группы для уведомлений)

**Получить ID чатов**: добавь `@userinfobot` в канал/группу как админа, он покажет ID.

## 🚀 Запуск

### Первый запуск (тест)

```bash
# ВАЖНО: активируй виртуальное окружение
source venv/bin/activate

# Запускай бота
python3 userbot.py
```

Введи номер телефона и код из Telegram. Если всё работает - можешь остановить через `Ctrl+C`.

### Автозапуск через systemd

#### ⚠️ **БЕЗОПАСНОСТЬ - ЧИТАЙ ОБЯЗАТЕЛЬНО!**

**🚨 Запуск под root ОПАСЕН!** Если сервер взломают, злоумышленники получат полный доступ к системе и твоему Telegram!

**Рекомендуемый способ - создать отдельного пользователя:**

```bash
# Создай пользователя для бота
useradd -m -s /bin/bash telegram-bot
passwd telegram-bot

# Перенеси проект
mv /root/telegram-channel-monitor /home/telegram-bot/
chown -R telegram-bot:telegram-bot /home/telegram-bot/telegram-channel-monitor
```

#### Настройка службы

**Для отдельного пользователя (РЕКОМЕНДУЕТСЯ):**

```bash
sudo nano /etc/systemd/system/telegram-channel-monitor.service
```

```ini
[Unit]
Description=Telegram Channel Monitor
After=network.target

[Service]
Type=simple
Restart=always
RestartSec=10
User=telegram-bot
WorkingDirectory=/home/telegram-bot/telegram-channel-monitor
ExecStart=/home/telegram-bot/telegram-channel-monitor/venv/bin/python3 userbot.py
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

**Для root (НЕ РЕКОМЕНДУЕТСЯ, но если очень нужно):**

```bash
sudo nano /etc/systemd/system/telegram-channel-monitor.service
```

```ini
[Unit]
Description=Telegram Channel Monitor
After=network.target

[Service]
Type=simple
Restart=always
RestartSec=10
User=root
WorkingDirectory=/root/telegram-channel-monitor
ExecStart=/root/telegram-channel-monitor/venv/bin/python3 userbot.py
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

#### Активация службы

```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-channel-monitor.service
sudo systemctl start telegram-channel-monitor.service
```

## 📊 Управление и диагностика

### Проверка статуса

```bash
# Статус службы
sudo systemctl status telegram-channel-monitor.service

# Логи в реальном времени
sudo journalctl -u telegram-channel-monitor.service -f

# Последние 50 строк логов
sudo journalctl -u telegram-channel-monitor.service -n 50
```

### Управление службой

```bash
# Перезапуск
sudo systemctl restart telegram-channel-monitor.service

# Остановка
sudo systemctl stop telegram-channel-monitor.service

# Отключить автозапуск
sudo systemctl disable telegram-channel-monitor.service
```

## 🐛 Устранение проблем

### Ошибка "ModuleNotFoundError: No module named 'telethon'"

**Проблема**: Виртуальное окружение не создалось или зависимости установились неправильно.

**Решение**:
```bash
cd /root/telegram-channel-monitor
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Проверь установку
python3 -c "import telethon; print('OK')"
```

### Ошибка "Assignment outside of section"

**Проблема**: Сломался формат systemd файла.

**Решение**: Удали и создай файл службы заново, точно скопировав содержимое из инструкции.

### Ошибка "No such file or directory"

**Проблема**: Неправильные пути в systemd файле.

**Решение**: Проверь что виртуальное окружение существует:
```bash
ls -la /root/telegram-channel-monitor/venv/bin/python3
```

## ⚠️ Важные моменты

- **Безопасность**: Лучше создать отдельного пользователя для бота!
- **Права администратора**: Ты должен быть админом отслеживаемого канала
- **Личный аккаунт**: Бот работает от твоего личного Telegram аккаунта
- **Секретные файлы**: Никогда не публикуй `config.py` и файлы `.session`
- **Виртуальное окружение**: Всегда активируй `venv` перед установкой пакетов

## 🔒 Дополнительная безопасность для root

Если всё-таки запускаешь под root:

```bash
# Ограничь права на важные файлы
chmod 600 /root/telegram-channel-monitor/config.py
chmod 600 /root/telegram-channel-monitor/*.session

# Базовая защита фаерволлом
ufw enable
ufw default deny incoming
ufw allow ssh
```

Готово! Теперь бот будет автоматически уведомлять о новых подписчиках и отписках в указанную группу.