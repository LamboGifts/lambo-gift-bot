import os
import requests
import json
import random
from flask import Flask, request, jsonify
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройки из переменных окружения
TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = "https://lambo-gift-bot.onrender.com"

if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

# Хранилище пользователей в памяти (в продакшене используйте базу данных)
users = {}

# Каталог подарков
GIFTS = {
    "rose": {"name": "🌹 Роза", "price": 5, "emoji": "🌹"},
    "coffee": {"name": "☕ Кофе", "price": 8, "emoji": "☕"},
    "cake": {"name": "🎂 Торт", "price": 15, "emoji": "🎂"},
    "flower": {"name": "🌸 Букет", "price": 25, "emoji": "🌸"},
    "gift": {"name": "🎁 Подарок", "price": 40, "emoji": "🎁"},
    "diamond": {"name": "💎 Бриллиант", "price": 75, "emoji": "💎"},
    "crown": {"name": "👑 Корона", "price": 100, "emoji": "👑"},
    "rocket": {"name": "🚀 Ракета", "price": 75, "emoji": "🚀"},
    "star": {"name": "⭐ Звезда", "price": 30, "emoji": "⭐"}
}

# Множители для Плинко (15 слотов)
PLINKO_MULTIPLIERS = [0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.5, 2.0, 3.0, 2.0, 1.5, 1.2, 1.0, 0.8, 0.6, 0.4, 0.2]

def get_user_data(user_id):
    """Получение данных пользователя"""
    user_id = str(user_id)
    if user_id not in users:
        users[user_id] = {
            "balance": 100,
            "gifts_sent": 0,
            "gifts_received": 0,
            "total_spent": 0,
            "plinko_played": 0,
            "plinko_won": 0,
            "last_bonus": None
        }
        logger.info(f"New user created: {user_id}")
    return users[user_id]

def update_user_balance(user_id, amount):
    """Обновление баланса пользователя"""
    user_data = get_user_data(user_id)
    user_data["balance"] = max(0, user_data["balance"] + amount)

def send_message(chat_id, text, reply_markup=None):
    """Отправка сообщения"""
    try:
        url = f"{API_URL}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        
        response = requests.post(url, data=data, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        return None

def edit_message(chat_id, message_id, text, reply_markup=None):
    """Редактирование сообщения"""
    try:
        url = f"{API_URL}/editMessageText"
        data = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML"
        }
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        
        response = requests.post(url, data=data, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to edit message: {e}")
        return None

def answer_callback(callback_query_id, text=""):
    """Ответ на callback query"""
    try:
        url = f"{API_URL}/answerCallbackQuery"
        data = {
            "callback_query_id": callback_query_id,
            "text": text
        }
        requests.post(url, data=data, timeout=5)
    except Exception as e:
        logger.error(f"Failed to answer callback: {e}")

def main_menu_keyboard():
    """Главное меню"""
    return {
        "inline_keyboard": [
            [{"text": "🎮 Открыть WebApp", "web_app": {"url": f"{WEBHOOK_URL}/webapp"}}],
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
    
    # Создаем кнопки по 2 в ряд
    gifts_items = list(GIFTS.items())
    for i in range(0, len(gifts_items), 2):
        row = []
        for j in range(i, min(i + 2, len(gifts_items))):
            gift_id, gift_info = gifts_items[j]
            row.append({
                "text": f"{gift_info['emoji']} {gift_info['name']} - {gift_info['price']}💰",
                "callback_data": f"buy_{gift_id}"
            })
        keyboard["inline_keyboard"].append(row)
    
    keyboard["inline_keyboard"].append([{"text": "🔙 Назад", "callback_data": "main"}])
    
    text = "🎁 <b>Каталог подарков:</b>\n\nВыберите подарок для покупки:"
    edit_message(chat_id, message_id, text, keyboard)

def play_plinko_game(bet_amount):
    """Логика игры Плинко"""
    # Симулируем падение шарика через пеги
    position = 8  # Начальная позиция в центре
    
    # 7 рядов пегов
    for _ in range(7):
        direction = random.choice([-1, 1])
        position += direction
        # Ограничиваем границы
        position = max(0, min(16, position))
    
    # Получаем множитель
    multiplier = PLINKO_MULTIPLIERS[position]
    win_amount = int(bet_amount * multiplier)
    
    return {
        "position": position,
        "multiplier": multiplier,
        "win_amount": win_amount
    }

def handle_plinko(chat_id, message_id):
    """Меню Плинко"""
    user_data = get_user_data(chat_id)
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🎲 Играть (5 монет)", "callback_data": "play_plinko_5"}],
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
• 5 монет - минимальная ставка
• 10 монет - базовая игра
• 25 монет - средняя ставка
• 50 монет - высокая ставка

🏆 <b>Множители:</b>
💎 x3.0 | 🟢 x2.0 | 🔵 x1.5 | 🟡 x1.2 | ⚪ x1.0 | 🔴 x0.2

📊 <b>Статистика:</b>
• Игр сыграно: {user_data['plinko_played']}
• Выиграно: {user_data['plinko_won']} монет"""

    edit_message(chat_id, message_id, text, keyboard)

def handle_play_plinko(chat_id, message_id, bet):
    """Играть в Плинко"""
    user_data = get_user_data(chat_id)
    
    if user_data['balance'] < bet:
        keyboard = {
            "inline_keyboard": [
                [{"text": "💰 Получить бонус", "callback_data": "daily_bonus"}],
                [{"text": "🔙 Назад", "callback_data": "plinko"}]
            ]
        }
        text = f"❌ Недостаточно средств!\n\nНужно: {bet} монет\nБаланс: {user_data['balance']} монет"
        edit_message(chat_id, message_id, text, keyboard)
        return
    
    # Списываем ставку
    user_data['balance'] -= bet
    user_data['plinko_played'] += 1
    
    # Играем
    result = play_plinko_game(bet)
    win_amount = result["win_amount"]
    
    # Начисляем выигрыш
    if win_amount > 0:
        user_data['balance'] += win_amount
        user_data['plinko_won'] += win_amount
    
    # Анимация падения шарика
    animation = """🎲 Шарик падает...

    ⚪
   / \\
  /   \\
 /     \\
━━━━━━━━━━━━━"""
    
    keyboard = {
        "inline_keyboard": [
            [{"text": f"🎲 Играть еще ({bet} монет)", "callback_data": f"play_plinko_{bet}"}],
            [{"text": "🔙 К Плинко", "callback_data": "plinko"}]
        ]
    }
    
    profit = win_amount - bet
    
    if profit > 0:
        result_text = "🎉 ВЫИГРЫШ!"
        result_emoji = "🟢"
    elif profit == 0:
        result_text = "😊 Возврат ставки"
        result_emoji = "🟡"
    else:
        result_text = "😔 Не повезло"
        result_emoji = "🔴"
    
    text = f"""{animation}

{result_text}

💰 <b>Ставка:</b> {bet} монет
🎯 <b>Позиция:</b> {result['position'] + 1}/17
🏆 <b>Множитель:</b> x{result['multiplier']}
💎 <b>Выигрыш:</b> {win_amount} монет
💳 <b>Баланс:</b> {user_data['balance']} монет

{result_emoji} <b>Результат:</b> {'+' if profit > 0 else ''}{profit} монет"""

    edit_message(chat_id, message_id, text, keyboard)

def handle_daily_bonus(chat_id, message_id):
    """Ежедневный бонус"""
    user_data = get_user_data(chat_id)
    today = datetime.now().strftime('%Y-%m-%d')
    
    if user_data['last_bonus'] == today:
        keyboard = {"inline_keyboard": [[{"text": "🔙 Назад", "callback_data": "main"}]]}
        text = f"⏰ Бонус уже получен сегодня!\n\n💰 Баланс: {user_data['balance']} монет"
        edit_message(chat_id, message_id, text, keyboard)
        return
    
    bonus = random.randint(50, 100)
    user_data['balance'] += bonus
    user_data['last_bonus'] = today
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🎲 Играть в Плинко", "callback_data": "plinko"}],
            [{"text": "🔙 Главное меню", "callback_data": "main"}]
        ]
    }
    
    text = f"""🎉 <b>Ежедневный бонус получен!</b>

💰 <b>Начислено:</b> {bonus} монет
💳 <b>Новый баланс:</b> {user_data['balance']} монет

Удачной игры!"""
    
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
                [{"text": "💰 Получить бонус", "callback_data": "daily_bonus"}],
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
            [{"text": "🎁 Купить еще", "callback_data": "catalog"}],
            [{"text": "🔙 Главное меню", "callback_data": "main"}]
        ]
    }
    
    text = f"""✅ <b>Подарок куплен!</b>

🎁 <b>{gift['name']}</b>
💰 <b>Списано:</b> {gift['price']} монет
💳 <b>Остаток:</b> {user_data['balance']} монет

🎉 <b>Подарок отправлен!</b>"""

    edit_message(chat_id, message_id, text, keyboard)

@app.route("/")
def home():
    return """
    <h1>🎁 GiftBot с Плинко работает! ✅</h1>
    <p><a href="/webapp">Открыть WebApp</a></p>
    """

@app.route("/webapp")
def webapp():
    """WebApp интерфейс"""
    return """<!DOCTYPE html>
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
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 400px;
            margin: 0 auto;
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
        
        .plinko-board {
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 30px 20px;
            text-align: center;
        }
        
        .multipliers {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 8px;
            margin: 20px 0;
        }
        
        .multiplier {
            padding: 10px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 12px;
            text-align: center;
        }
        
        .multiplier.high { background: #4caf50; }
        .multiplier.medium { background: #ff9800; }
        .multiplier.low { background: #f44336; }
        
        .bet-controls {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .btn {
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            border: none;
            color: #fff;
            padding: 15px;
            border-radius: 15px;
            cursor: pointer;
            font-weight: bold;
            font-size: 14px;
            transition: all 0.3s ease;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .btn:disabled {
            background: rgba(255,255,255,0.3);
            cursor: not-allowed;
            transform: none;
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="balance">💰 <span id="balance">100</span> монет</div>
            <div>GiftBot WebApp</div>
        </div>
        
        <div class="plinko-board">
            <h3>🎲 Плинко</h3>
            
            <div class="multipliers">
                <div class="multiplier low">0.2x</div>
                <div class="multiplier medium">0.8x</div>
                <div class="multiplier medium">1.2x</div>
                <div class="multiplier high">2.0x</div>
                <div class="multiplier high">3.0x</div>
                <div class="multiplier high">2.0x</div>
                <div class="multiplier medium">1.2x</div>
                <div class="multiplier medium">0.8x</div>
                <div class="multiplier low">0.2x</div>
            </div>
            
            <div class="bet-controls">
                <button class="btn" onclick="playPlinko(5)">🎲 5 монет</button>
                <button class="btn" onclick="playPlinko(10)">🎲 10 монет</button>
                <button class="btn" onclick="playPlinko(25)">🎲 25 монет</button>
                <button class="btn" onclick="playPlinko(50)">🎲 50 монет</button>
            </div>
            
            <div class="result" id="plinkoResult"></div>
        </div>
    </div>
    
    <script>
        window.Telegram.WebApp.ready();
        window.Telegram.WebApp.expand();
        
        let userData = { balance: 100 };
        
        function updateDisplay() {
            document.getElementById('balance').textContent = userData.balance;
        }
        
        function playPlinko(bet) {
            if (userData.balance < bet) {
                alert('Недостаточно средств!');
                return;
            }
            
            const buttons = document.querySelectorAll('.btn');
            buttons.forEach(btn => btn.disabled = true);
            
            userData.balance -= bet;
            
            // Симуляция игры
            const multipliers = [0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.5, 2.0, 3.0, 2.0, 1.5, 1.2, 1.0, 0.8, 0.6, 0.4, 0.2];
            const position = Math.floor(Math.random() * multipliers.length);
            const multiplier = multipliers[position];
            const winAmount = Math.floor(bet * multiplier);
            
            userData.balance += winAmount;
            updateDisplay();
            
            const resultDiv = document.getElementById('plinkoResult');
            const profit = winAmount - bet;
            
            resultDiv.innerHTML = `
                <div style="font-size: 18px; margin-bottom: 10px;">
                    ${winAmount > bet ? '🎉 ВЫИГРЫШ!' : winAmount === bet ? '😊 Возврат' : '😔 Проигрыш'}
                </div>
                <div>Ставка: ${bet} монет</div>
                <div>Множитель: x${multiplier}</div>
                <div>Выигрыш: ${winAmount} монет</div>
                <div style="color: ${profit > 0 ? '#4caf50' : profit < 0 ? '#f44336' : '#ff9800'}">
                    Результат: ${profit > 0 ? '+' : ''}${profit} монет
                </div>
            `;
            
            resultDiv.classList.add('show');
            
            setTimeout(() => {
                buttons.forEach(btn => btn.disabled = false);
                resultDiv.classList.remove('show');
            }, 3000);
        }
        
        updateDisplay();
    </script>
</body>
</html>"""

@app.route(f"/webhook", methods=["POST"])
def webhook():
    """Обработка webhook - путь без токена для безопасности"""
    try:
        data = request.get_json()
        
        if "message" in data:
            message = data["message"]
            chat_id = message["chat"]["id"]
            user_name = message["from"].get("first_name", "Пользователь")
            text = message.get("text", "")
            
            if text == "/start":
                handle_start(chat_id, user_name)
        
        elif "callback_query" in data:
            callback = data["callback_query"]
            chat_id = callback["message"]["chat"]["id"]
            message_id = callback["message"]["message_id"]
            callback_data = callback["data"]
            user_name = callback["from"].get("first_name", "Пользователь")
            
            answer_callback(callback["id"])
            
            # Обработка callback_data
            if callback_data == "catalog":
                handle_catalog(chat_id, message_id)
            elif callback_data == "plinko":
                handle_plinko(chat_id, message_id)
            elif callback_data.startswith("play_plinko_"):
                bet = int(callback_data.split("_")[-1])
                handle_play_plinko(chat_id, message_id, bet)
            elif callback_data in ["balance", "stats"]:
                user_data = get_user_data(chat_id)
                text = f"""📊 <b>Статистика - {user_name}</b>

💰 <b>Баланс:</b> {user_data['balance']} монет

📈 <b>Общая статистика:</b>
🎁 Подарков отправлено: {user_data['gifts_sent']}
💸 Потрачено на подарки: {user_data['total_spent']} монет

🎲 <b>Статистика Плинко:</b>
🎮 Игр сыграно: {user_data['plinko_played']}
🏆 Всего выиграно: {user_data['plinko_won']} монет"""
                
                keyboard = {
                    "inline_keyboard": [
                        [{"text": "💰 Ежедневный бонус", "callback_data": "daily_bonus"}],
                        [{"text": "🎲 Играть в Плинко", "callback_data": "plinko"}],
                        [{"text": "🔙 Назад", "callback_data": "main"}]
                    ]
                }
                edit_message(chat_id, message_id, text, keyboard)
            elif callback_data == "daily_bonus":
                handle_daily_bonus(chat_id, message_id)
            elif callback_data == "main":
                user_data = get_user_data(chat_id)
                text = f"""🎁 <b>GiftBot - {user_name}</b>

💰 <b>Ваш баланс:</b> {user_data['balance']} монет
🎉 <b>Выберите действие:</b>"""
                edit_message(chat_id, message_id, text, main_menu_keyboard())
            elif callback_data.startswith("buy_"):
                gift_id = callback_data.replace("buy_", "")
                handle_buy_gift(chat_id, message_id, gift_id)
        
        return "OK"
    
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "ERROR", 500

def setup_webhook():
    """Настройка webhook"""
    try:
        webhook_url = f"{WEBHOOK_URL}/webhook"
        response = requests.post(f"{API_URL}/setWebhook", data={"url": webhook_url}, timeout=10)
        result = response.json()
        
        if result.get("ok"):
            logger.info(f"Webhook установлен: {webhook_url}")
            return True
        else:
            logger.error(f"Ошибка webhook: {result}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to setup webhook: {e}")
        return False

if __name__ == "__main__":
    setup_webhook()
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
