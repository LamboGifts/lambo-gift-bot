import os
import requests
import json
import random
from flask import Flask, request

# Настройки
TOKEN = "7678954168:AAG6755ngOoYcQfIt6viZKMRXRcv6dOd0vY"
API_URL = f"https://api.telegram.org/bot{TOKEN}"
WEBHOOK_URL = "https://lambo-gift-bot.onrender.com"

app = Flask(__name__)

# Хранилище пользователей в памяти
users = {}

# Каталог подарков
GIFTS = {
    "rose": {"name": "🌹 Роза", "price": 10, "emoji": "🌹"},
    "cake": {"name": "🎂 Торт", "price": 25, "emoji": "🎂"}, 
    "diamond": {"name": "💎 Бриллиант", "price": 50, "emoji": "💎"},
    "crown": {"name": "👑 Корона", "price": 100, "emoji": "👑"},
    "rocket": {"name": "🚀 Ракета", "price": 75, "emoji": "🚀"},
    "star": {"name": "⭐ Звезда", "price": 30, "emoji": "⭐"}
}

def get_user_data(user_id):
    """Получение данных пользователя"""
    if user_id not in users:
        users[user_id] = {
            "balance": 100,
            "gifts_sent": 0,
            "gifts_received": 0,
            "total_spent": 0,
            "plinko_played": 0,
            "plinko_won": 0
        }
    return users[user_id]

def update_user_balance(user_id, amount):
    """Обновление баланса"""
    if user_id not in users:
        get_user_data(user_id)
    users[user_id]["balance"] += amount

def send_message(chat_id, text, reply_markup=None):
    """Отправка сообщения"""
    url = f"{API_URL}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    
    requests.post(url, data=data)

def edit_message(chat_id, message_id, text, reply_markup=None):
    """Редактирование сообщения"""
    url = f"{API_URL}/editMessageText"
    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    
    requests.post(url, data=data)

def answer_callback(callback_query_id):
    """Ответ на callback query"""
    url = f"{API_URL}/answerCallbackQuery"
    requests.post(url, data={"callback_query_id": callback_query_id})

def main_menu_keyboard():
    """Главное меню"""
    return {
        "inline_keyboard": [
            [{"text": "🎁 Каталог подарков", "callback_data": "catalog"}],
            [{"text": "🎲 Плинко", "callback_data": "plinko"}],
            [{"text": "💳 Баланс", "callback_data": "balance"}],
            [{"text": "📊 Статистика", "callback_data": "stats"}]
        ]
    }

def handle_start(chat_id, user_name):
    """Обработка /start"""
    user_data = get_user_data(chat_id)
    
    text = f"""🎁 <b>Добро пожаловать в GiftBot, {user_name}!</b>

💰 <b>Ваш баланс:</b> {user_data['balance']} монет
🎉 <b>Отправляйте подарки и играйте в Плинко!</b>

Выберите действие:"""

    send_message(chat_id, text, main_menu_keyboard())

def handle_catalog(chat_id, message_id):
    """Каталог подарков"""
    keyboard = {"inline_keyboard": []}
    
    for gift_id, gift_info in GIFTS.items():
        keyboard["inline_keyboard"].append([{
            "text": f"{gift_info['emoji']} {gift_info['name']} - {gift_info['price']} монет",
            "callback_data": f"buy_{gift_id}"
        }])
    
    keyboard["inline_keyboard"].append([{"text": "🔙 Назад", "callback_data": "main"}])
    
    text = "🎁 <b>Каталог подарков:</b>\n\nВыберите подарок для покупки:"
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
    user_data['total_spent'] += gift['price']
    
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

def play_plinko():
    """Логика игры Плинко"""
    # Эмулируем падение шарика
    paths = [
        {"emoji": "🔥", "multiplier": 0, "chance": 20},      # Проиграл
        {"emoji": "💰", "multiplier": 1.2, "chance": 30},   # x1.2
        {"emoji": "🎉", "multiplier": 1.5, "chance": 25},   # x1.5
        {"emoji": "💎", "multiplier": 2.0, "chance": 15},   # x2.0
        {"emoji": "🏆", "multiplier": 3.0, "chance": 7},    # x3.0
        {"emoji": "👑", "multiplier": 5.0, "chance": 3}     # x5.0
    ]
    
    # Выбираем результат по вероятности
    rand = random.randint(1, 100)
    cumulative = 0
    
    for result in paths:
        cumulative += result["chance"]
        if rand <= cumulative:
            return result
    
    return paths[0]  # fallback

def handle_plinko(chat_id, message_id):
    """Меню Плинко"""
    user_data = get_user_data(chat_id)
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🎲 Играть (10 монет)", "callback_data": "play_plinko_10"}],
            [{"text": "🎲 Играть (25 монет)", "callback_data": "play_plinko_25"}],
            [{"text": "🎲 Играть (50 монет)", "callback_data": "play_plinko_50"}],
            [{"text": "📊 Статистика Плинко", "callback_data": "plinko_stats"}],
            [{"text": "🔙 Назад", "callback_data": "main"}]
        ]
    }
    
    text = f"""🎲 <b>Добро пожаловать в Плинко!</b>

💰 <b>Ваш баланс:</b> {user_data['balance']} монет

🎯 <b>Выберите ставку:</b>
• 10 монет - базовая игра
• 25 монет - увеличенные множители
• 50 монет - максимальные призы!

🏆 <b>Множители:</b>
👑 x5.0 | 💎 x2.0 | 🎉 x1.5 | 💰 x1.2 | 🔥 x0"""

    edit_message(chat_id, message_id, text, keyboard)

def handle_play_plinko(chat_id, message_id, bet):
    """Играть в Плинко"""
    user_data = get_user_data(chat_id)
    
    if user_data['balance'] < bet:
        keyboard = {
            "inline_keyboard": [
                [{"text": "💰 Пополнить баланс", "callback_data": "add_balance"}],
                [{"text": "🔙 Назад", "callback_data": "plinko"}]
            ]
        }
        text = f"❌ Недостаточно средств!\nНужно: {bet} монет"
        edit_message(chat_id, message_id, text, keyboard)
        return
    
    # Списываем ставку
    user_data['balance'] -= bet
    user_data['plinko_played'] += 1
    
    # Играем
    result = play_plinko()
    win_amount = int(bet * result["multiplier"])
    
    # Начисляем выигрыш
    if win_amount > 0:
        user_data['balance'] += win_amount
        user_data['plinko_won'] += win_amount
    
    # Анимация падения шарика
    animation = """
🎲 Шарик падает...

    ●
   / \\
  /   \\
 /     \\
━━━━━━━━━
"""
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🎲 Играть еще", "callback_data": f"play_plinko_{bet}"}],
            [{"text": "🔙 К Плинко", "callback_data": "plinko"}]
        ]
    }
    
    if win_amount > 0:
        text = f"""{animation}

{result["emoji"]} <b>ВЫИГРЫШ!</b>

💰 <b>Ставка:</b> {bet} монет
🏆 <b>Множитель:</b> x{result["multiplier"]}
💎 <b>Выигрыш:</b> {win_amount} монет
💳 <b>Баланс:</b> {user_data['balance']} монет"""
    else:
        text = f"""{animation}

{result["emoji"]} <b>Не повезло!</b>

💰 <b>Ставка:</b> {bet} монет
🏆 <b>Множитель:</b> x{result["multiplier"]}
💔 <b>Проигрыш:</b> {bet} монет
💳 <b>Баланс:</b> {user_data['balance']} монет"""

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

📊 <b>Статистика:</b>
🎁 Подарков отправлено: {user_data['gifts_sent']}
💸 Потрачено на подарки: {user_data['total_spent']} монет
🎲 Игр в Плинко: {user_data['plinko_played']}
🏆 Выиграно в Плинко: {user_data['plinko_won']} монет"""

    edit_message(chat_id, message_id, text, keyboard)

def handle_add_balance(chat_id, message_id):
    """Пополнение баланса"""
    update_user_balance(chat_id, 100)
    user_data = get_user_data(chat_id)
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🔙 Назад", "callback_data": "main"}]
        ]
    }
    
    text = f"""🎉 <b>Бонус получен!</b>

💰 <b>Начислено:</b> 100 монет
💳 <b>Новый баланс:</b> {user_data['balance']} монет

<i>В реальной версии здесь была бы оплата</i>"""

    edit_message(chat_id, message_id, text, keyboard)

def handle_main_menu(chat_id, message_id, user_name):
    """Главное меню"""
    user_data = get_user_data(chat_id)
    
    text = f"""🎁 <b>GiftBot - {user_name}!</b>

💰 <b>Ваш баланс:</b> {user_data['balance']} монет
🎉 <b>Выберите действие:</b>"""

    edit_message(chat_id, message_id, text, main_menu_keyboard())

@app.route("/")
def home():
    return "🎁 GiftBot с Плинко работает! ✅"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    """Обработка webhook"""
    try:
        data = request.get_json()
        print(f"Webhook получил: {data}")
        
        if "message" in data:
            message = data["message"]
            chat_id = message["chat"]["id"]
            user_name = message["from"].get("first_name", "User")
            text = message.get("text", "")
            
            print(f"Сообщение от {user_name}: {text}")
            
            if text == "/start":
                handle_start(chat_id, user_name)
            else:
                send_message(chat_id, f"Получил: {text}\nИспользуйте /start для начала")
        
        elif "callback_query" in data:
            callback = data["callback_query"]
            chat_id = callback["message"]["chat"]["id"]
            message_id = callback["message"]["message_id"]
            callback_data = callback["data"]
            user_name = callback["from"].get("first_name", "User")
            
            answer_callback(callback["id"])
            
            # Обрабатываем callback
            if callback_data == "catalog":
                handle_catalog(chat_id, message_id)
            elif callback_data == "plinko":
                handle_plinko(chat_id, message_id)
            elif callback_data.startswith("play_plinko_"):
                bet = int(callback_data.split("_")[-1])
                handle_play_plinko(chat_id, message_id, bet)
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
        print(f"Ошибка webhook: {e}")
        return "ERROR", 500

if __name__ == "__main__":
    # Устанавливаем webhook
    webhook_url = f"{WEBHOOK_URL}/{TOKEN}"
    response = requests.post(f"{API_URL}/setWebhook", data={"url": webhook_url})
    print(f"Webhook установлен: {response.json()}")
    
    # Запускаем Flask
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

