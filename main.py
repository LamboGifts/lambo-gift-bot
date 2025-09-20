import os
import requests
import json
import random
from flask import Flask, request

# Настройки
TOKEN = "7678954168:AAG6755ngOoYcQfIt6viZKMRXRcv6dOd0vY"
API_URL = f"https://api.telegram.org/bot{TOKEN}"
WEBHOOK_URL = "https://lambo-gift.onrender.com"

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
            [{"text": "🎮 Открыть WebApp", "web_app": {"url": "https://lambo-gift-bot.onrender.com/webapp"}}],
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

@app.route("/webapp")
def webapp():
    """WebApp интерфейс"""
    webapp_html = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GiftBot WebApp</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            overflow-x: hidden;
            min-height: 100vh;
        }

        .container {
            max-width: 400px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 20px;
            backdrop-filter: blur(10px);
        }

        .balance {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }

        .tabs {
            display: flex;
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 5px;
            margin-bottom: 30px;
        }

        .tab {
            flex: 1;
            padding: 15px;
            text-align: center;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: bold;
        }

        .tab.active {
            background: rgba(255,255,255,0.3);
            transform: scale(1.05);
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .gift-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-bottom: 30px;
        }

        .gift-card {
            background: rgba(255,255,255,0.15);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            border: 2px solid transparent;
        }

        .gift-card:hover {
            transform: translateY(-5px);
            background: rgba(255,255,255,0.25);
            border-color: rgba(255,255,255,0.3);
        }

        .gift-emoji {
            font-size: 40px;
            margin-bottom: 10px;
            display: block;
        }

        .gift-name {
            font-weight: bold;
            margin-bottom: 5px;
        }

        .gift-price {
            color: #ffeb3b;
            font-weight: bold;
        }

        .plinko-board {
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 30px 20px;
            text-align: center;
            margin-bottom: 20px;
        }

        .plinko-animation {
            height: 200px;
            position: relative;
            margin: 20px 0;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 15px;
            background: linear-gradient(45deg, rgba(255,255,255,0.05), rgba(255,255,255,0.1));
            overflow: hidden;
        }

        .plinko-ball {
            width: 20px;
            height: 20px;
            background: #ffeb3b;
            border-radius: 50%;
            position: absolute;
            top: 10px;
            left: 50%;
            transform: translateX(-50%);
            box-shadow: 0 0 15px rgba(255, 235, 59, 0.7);
            opacity: 0;
            transition: all 0.5s ease;
        }

        .plinko-ball.dropping {
            opacity: 1;
            animation: drop 2s ease-in-out;
        }

        @keyframes drop {
            0% { top: 10px; transform: translateX(-50%); }
            25% { top: 60px; transform: translateX(-30px); }
            50% { top: 110px; transform: translateX(-70px); }
            75% { top: 150px; transform: translateX(-20px); }
            100% { top: 180px; transform: translateX(-40px); }
        }

        .bet-input-section {
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
            text-align: center;
        }

        .bet-input {
            width: 100px;
            padding: 8px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 8px;
            background: rgba(255,255,255,0.1);
            color: #fff;
            font-size: 14px;
            margin: 5px;
            text-align: center;
        }

        .total-bet {
            margin-top: 10px;
            font-weight: bold;
            color: #ffeb3b;
            font-size: 16px;
        }

        .bet-btn-custom {
            background: linear-gradient(45deg, #4caf50, #45a049);
            border: none;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            font-size: 16px;
            transition: all 0.3s ease;
        }

        .bet-btn-custom:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }

        .bet-btn-custom:disabled {
            background: rgba(255,255,255,0.3);
            cursor: not-allowed;
            transform: none;
        }

        .plinko-visual {
            position: relative;
            background: linear-gradient(135deg, #1e3a8a, #3730a3);
            border-radius: 15px;
            padding: 30px 20px;
            margin: 20px 0;
            min-height: 400px;
        }

        .plinko-pyramid {
            position: relative;
            width: 100%;
            height: 300px;
            margin-bottom: 20px;
        }

        .peg-row {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 25px;
            gap: 30px;
        }

        .peg {
            width: 8px;
            height: 8px;
            background: #ffffff;
            border-radius: 50%;
            box-shadow: 0 0 8px rgba(255, 255, 255, 0.8);
            position: relative;
        }

        .row-1 { margin-top: 10px; }
        .row-2 .peg { margin: 0 -5px; }
        .row-3 .peg { margin: 0 -8px; }
        .row-4 .peg { margin: 0 -10px; }
        .row-5 .peg { margin: 0 -12px; }
        .row-6 .peg { margin: 0 -14px; }
        .row-7 .peg { margin: 0 -16px; }

        .plinko-animation {
            height: 300px;
            position: absolute;
            top: 30px;
            left: 20px;
            right: 20px;
            pointer-events: none;
        }

        .plinko-ball {
            width: 18px;
            height: 18px;
            background: radial-gradient(circle at 30% 30%, #60a5fa, #3b82f6);
            border-radius: 50%;
            position: absolute;
            top: 5px;
            left: 50%;
            transform: translateX(-50%);
            box-shadow: 0 0 15px rgba(59, 130, 246, 0.8);
            opacity: 0;
            transition: all 0.3s ease;
            z-index: 10;
        }

        .plinko-ball.dropping {
            opacity: 1;
        }

        .multipliers-bottom {
            display: grid;
            grid-template-columns: repeat(11, 1fr);
            gap: 2px;
            margin-top: 20px;
        }

        .multiplier {
            padding: 10px 4px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 11px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.2);
            position: relative;
        }

        .multiplier.lose {
            background: linear-gradient(135deg, #dc2626, #b91c1c);
            color: #fef2f2;
        }

        .multiplier.small-win {
            background: linear-gradient(135deg, #f59e0b, #d97706);
            color: #fef3c7;
        }

        .multiplier.medium-win {
            background: linear-gradient(135deg, #10b981, #059669);
            color: #ecfdf5;
        }

        .multiplier.big-win {
            background: linear-gradient(135deg, #8b5cf6, #7c3aed);
            color: #f3e8ff;
            box-shadow: 0 0 10px rgba(139, 92, 246, 0.5);
        }

        .responsible-gaming {
            background: rgba(255, 152, 0, 0.2);
            border: 1px solid #ff9800;
            border-radius: 10px;
            padding: 15px;
            margin: 15px 0;
            text-align: center;
            font-size: 14px;
        }

        .responsible-gaming p {
            margin: 5px 0;
        }

        .result {
            margin-top: 20px;
            padding: 20px;
            background: rgba(255,255,255,0.15);
            border-radius: 15px;
            text-align: center;
            display: none;
        }

        .result.show {
            display: block;
            animation: slideUp 0.5s ease;
        }

        @keyframes slideUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .win {
            color: #4caf50;
            font-size: 18px;
            font-weight: bold;
        }

        .lose {
            color: #f44336;
            font-size: 18px;
            font-weight: bold;
        }

        .btn {
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            border: none;
            color: #fff;
            padding: 15px 30px;
            border-radius: 25px;
            cursor: pointer;
            font-weight: bold;
            font-size: 16px;
            transition: all 0.3s ease;
            width: 100%;
            margin-top: 10px;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }

        .stats {
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
        }

        .stat-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }

        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #4caf50;
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            transform: translateX(100%);
            transition: transform 0.3s ease;
            z-index: 1000;
        }

        .notification.show {
            transform: translateX(0);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="balance">💰 <span id="balance">100</span> монет</div>
            <div>GiftBot WebApp</div>
        </div>

        <div class="tabs">
            <div class="tab active" onclick="showTab('gifts')">🎁 Подарки</div>
            <div class="tab" onclick="showTab('plinko')">🎲 Плинко</div>
            <div class="tab" onclick="showTab('stats')">📊 Статистика</div>
        </div>

        <div id="gifts" class="tab-content active">
            <div class="gift-grid">
                <div class="gift-card" onclick="buyGift('rose', 10)">
                    <span class="gift-emoji">🌹</span>
                    <div class="gift-name">Роза</div>
                    <div class="gift-price">10 монет</div>
                </div>
                <div class="gift-card" onclick="buyGift('cake', 25)">
                    <span class="gift-emoji">🎂</span>
                    <div class="gift-name">Торт</div>
                    <div class="gift-price">25 монет</div>
                </div>
                <div class="gift-card" onclick="buyGift('diamond', 50)">
                    <span class="gift-emoji">💎</span>
                    <div class="gift-name">Бриллиант</div>
                    <div class="gift-price">50 монет</div>
                </div>
                <div class="gift-card" onclick="buyGift('crown', 100)">
                    <span class="gift-emoji">👑</span>
                    <div class="gift-name">Корона</div>
                    <div class="gift-price">100 монет</div>
                </div>
                <div class="gift-card" onclick="buyGift('rocket', 75)">
                    <span class="gift-emoji">🚀</span>
                    <div class="gift-name">Ракета</div>
                    <div class="gift-price">75 монет</div>
                </div>
                <div class="gift-card" onclick="buyGift('star', 30)">
                    <span class="gift-emoji">⭐</span>
                    <div class="gift-name">Звезда</div>
                    <div class="gift-price">30 монет</div>
                </div>
            </div>
        </div>

        <div id="plinko" class="tab-content">
            <div class="plinko-board">
                <h3>🎲 Плинко</h3>
                <div class="bet-input-section">
                    <label for="betAmount">Ставка за шарик:</label>
                    <input type="number" id="betAmount" min="1" value="10" class="bet-input">
                    
                    <label for="ballCount">Количество шариков (1-5):</label>
                    <input type="number" id="ballCount" min="1" max="5" value="1" class="bet-input">
                    
                    <button class="bet-btn-custom" onclick="playMultiplePlinko()">🎲 Играть</button>
                    <div class="total-bet">Общая ставка: <span id="totalBet">10</span> монет</div>
                </div>
                
                <div class="plinko-visual">
                    <div class="plinko-pyramid">
                        <!-- Пирамида пегов как на фото -->
                        <div class="peg-row row-1">
                            <div class="peg"></div>
                            <div class="peg"></div>
                            <div class="peg"></div>
                        </div>
                        <div class="peg-row row-2">
                            <div class="peg"></div>
                            <div class="peg"></div>
                            <div class="peg"></div>
                            <div class="peg"></div>
                        </div>
                        <div class="peg-row row-3">
                            <div class="peg"></div>
                            <div class="peg"></div>
                            <div class="peg"></div>
                            <div class="peg"></div>
                            <div class="peg"></div>
                        </div>
                        <div class="peg-row row-4">
                            <div class="peg"></div>
                            <div class="peg"></div>
                            <div class="peg"></div>
                            <div class="peg"></div>
                            <div class="peg"></div>
                            <div class="peg"></div>
                        </div>
                        <div class="peg-row row-5">
                            <div class="peg"></div>
                            <div class="peg"></div>
                            <div class="peg"></div>
                            <div class="peg"></div>
                            <div class="peg"></div>
                            <div class="peg"></div>
                            <div class="peg"></div>
                        </div>
                        <div class="peg-row row-6">
                            <div class="peg"></div>
                            <div class="peg"></div>
                            <div class="peg"></div>
                            <div class="peg"></div>
                            <div class="peg"></div>
                            <div class="peg"></div>
                            <div class="peg"></div>
                            <div class="peg"></div>
                        </div>
                        <div class="peg-row row-7">
                            <div class="peg"></div>
                            <div class="peg"></div>
                            <div class="peg"></div>
                            <div class="peg"></div>
                            <div class="peg"></div>
                            <div class="peg"></div>
                            <div class="peg"></div>
                            <div class="peg"></div>
                            <div class="peg"></div>
                        </div>
                    </div>
                    
                    <div class="plinko-animation" id="plinkoAnimation">
                        <div class="plinko-ball" id="plinkoBall"></div>
                    </div>

                    <div class="multipliers-bottom">
                        <div class="multiplier lose">0.2x</div>
                        <div class="multiplier small-win">0.5x</div>
                        <div class="multiplier small-win">1x</div>
                        <div class="multiplier medium-win">1.5x</div>
                        <div class="multiplier big-win">2x</div>
                        <div class="multiplier big-win">3x</div>
                        <div class="multiplier big-win">2x</div>
                        <div class="multiplier medium-win">1.5x</div>
                        <div class="multiplier small-win">1x</div>
                        <div class="multiplier small-win">0.5x</div>
                        <div class="multiplier lose">0.2x</div>
                    </div>
                </div>

                <div class="result" id="plinkoResult"></div>
            </div>
        </div>

        <div id="stats" class="tab-content">
            <div class="stats">
                <h3>📊 Ваша статистика</h3>
                <div class="stat-row">
                    <span>🎁 Подарков отправлено:</span>
                    <span id="giftsSent">0</span>
                </div>
                <div class="stat-row">
                    <span>💸 Потрачено на подарки:</span>
                    <span id="totalSpent">0</span>
                </div>
                <div class="stat-row">
                    <span>🎲 Игр в Плинко:</span>
                    <span id="plinkoPlayed">0</span>
                </div>
                <div class="stat-row">
                    <span>🏆 Выиграно в Плинко:</span>
                    <span id="plinkoWon">0</span>
                </div>
            </div>
            <button class="btn" onclick="addBalance()">💰 Получить бонус (100 монет)</button>
        </div>
    </div>

    <div class="notification" id="notification"></div>

    <script>
        window.Telegram.WebApp.ready();
        window.Telegram.WebApp.expand();

        const user = window.Telegram.WebApp.initDataUnsafe?.user;
        const userId = user?.id || 'demo_user';

        let userData = {
            balance: 100,
            giftsSent: 0,
            totalSpent: 0,
            plinkoPlayed: 0,
            plinkoWon: 0
        };

        function loadUserData() {
            const saved = localStorage.getItem(`giftbot_${userId}`);
            if (saved) {
                userData = JSON.parse(saved);
                updateDisplay();
            }
        }

        function saveUserData() {
            localStorage.setItem(`giftbot_${userId}`, JSON.stringify(userData));
        }

        function updateDisplay() {
            document.getElementById('balance').textContent = userData.balance;
            document.getElementById('giftsSent').textContent = userData.giftsSent;
            document.getElementById('totalSpent').textContent = userData.totalSpent;
            document.getElementById('plinkoPlayed').textContent = userData.plinkoPlayed;
            document.getElementById('plinkoWon').textContent = userData.plinkoWon;
        }

        function showNotification(message) {
            const notification = document.getElementById('notification');
            notification.textContent = message;
            notification.classList.add('show');
            
            setTimeout(() => {
                notification.classList.remove('show');
            }, 3000);
        }

        function showTab(tabName) {
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById(tabName).classList.add('active');
        }

        function buyGift(giftId, price) {
            if (userData.balance < price) {
                showNotification('Недостаточно средств!');
                return;
            }

            userData.balance -= price;
            userData.giftsSent += 1;
            userData.totalSpent += price;
            
            saveUserData();
            updateDisplay();
            
            const giftNames = {
                'rose': '🌹 Роза',
                'cake': '🎂 Торт', 
                'diamond': '💎 Бриллиант',
                'crown': '👑 Корона',
                'rocket': '🚀 Ракета',
                'star': '⭐ Звезда'
            };
            
            showNotification(`${giftNames[giftId]} куплен и отправлен!`);
        }

        function playMultiplePlinko() {
            const betInput = document.getElementById('betAmount');
            const ballCountInput = document.getElementById('ballCount');
            const bet = parseInt(betInput.value);
            const ballCount = parseInt(ballCountInput.value);
            
            // Проверки
            if (isNaN(bet) || bet < 1) {
                showNotification('Ставка должна быть не менее 1 монеты!');
                return;
            }
            
            if (isNaN(ballCount) || ballCount < 1 || ballCount > 5) {
                showNotification('Количество шариков должно быть от 1 до 5!');
                return;
            }
            
            const totalBet = bet * ballCount;
            
            if (userData.balance < totalBet) {
                showNotification('Недостаточно средств для ставки!');
                return;
            }

            // Блокируем интерфейс
            const playButton = document.querySelector('.bet-btn-custom');
            playButton.disabled = true;
            
            // Списываем ставку
            userData.balance -= totalBet;
            userData.plinkoPlayed += ballCount;
            
            let totalWin = 0;
            let completedBalls = 0;
            const results = [];
            
            // Запускаем шарики с небольшими интервалами
            for (let ballIndex = 0; ballIndex < ballCount; ballIndex++) {
                setTimeout(() => {
                    playSingleBall(bet, ballIndex, (result) => {
                        totalWin += result.winAmount;
                        results.push(result);
                        completedBalls++;
                        
                        if (completedBalls === ballCount) {
                            // Все шарики упали, показываем итоги
                            userData.balance += totalWin;
                            userData.plinkoWon += totalWin;
                            
                            showFinalResults(results, totalBet, totalWin);
                            
                            saveUserData();
                            updateDisplay();
                            
                            // Разблокируем интерфейс
                            playButton.disabled = false;
                        }
                    });
                }, ballIndex * 200); // Интервал между шариками
            }
        }
        
        function playSingleBall(bet, ballIndex, callback) {
            // Создаем уникальный шарик для каждого броска
            const ballId = `ball_${ballIndex}`;
            const ball = document.createElement('div');
            ball.className = 'plinko-ball';
            ball.id = ballId;
            ball.style.backgroundColor = getRandomBallColor();
            
            const animation = document.getElementById('plinkoAnimation');
            animation.appendChild(ball);
            
            // Анимация падения через пирамиду пегов
            ball.classList.add('dropping');
            
            // Начальная позиция в центре (индекс 5 из 11)
            let position = 5;
            const drops = 7; // 7 рядов пегов
            
            for (let i = 0; i < drops; i++) {
                setTimeout(() => {
                    // На каждом пеге шарик может отскочить влево или вправо
                    const deviation = Math.random() < 0.5 ? -1 : 1;
                    position = Math.max(0, Math.min(10, position + deviation));
                    
                    // Обновляем позицию шарика
                    const leftPercent = (position * 9.09) + 4.5; // Распределяем по 11 слотам
                    ball.style.left = `${leftPercent}%`;
                    ball.style.top = `${20 + (i * 35)}px`;
                    
                }, i * 200); // Интервал между отскоками
            }
            
            setTimeout(() => {
                // Определяем результат на основе финальной позиции (11 слотов)
                const multipliers = [0.2, 0.5, 1.0, 1.5, 2.0, 3.0, 2.0, 1.5, 1.0, 0.5, 0.2];
                const finalMultiplier = multipliers[position];
                const winAmount = Math.floor(bet * finalMultiplier);
                
                // Подсвечиваем слот куда упал шарик
                const slots = document.querySelectorAll('.multiplier');
                if (slots[position]) {
                    slots[position].style.backgroundColor = winAmount >= bet ? 
                        'rgba(16, 185, 129, 0.8)' : 'rgba(220, 38, 38, 0.8)';
                    slots[position].style.transform = 'scale(1.1)';
                    
                    // Убираем подсветку через 2 секунды
                    setTimeout(() => {
                        slots[position].style.backgroundColor = '';
                        slots[position].style.transform = '';
                    }, 2000);
                }
                
                // Убираем шарик после анимации
                setTimeout(() => {
                    ball.remove();
                }, 1500);
                
                callback({
                    position: position,
                    multiplier: finalMultiplier,
                    winAmount: winAmount,
                    bet: bet
                });
                
            }, drops * 200 + 300);
        }
        
        function getRandomBallColor() {
            const colors = [
                '#ffeb3b', // желтый
                '#ff5722', // оранжево-красный
                '#4caf50', // зеленый
                '#2196f3', // синий
                '#9c27b0'  // фиолетовый
            ];
            return colors[Math.floor(Math.random() * colors.length)];
        }
        
        function showFinalResults(results, totalBet, totalWin) {
            const resultDiv = document.getElementById('plinkoResult');
            
            let resultText = `<div class="${totalWin > 0 ? 'win' : 'lose'}">`;
            resultText += `<strong>Результаты ${results.length} шариков:</strong><br>`;
            
            results.forEach((result, index) => {
                resultText += `Шарик ${index + 1}: x${result.multiplier} = ${result.winAmount} монет<br>`;
            });
            
            resultText += `<br><strong>Итого:</strong><br>`;
            resultText += `Ставка: ${totalBet} монет<br>`;
            resultText += `Выигрыш: ${totalWin} монет<br>`;
            
            if (totalWin > totalBet) {
                resultText += `<span style="color: #4caf50;">Прибыль: +${totalWin - totalBet} монет 🎉</span>`;
            } else if (totalWin < totalBet) {
                resultText += `<span style="color: #f44336;">Убыток: -${totalBet - totalWin} монет</span>`;
            } else {
                resultText += `Безубыток: 0 монет`;
            }
            
            resultText += `</div>`;
            
            resultDiv.innerHTML = resultText;
            resultDiv.classList.add('show');
            
            setTimeout(() => {
                resultDiv.classList.remove('show');
            }, 5000);
        }
        
        // Обновляем общую ставку при изменении инпутов
        document.addEventListener('DOMContentLoaded', function() {
            loadUserData();
            
            function updateTotalBet() {
                const bet = parseInt(document.getElementById('betAmount').value) || 0;
                const balls = parseInt(document.getElementById('ballCount').value) || 0;
                document.getElementById('totalBet').textContent = bet * balls;
            }
            
            document.getElementById('betAmount').addEventListener('input', updateTotalBet);
            document.getElementById('ballCount').addEventListener('input', updateTotalBet);
        });
    </script>
</body>
</html>"""
    
    return webapp_html

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

