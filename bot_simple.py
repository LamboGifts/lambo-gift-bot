import os
import json
import logging
from flask import Flask, request, jsonify
import requests

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7678954168:AAG6755ngOoYcQfIt6viZKMRXRcv6dOd0vY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://lambo-gift.onrender.com")
TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"

# Flask приложение
app = Flask(__name__)

# Простое хранилище пользователей в памяти
users = {}

def send_message(chat_id, text, reply_markup=None):
    """Отправка сообщения через Telegram API"""
    url = f"{TELEGRAM_API}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    
    response = requests.post(url, data=data)
    return response.json()

def edit_message(chat_id, message_id, text, reply_markup=None):
    """Редактирование сообщения"""
    url = f"{TELEGRAM_API}/editMessageText"
    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    
    response = requests.post(url, data=data)
    return response.json()

def get_user_data(user_id):
    """Получение данных пользователя"""
    if user_id not in users:
        users[user_id] = {
            "balance": 100,
            "gifts_sent": 0,
            "gifts_received": 0
        }
    return users[user_id]

def update_user_balance(user_id, amount):
    """Обновление баланса пользователя"""
    if user_id not in users:
        get_user_data(user_id)
    users[user_id]["balance"] += amount

# Каталог подарков
GIFTS = {
    "rose": {"name": "🌹 Роза", "price": 10},
    "cake": {"name": "🎂 Торт", "price": 25},
    "diamond": {"name": "💎 Бриллиант", "price": 50},
    "crown": {"name": "👑 Корона", "price": 100}
}

def handle_start(chat_id, user_name):
    """Обработка команды /start"""
    user_data = get_user_data(chat_id)
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🎁 Каталог подарков", "callback_data": "catalog"}],
            [{"text": "💳 Баланс", "callback_data": "balance"}],
            [{"text": "📊 Статистика", "callback_data": "stats"}]
        ]
    }
    
    text = f"""🎁 <b>Добро пожаловать в GiftBot, {user_name}!</b>

💰 <b>Ваш баланс:</b> {user_data['balance']} монет
🎉 <b>Отправляйте виртуальные подарки друзьям!</b>

Выберите действие:"""

    send_message(chat_id, text, keyboard)

def handle_catalog(chat_id, message_id):
    """Показ каталога подарков"""
    keyboard = {"inline_keyboard": []}
    
    for gift_id, gift_info in GIFTS.items():
        keyboard["inline_keyboard"].append([{
            "text": f"{gift_info['name']} - {gift_info['price']} монет",
            "callback_data": f"buy_{gift_id}"
        }])
    
    keyboard["inline_keyboard"].append([{"text": "🔙 Назад", "callback_data": "main"}])
    
    text = "🎁 <b>Каталог подарков:</b>\n\nВыберите подарок для покупки:"
    edit_message(chat_id, message_id, text, keyboard)

def handle_balance(chat_id, message_id):
    """Показ баланса"""
    user_data = get_user_data(chat_id)
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "💰 Пополнить баланс", "callback_data": "add_balance"}],
            [{"text": "🔙 Назад", "callback_data": "main"}]
        ]
    }
    
    text = f"""💳 <b>Ваш баланс:</b> {user_data['balance']} монет
🎁 <b>Подарков отправлено:</b> {user_data['gifts_sent']}
🎉 <b>Подарков получено:</b> {user_data['gifts_received']}"""

    edit_message(chat_id, message_id, text, keyboard)

def handle_buy_gift(chat_id, message_id, gift_id):
    """Покупка подарка"""
    user_data = get_user_data(chat_id)
    gift = GIFTS.get(gift_id)
    
    if not gift:
        edit_message(chat_id, message_id, "❌ Подарок не найден!")
        return
    
    if user_data['balance'] < gift['price']:
        keyboard = {
            "inline_keyboard": [
                [{"text": "💰 Пополнить баланс", "callback_data": "add_balance"}],
                [{"text": "🔙 К каталогу", "callback_data": "catalog"}]
            ]
        }
        text = f"""❌ <b>Недостаточно средств!</b>

💰 <b>Ваш баланс:</b> {user_data['balance']} монет
💸 <b>Нужно:</b> {gift['price']} монет"""
        edit_message(chat_id, message_id, text, keyboard)
        return
    
    # Покупаем подарок
    user_data['balance'] -= gift['price']
    user_data['gifts_sent'] += 1
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🔙 В главное меню", "callback_data": "main"}]
        ]
    }
    
    text = f"""✅ <b>Подарок куплен!</b>

🎁 <b>{gift['name']}</b>
💰 <b>Списано:</b> {gift['price']} монет
💳 <b>Остаток:</b> {user_data['balance']} монет

🎉 <b>Подарок отправлен!</b>"""

    edit_message(chat_id, message_id, text, keyboard)

def handle_add_balance(chat_id, message_id):
    """Пополнение баланса"""
    update_user_balance(chat_id, 50)
    user_data = get_user_data(chat_id)
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🔙 Назад", "callback_data": "main"}]
        ]
    }
    
    text = f"""🎉 <b>Бонус получен!</b>

💰 <b>Начислено:</b> 50 монет
💳 <b>Новый баланс:</b> {user_data['balance']} монет

<i>В реальной версии здесь была бы оплата</i>"""

    edit_message(chat_id, message_id, text, keyboard)

def handle_main_menu(chat_id, message_id, user_name):
    """Возврат в главное меню"""
    user_data = get_user_data(chat_id)
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🎁 Каталог подарков", "callback_data": "catalog"}],
            [{"text": "💳 Баланс", "callback_data": "balance"}],
            [{"text": "📊 Статистика", "callback_data": "stats"}]
        ]
    }
    
    text = f"""🎁 <b>GiftBot - {user_name}!</b>

💰 <b>Ваш баланс:</b> {user_data['balance']} монет
🎉 <b>Выберите действие:</b>"""

    edit_message(chat_id, message_id, text, keyboard)

@app.route("/")
def index():
    return "🎁 GiftBot is running! ✅"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    """Обработка webhook от Telegram"""
    try:
        data = request.get_json()
        logger.info(f"Получено обновление: {data}")
        
        if "message" in data:
            # Новое сообщение
            message = data["message"]
            chat_id = message["chat"]["id"]
            user_name = message["from"].get("first_name", "Пользователь")
            text = message.get("text", "")
            
            if text == "/start":
                handle_start(chat_id, user_name)
        
        elif "callback_query" in data:
            # Нажатие кнопки
            callback = data["callback_query"]
            chat_id = callback["message"]["chat"]["id"]
            message_id = callback["message"]["message_id"]
            callback_data = callback["data"]
            user_name = callback["from"].get("first_name", "Пользователь")
            
            # Отвечаем на callback
            answer_url = f"{TELEGRAM_API}/answerCallbackQuery"
            requests.post(answer_url, data={"callback_query_id": callback["id"]})
            
            # Обрабатываем действие
            if callback_data == "catalog":
                handle_catalog(chat_id, message_id)
            elif callback_data == "balance" or callback_data == "stats":
                handle_balance(chat_id, message_id)
            elif callback_data == "add_balance":
                handle_add_balance(chat_id, message_id)
            elif callback_data == "main":
                handle_main_menu(chat_id, message_id, user_name)
            elif callback_data.startswith("buy_"):
                gift_id = callback_data.replace("buy_", "")
                handle_buy_gift(chat_id, message_id, gift_id)
        
        return "OK"
    
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}")
        return "ERROR", 500

def set_webhook():
    """Установка webhook"""
    webhook_url = f"{WEBHOOK_URL}/{TOKEN}"
    url = f"{TELEGRAM_API}/setWebhook"
    data = {"url": webhook_url}
    
    response = requests.post(url, data=data)
    logger.info(f"Webhook установлен: {response.json()}")

if __name__ == "__main__":
    # Устанавливаем webhook
    set_webhook()
    
    # Запускаем Flask
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
