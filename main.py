import os
import requests
import json
import random
import time
import threading
from flask import Flask, request, jsonify, render_template_string
import logging
from datetime import datetime, timedelta

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройки
TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = "https://lambo-gift-bot.onrender.com"

if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

# Глобальные переменные для игры
users = {}
current_crash_game = None
game_lock = threading.Lock()

# Обновленная система подарков на основе реальных Telegram Gifts
REAL_TELEGRAM_GIFTS = {
    # Hanging Star (самые дорогие)
    "hanging_star_1649": {"name": "💫 Hanging Star", "stars": 1649, "emoji": "💫", "rarity": "mythic"},
    "hanging_star_1554": {"name": "💫 Hanging Star", "stars": 1554, "emoji": "💫", "rarity": "mythic"},
    "hanging_star_1545": {"name": "💫 Hanging Star", "stars": 1545, "emoji": "💫", "rarity": "legendary"},
    "hanging_star_1500": {"name": "💫 Hanging Star", "stars": 1500, "emoji": "💫", "rarity": "legendary"},
    "hanging_star_1499": {"name": "💫 Hanging Star", "stars": 1499, "emoji": "💫", "rarity": "legendary"},
    "hanging_star_1443": {"name": "💫 Hanging Star", "stars": 1443, "emoji": "💫", "rarity": "legendary"},
    "hanging_star_1422": {"name": "💫 Hanging Star", "stars": 1422, "emoji": "💫", "rarity": "epic"},
    
    # Mad Pumpkin (дорогие хэллоуин подарки)
    "mad_pumpkin_5151": {"name": "🎃 Mad Pumpkin", "stars": 5151, "emoji": "🎃", "rarity": "mythic"},
    "mad_pumpkin_5125": {"name": "🎃 Mad Pumpkin", "stars": 5125, "emoji": "🎃", "rarity": "mythic"},
    "mad_pumpkin_5043": {"name": "🎃 Mad Pumpkin", "stars": 5043, "emoji": "🎃", "rarity": "mythic"},
    "mad_pumpkin_4945": {"name": "🎃 Mad Pumpkin", "stars": 4945, "emoji": "🎃", "rarity": "mythic"},
    "mad_pumpkin_4739": {"name": "🎃 Mad Pumpkin", "stars": 4739, "emoji": "🎃", "rarity": "mythic"},
    "mad_pumpkin_4533": {"name": "🎃 Mad Pumpkin", "stars": 4533, "emoji": "🎃", "rarity": "mythic"},
    "mad_pumpkin_4431": {"name": "🎃 Mad Pumpkin", "stars": 4431, "emoji": "🎃", "rarity": "mythic"},
    
    # Evil Eye (средне-дорогие)
    "evil_eye_979": {"name": "👁 Evil Eye", "stars": 979, "emoji": "👁", "rarity": "legendary"},
    "evil_eye_969": {"name": "👁 Evil Eye", "stars": 969, "emoji": "👁", "rarity": "legendary"},
    "evil_eye_967": {"name": "👁 Evil Eye", "stars": 967, "emoji": "👁", "rarity": "legendary"},
    "evil_eye_960": {"name": "👁 Evil Eye", "stars": 960, "emoji": "👁", "rarity": "legendary"},
    "evil_eye_948": {"name": "👁 Evil Eye", "stars": 948, "emoji": "👁", "rarity": "legendary"},
    "evil_eye_946": {"name": "👁 Evil Eye", "stars": 946, "emoji": "👁", "rarity": "epic"},
    "evil_eye_897": {"name": "👁 Evil Eye", "stars": 897, "emoji": "👁", "rarity": "epic"},
    "evil_eye_892": {"name": "👁 Evil Eye", "stars": 892, "emoji": "👁", "rarity": "epic"},
    "evil_eye_886": {"name": "👁 Evil Eye", "stars": 886, "emoji": "👁", "rarity": "epic"},
    "evil_eye_874": {"name": "👁 Evil Eye", "stars": 874, "emoji": "👁", "rarity": "epic"},
    
    # Jelly Bunny (средние)
    "jelly_bunny_925": {"name": "🐰 Jelly Bunny", "stars": 925, "emoji": "🐰", "rarity": "legendary"},
    "jelly_bunny_923": {"name": "🐰 Jelly Bunny", "stars": 923, "emoji": "🐰", "rarity": "legendary"},
    "jelly_bunny_921": {"name": "🐰 Jelly Bunny", "stars": 921, "emoji": "🐰", "rarity": "legendary"},
    "jelly_bunny_905": {"name": "🐰 Jelly Bunny", "stars": 905, "emoji": "🐰", "rarity": "epic"},
    "jelly_bunny_900": {"name": "🐰 Jelly Bunny", "stars": 900, "emoji": "🐰", "rarity": "epic"},
    "jelly_bunny_894": {"name": "🐰 Jelly Bunny", "stars": 894, "emoji": "🐰", "rarity": "epic"},
    "jelly_bunny_867": {"name": "🐰 Jelly Bunny", "stars": 867, "emoji": "🐰", "rarity": "epic"},
    "jelly_bunny_865": {"name": "🐰 Jelly Bunny", "stars": 865, "emoji": "🐰", "rarity": "epic"},
    "jelly_bunny_824": {"name": "🐰 Jelly Bunny", "stars": 824, "emoji": "🐰", "rarity": "rare"},
    "jelly_bunny_818": {"name": "🐰 Jelly Bunny", "stars": 818, "emoji": "🐰", "rarity": "rare"},
    "jelly_bunny_816": {"name": "🐰 Jelly Bunny", "stars": 816, "emoji": "🐰", "rarity": "rare"},
    
    # B-Day Candle (дешевые)
    "bday_candle_334": {"name": "🕯 B-Day Candle", "stars": 334, "emoji": "🕯", "rarity": "uncommon"},
    "bday_candle_319": {"name": "🕯 B-Day Candle", "stars": 319, "emoji": "🕯", "rarity": "uncommon"},
    "bday_candle_317": {"name": "🕯 B-Day Candle", "stars": 317, "emoji": "🕯", "rarity": "uncommon"},
    "bday_candle_309": {"name": "🕯 B-Day Candle", "stars": 309, "emoji": "🕯", "rarity": "uncommon"},
    "bday_candle_307": {"name": "🕯 B-Day Candle", "stars": 307, "emoji": "🕯", "rarity": "common"},
    
    # Desk Calendar (средне-дешевые)
    "desk_calendar_301": {"name": "📅 Desk Calendar", "stars": 301, "emoji": "📅", "rarity": "uncommon"},
    "desk_calendar_299": {"name": "📅 Desk Calendar", "stars": 299, "emoji": "📅", "rarity": "uncommon"},
    "desk_calendar_295": {"name": "📅 Desk Calendar", "stars": 295, "emoji": "📅", "rarity": "uncommon"},
    "desk_calendar_289": {"name": "📅 Desk Calendar", "stars": 289, "emoji": "📅", "rarity": "uncommon"},
    "desk_calendar_287": {"name": "📅 Desk Calendar", "stars": 287, "emoji": "📅", "rarity": "common"},
    "desk_calendar_199": {"name": "📅 Desk Calendar", "stars": 199, "emoji": "📅", "rarity": "common"},
    
    # Базовые дешевые подарки
    "delicious_cake": {"name": "🎂 Delicious Cake", "stars": 1, "emoji": "🎂", "rarity": "common"},
    "green_star": {"name": "💚 Green Star", "stars": 2, "emoji": "💚", "rarity": "common"},
    "fireworks": {"name": "🎆 Fireworks", "stars": 5, "emoji": "🎆", "rarity": "common"},
    "blue_star": {"name": "💙 Blue Star", "stars": 10, "emoji": "💙", "rarity": "common"},
    "red_heart": {"name": "❤️ Red Heart", "stars": 25, "emoji": "❤️", "rarity": "uncommon"},
}

# Кейсы с реалистичными подарками и шансами
CASES = {
    "basic_gifts": {
        "name": "Базовые Подарки", 
        "emoji": "🎁", 
        "price": 50,
        "items": [
            {"id": "delicious_cake", "chance": 35},
            {"id": "green_star", "chance": 30},
            {"id": "fireworks", "chance": 20},
            {"id": "blue_star", "chance": 12},
            {"id": "red_heart", "chance": 3}
        ]
    },
    "calendar_case": {
        "name": "Календарные Подарки", 
        "emoji": "📅", 
        "price": 150,
        "items": [
            {"id": "desk_calendar_199", "chance": 25},
            {"id": "desk_calendar_287", "chance": 20},
            {"id": "desk_calendar_289", "chance": 18},
            {"id": "desk_calendar_295", "chance": 15},
            {"id": "desk_calendar_299", "chance": 12},
            {"id": "desk_calendar_301", "chance": 10}
        ]
    },
    "birthday_case": {
        "name": "День Рождения", 
        "emoji": "🕯", 
        "price": 200,
        "items": [
            {"id": "bday_candle_307", "chance": 25},
            {"id": "bday_candle_309", "chance": 20},
            {"id": "bday_candle_317", "chance": 18},
            {"id": "bday_candle_319", "chance": 15},
            {"id": "bday_candle_334", "chance": 12},
            {"id": "red_heart", "chance": 10}
        ]
    },
    "bunny_case": {
        "name": "Желейные Кролики", 
        "emoji": "🐰", 
        "price": 500,
        "items": [
            {"id": "jelly_bunny_816", "chance": 20},
            {"id": "jelly_bunny_818", "chance": 18},
            {"id": "jelly_bunny_824", "chance": 16},
            {"id": "jelly_bunny_865", "chance": 14},
            {"id": "jelly_bunny_867", "chance": 12},
            {"id": "jelly_bunny_894", "chance": 8},
            {"id": "jelly_bunny_900", "chance": 6},
            {"id": "jelly_bunny_905", "chance": 4},
            {"id": "jelly_bunny_921", "chance": 2}
        ]
    },
    "evil_eye_case": {
        "name": "Дурной Глаз", 
        "emoji": "👁", 
        "price": 750,
        "items": [
            {"id": "evil_eye_874", "chance": 20},
            {"id": "evil_eye_886", "chance": 18},
            {"id": "evil_eye_892", "chance": 16},
            {"id": "evil_eye_897", "chance": 14},
            {"id": "evil_eye_946", "chance": 12},
            {"id": "evil_eye_948", "chance": 8},
            {"id": "evil_eye_960", "chance": 6},
            {"id": "evil_eye_967", "chance": 4},
            {"id": "evil_eye_969", "chance": 1.5},
            {"id": "evil_eye_979", "chance": 0.5}
        ]
    },
    "hanging_star_case": {
        "name": "Висящие Звезды", 
        "emoji": "💫", 
        "price": 1000,
        "items": [
            {"id": "hanging_star_1422", "chance": 25},
            {"id": "hanging_star_1443", "chance": 20},
            {"id": "hanging_star_1499", "chance": 15},
            {"id": "hanging_star_1500", "chance": 12},
            {"id": "hanging_star_1545", "chance": 10},
            {"id": "hanging_star_1554", "chance": 8},
            {"id": "hanging_star_1649", "chance": 5},
            {"id": "evil_eye_979", "chance": 5}
        ]
    },
    "ultimate_pumpkin_case": {
        "name": "Безумные Тыквы", 
        "emoji": "🎃", 
        "price": 2000,
        "items": [
            {"id": "mad_pumpkin_4431", "chance": 20},
            {"id": "mad_pumpkin_4533", "chance": 18},
            {"id": "mad_pumpkin_4739", "chance": 15},
            {"id": "mad_pumpkin_4945", "chance": 12},
            {"id": "mad_pumpkin_5043", "chance": 10},
            {"id": "mad_pumpkin_5125", "chance": 8},
            {"id": "mad_pumpkin_5151", "chance": 5},
            {"id": "hanging_star_1649", "chance": 7},
            {"id": "evil_eye_979", "chance": 5}
        ]
    }
}

class CrashGame:
    def __init__(self):
        self.multiplier = 1.0
        self.is_running = False
        self.is_crashed = False
        self.bets = {}
        self.cashed_out = {}
        self.start_time = None
        self.crash_point = None
        
    def start_round(self):
        self.multiplier = 1.0
        self.is_running = True
        self.is_crashed = False
        self.bets = {}
        self.cashed_out = {}
        self.start_time = time.time()
        self.crash_point = self.generate_crash_point()
        logger.info(f"New crash game started. Crash point: {self.crash_point:.2f}")
        
    def generate_crash_point(self):
        rand = random.random()
        if rand < 0.05:
            return random.uniform(10.0, 100.0)
        elif rand < 0.15:
            return random.uniform(5.0, 10.0)
        elif rand < 0.35:
            return random.uniform(2.0, 5.0)
        else:
            return random.uniform(1.01, 2.0)
    
    def update_multiplier(self):
        if not self.is_running or self.is_crashed:
            return
            
        elapsed = time.time() - self.start_time
        self.multiplier = 1.0 + elapsed * 0.1 * (1 + elapsed * 0.05)
        
        if self.multiplier >= self.crash_point:
            self.crash()
    
    def crash(self):
        self.is_crashed = True
        self.is_running = False
        logger.info(f"Game crashed at {self.multiplier:.2f}")
        
        # Обработка проигравших ставок
        for user_id in self.bets:
            if user_id not in self.cashed_out:
                user_data = get_user_data(user_id)
                user_data['total_lost'] += self.bets[user_id]['amount']
                user_data['games_lost'] += 1
    
    def place_bet(self, user_id, amount, auto_cashout=None):
        user_id_str = str(user_id)
        
        if self.is_running:
            return False, "Игра уже идет"
        
        user_data = get_user_data(user_id)
        if user_data['balance'] < amount:
            return False, "Недостаточно средств"
        
        user_data['balance'] -= amount
        user_data['total_bet'] += amount
        user_data['games_played'] += 1
        
        self.bets[user_id_str] = {
            'amount': amount,
            'auto_cashout': auto_cashout
        }
        return True, "Ставка принята"
    
    def cashout(self, user_id):
        user_id_str = str(user_id)
        
        if not self.is_running or self.is_crashed:
            return False, "Игра не идет"
        
        if user_id_str not in self.bets:
            return False, "У вас нет ставки"
        
        if user_id_str in self.cashed_out:
            return False, "Вы уже вывели"
        
        bet_amount = self.bets[user_id_str]['amount']
        win_amount = int(bet_amount * self.multiplier)
        
        user_data = get_user_data(user_id)
        user_data['balance'] += win_amount
        user_data['total_won'] += win_amount
        user_data['games_won'] += 1
        
        self.cashed_out[user_id_str] = self.multiplier
        return True, f"Выведено {win_amount} монет при x{self.multiplier:.2f}"

def get_user_data(user_id):
    user_id = str(user_id)
    if user_id not in users:
        users[user_id] = {
            "balance": 1000,
            "gifts_sent": 0,
            "gifts_received": 0,
            "total_spent": 0,
            "games_played": 0,
            "games_won": 0,
            "games_lost": 0,
            "total_bet": 0,
            "total_won": 0,
            "total_lost": 0,
            "last_bonus": None,
            "level": 1,
            "experience": 0,
            "achievements": [],
            "inventory": {},
            "referrals": [],
            "cases_opened": 0
        }
    return users[user_id]

def send_message(chat_id, text, reply_markup=None):
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
        result = response.json()
        
        if not result.get("ok"):
            logger.error(f"Send message error: {result}")
            
        return result
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        return None

def edit_message(chat_id, message_id, text, reply_markup=None):
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
        result = response.json()
        
        if not result.get("ok"):
            logger.error(f"Edit message error: {result}")
            
        return result
    except Exception as e:
        logger.error(f"Failed to edit message: {e}")
        return None

def answer_callback(callback_query_id, text=""):
    try:
        url = f"{API_URL}/answerCallbackQuery"
        data = {
            "callback_query_id": callback_query_id,
            "text": text
        }
        response = requests.post(url, data=data, timeout=5)
        return response.json()
    except Exception as e:
        logger.error(f"Failed to answer callback: {e}")
        return None

def main_menu_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🚀 Играть в Crash", "callback_data": "play_crash"}],
            [{"text": "🎁 Магазин подарков", "callback_data": "gift_shop"}],
            [{"text": "💰 Баланс", "callback_data": "balance"}, {"text": "📊 Статистика", "callback_data": "stats"}],
            [{"text": "🎁 Ежедневный бонус", "callback_data": "daily_bonus"}],
            [{"text": "🏆 Достижения", "callback_data": "achievements"}, {"text": "💥 Рефералы", "callback_data": "referrals"}],
            [{"text": "🎮 WebApp", "web_app": {"url": f"{WEBHOOK_URL}/webapp"}}]
        ]
    }

def handle_start(chat_id, user_name, referrer_id=None):
    user_data = get_user_data(chat_id)
    
    # Обработка реферальной системы
    if referrer_id and str(referrer_id) != str(chat_id):
        referrer_data = get_user_data(referrer_id)
        if str(chat_id) not in referrer_data['referrals']:
            referrer_data['balance'] += 500
            referrer_data['referrals'].append(str(chat_id))
            user_data['balance'] += 200
            
            send_message(referrer_id, f"🎉 Новый реферал! +500 монет\nВсего рефералов: {len(referrer_data['referrals'])}")
    
    text = f"""🎁 <b>Добро пожаловать в GiftBot, {user_name}!</b>

💰 <b>Баланс:</b> {user_data['balance']} монет
🎯 <b>Уровень:</b> {user_data['level']} ({user_data['experience']} XP)

🚀 <b>Crash Game</b> - главная игра!
🎁 <b>Магазин подарков</b> - купите подарки друзьям
📈 <b>Статистика</b> - ваши достижения

💡 <i>Совет: начните с малых ставок!</i>"""

    send_message(chat_id, text, main_menu_keyboard())

def get_random_item_from_case(case):
    """Получить случайный предмет из кейса с учетом шансов"""
    total_chance = sum(item['chance'] for item in case['items'])
    random_value = random.random() * total_chance
    
    current_chance = 0
    for item in case['items']:
        current_chance += item['chance']
        if random_value <= current_chance:
            return item
    
    return case['items'][0]  # fallback

def get_rarity_from_stars(stars):
    """Определить редкость по количеству звезд"""
    if stars <= 25:
        return "common"
    elif stars <= 100:
        return "uncommon"
    elif stars <= 500:
        return "rare"
    elif stars <= 1000:
        return "epic"
    elif stars <= 2000:
        return "legendary"
    else:
        return "mythic"

def game_loop():
    global current_crash_game
    
    while True:
        try:
            with game_lock:
                current_crash_game = CrashGame()
                
                # Ожидание между играми
                time.sleep(10)
                
                # Запуск новой игры
                current_crash_game.start_round()
                
                # Игровой цикл
                while current_crash_game.is_running and not current_crash_game.is_crashed:
                    current_crash_game.update_multiplier()
                    
                    # Проверка авто-вывода
                    for user_id in list(current_crash_game.bets.keys()):
                        bet_info = current_crash_game.bets[user_id]
                        if (bet_info.get('auto_cashout') and 
                            current_crash_game.multiplier >= bet_info['auto_cashout'] and
                            user_id not in current_crash_game.cashed_out):
                            current_crash_game.cashout(user_id)
                    
                    time.sleep(0.1)
                
                # Обеспечиваем краш если игра завершилась не крашем
                if not current_crash_game.is_crashed:
                    current_crash_game.crash()
                
                # Пауза после краша
                time.sleep(10)
                
        except Exception as e:
            logger.error(f"Game loop error: {e}")
            time.sleep(5)

# Запуск игрового цикла в отдельном потоке
game_thread = threading.Thread(target=game_loop)
game_thread.daemon = True
game_thread.start()

@app.route("/")
def home():
    return """
    <h1>🎁 GiftBot Crash Game 🚀</h1>
    <p>Telegram bot в стиле GiftUp</p>
    """

@app.route("/webapp")
def webapp():
    html_content = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GiftBot WebApp</title>
    <style>
        body {
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: white;
            min-height: 100vh;
        }
        .container {
            max-width: 400px;
            margin: 0 auto;
            text-align: center;
        }
        h1 {
            margin-bottom: 30px;
            font-size: 28px;
        }
        .game-area {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 20px;
            margin: 20px 0;
            backdrop-filter: blur(10px);
        }
        .button {
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            border: none;
            border-radius: 12px;
            color: white;
            font-size: 16px;
            padding: 12px 24px;
            margin: 10px 5px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .button:hover {
            transform: translateY(-2px);
        }
        .status {
            font-size: 24px;
            margin: 20px 0;
            font-weight: bold;
        }
        .balance {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 12px;
            padding: 15px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎁 GiftBot WebApp</h1>
        
        <div class="balance">
            <div>💰 Баланс: <span id="balance">1000</span> монет</div>
        </div>
        
        <div class="game-area">
            <div class="status">🚀 Crash Game</div>
            <div id="multiplier">1.00x</div>
            <div id="status">Ожидание...</div>
            
            <button class="button" onclick="placeBet(50)">Ставка 50</button>
            <button class="button" onclick="placeBet(100)">Ставка 100</button>
            <button class="button" onclick="cashOut()" id="cashoutBtn" disabled>💸 Вывести</button>
        </div>
        
        <div class="game-area">
            <h3>🎁 Магазин подарков</h3>
            <p>Открывайте кейсы и получайте редкие подарки!</p>
            <button class="button" onclick="openCase()">Открыть кейс (50 монет)</button>
        </div>
    </div>
    
    <script>
        let gameState = {
            balance: 1000,
            currentBet: 0,
            isPlaying: false
        };
        
        function updateBalance() {
            document.getElementById('balance').textContent = gameState.balance;
        }
        
        function placeBet(amount) {
            if (gameState.isPlaying) {
                alert('Игра уже идет!');
                return;
            }
            
            if (gameState.balance < amount) {
                alert('Недостаточно монет!');
                return;
            }
            
            gameState.balance -= amount;
            gameState.currentBet = amount;
            gameState.isPlaying = true;
            
            updateBalance();
            document.getElementById('cashoutBtn').disabled = false;
            document.getElementById('status').textContent = 'Игра идет...';
            
            // Симуляция игры
            setTimeout(() => {
                if (Math.random() < 0.7) {
                    // Проиграл
                    gameState.isPlaying = false;
                    document.getElementById('cashoutBtn').disabled = true;
                    document.getElementById('status').textContent = 'Краш! Попробуйте еще раз';
                    gameState.currentBet = 0;
                } else {
                    // Выиграл
                    const multiplier = 1.5 + Math.random() * 2;
                    const winAmount = Math.floor(gameState.currentBet * multiplier);
                    gameState.balance += winAmount;
                    gameState.isPlaying = false;
                    gameState.currentBet = 0;
                    
                    updateBalance();
                    document.getElementById('cashoutBtn').disabled = true;
                    document.getElementById('status').textContent = `Выигрыш! +${winAmount} монет`;
                }
            }, 3000 + Math.random() * 5000);
        }
        
        function cashOut() {
            if (!gameState.isPlaying) return;
            
            const multiplier = 1.2 + Math.random() * 1.5;
            const winAmount = Math.floor(gameState.currentBet * multiplier);
            
            gameState.balance += winAmount;
            gameState.isPlaying = false;
            gameState.currentBet = 0;
            
            updateBalance();
            document.getElementById('cashoutBtn').disabled = true;
            document.getElementById('status').textContent = `Вывод! +${winAmount} монет`;
        }
        
        function openCase() {
            if (gameState.balance < 50) {
                alert('Недостаточно монет для открытия кейса!');
                return;
            }
            
            gameState.balance -= 50;
            updateBalance();
            
            const gifts = ['🎂 Торт', '💚 Зеленая звезда', '🎆 Фейерверк', '💙 Синяя звезда', '❤️ Красное сердце'];
            const gift = gifts[Math.floor(Math.random() * gifts.length)];
            
            alert(`Поздравляем! Вы получили: ${gift}`);
        }
        
        updateBalance();
    </script>
</body>
</html>'''
    return html_content

@app.route(f"/{TOKEN}", methods=['POST'])
def webhook():
    try:
        update = request.get_json()
        
        if 'message' in update:
            message = update['message']
            chat_id = message['chat']['id']
            text = message.get('text', '')
            user_name = message['from'].get('first_name', 'User')
            
            if text.startswith('/start'):
                # Обработка реферальной ссылки
                referrer_id = None
                if ' ' in text:
                    try:
                        referrer_id = int(text.split()[1])
                    except:
                        pass
                handle_start(chat_id, user_name, referrer_id)
                
        elif 'callback_query' in update:
            callback = update['callback_query']
            chat_id = callback['message']['chat']['id']
            message_id = callback['message']['message_id']
            data = callback['data']
            user_id = callback['from']['id']
            user_name = callback['from'].get('first_name', 'User')
            
            handle_callback(chat_id, message_id, data, user_id, user_name, callback['id'])
            
        return jsonify({"ok": True})
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"ok": False})

def handle_callback(chat_id, message_id, data, user_id, user_name, callback_id):
    try:
        user_data = get_user_data(user_id)
        
        if data == "play_crash":
            handle_crash_game(chat_id, message_id, user_id)
            
        elif data == "balance":
            text = f"""💰 <b>Ваш баланс</b>

💎 <b>Монеты:</b> {user_data['balance']}
🎯 <b>Уровень:</b> {user_data['level']} ({user_data['experience']} XP)

📊 <b>Статистика игр:</b>
🎮 Игр сыграно: {user_data['games_played']}
✅ Выиграно: {user_data['games_won']}
❌ Проиграно: {user_data['games_lost']}
💰 Общий выигрыш: {user_data['total_won']}"""

            keyboard = {
                "inline_keyboard": [
                    [{"text": "🔙 Назад", "callback_data": "main_menu"}]
                ]
            }
            edit_message(chat_id, message_id, text, keyboard)
            
        elif data == "gift_shop":
            handle_gift_shop(chat_id, message_id, user_id)
            
        elif data == "daily_bonus":
            handle_daily_bonus(chat_id, message_id, user_id)
            
        elif data == "stats":
            winrate = round((user_data['games_won'] / max(user_data['games_played'], 1)) * 100, 1)
            text = f"""📊 <b>Статистика {user_name}</b>

🎮 <b>Игры:</b>
• Сыграно: {user_data['games_played']}
• Выиграно: {user_data['games_won']}
• Проиграно: {user_data['games_lost']}
• Винрейт: {winrate}%

💰 <b>Финансы:</b>
• Поставлено: {user_data['total_bet']}
• Выиграно: {user_data['total_won']}
• Проиграно: {user_data['total_lost']}

🎁 <b>Подарки:</b>
• Кейсов открыто: {user_data['cases_opened']}
• Отправлено: {user_data['gifts_sent']}
• Получено: {user_data['gifts_received']}

👥 <b>Рефералы:</b> {len(user_data['referrals'])}"""

            keyboard = {
                "inline_keyboard": [
                    [{"text": "🔙 Назад", "callback_data": "main_menu"}]
                ]
            }
            edit_message(chat_id, message_id, text, keyboard)
            
        elif data == "main_menu":
            text = f"""🎁 <b>Главное меню</b>

💰 <b>Баланс:</b> {user_data['balance']} монет
🎯 <b>Уровень:</b> {user_data['level']} ({user_data['experience']} XP)

Выберите действие:"""
            edit_message(chat_id, message_id, text, main_menu_keyboard())
            
        elif data.startswith("bet_"):
            amount = int(data.split("_")[1])
            handle_crash_bet(chat_id, message_id, user_id, amount, callback_id)
            
        elif data == "crash_cashout":
            handle_crash_cashout(chat_id, message_id, user_id, callback_id)
            
        elif data.startswith("open_case_"):
            case_id = data.replace("open_case_", "")
            handle_open_case(chat_id, message_id, user_id, case_id, callback_id)
            
        answer_callback(callback_id)
        
    except Exception as e:
        logger.error(f"Callback error: {e}")
        answer_callback(callback_id, "❌ Произошла ошибка")

def handle_crash_game(chat_id, message_id, user_id):
    global current_crash_game
    
    if current_crash_game is None:
        text = "🔄 Игра загружается..."
    elif current_crash_game.is_running:
        text = f"""🚀 <b>Crash Game - Игра идет!</b>

📈 <b>Множитель:</b> {current_crash_game.multiplier:.2f}x
🎮 <b>Игроков в игре:</b> {len(current_crash_game.bets)}

⚡ Игра может крашнуться в любой момент!"""
    else:
        text = """🚀 <b>Crash Game</b>

🎯 <b>Как играть:</b>
• Сделайте ставку
• Множитель растет с 1.00x
• Выведите до краша!

💡 <b>Совет:</b> Начните с малых ставок"""

    keyboard = {
        "inline_keyboard": [
            [{"text": "💰 50", "callback_data": "bet_50"}, {"text": "💰 100", "callback_data": "bet_100"}],
            [{"text": "💰 250", "callback_data": "bet_250"}, {"text": "💰 500", "callback_data": "bet_500"}],
            [{"text": "💸 Вывести", "callback_data": "crash_cashout"}],
            [{"text": "🔄 Обновить", "callback_data": "play_crash"}],
            [{"text": "🔙 Назад", "callback_data": "main_menu"}]
        ]
    }
    
    edit_message(chat_id, message_id, text, keyboard)

def handle_crash_bet(chat_id, message_id, user_id, amount, callback_id):
    global current_crash_game
    
    if current_crash_game is None:
        answer_callback(callback_id, "❌ Игра не найдена")
        return
    
    success, message = current_crash_game.place_bet(user_id, amount)
    answer_callback(callback_id, message)
    
    if success:
        handle_crash_game(chat_id, message_id, user_id)

def handle_crash_cashout(chat_id, message_id, user_id, callback_id):
    global current_crash_game
    
    if current_crash_game is None:
        answer_callback(callback_id, "❌ Игра не найдена")
        return
    
    success, message = current_crash_game.cashout(user_id)
    answer_callback(callback_id, message)
    
    if success:
        handle_crash_game(chat_id, message_id, user_id)

def handle_gift_shop(chat_id, message_id, user_id):
    text = """🎁 <b>Магазин подарков</b>

🎰 Открывайте кейсы и получайте редкие подарки!

💎 Каждый кейс содержит уникальные предметы с разной редкостью."""

    keyboard = {
        "inline_keyboard": []
    }
    
    for case_id, case_info in list(CASES.items())[:6]:  # Показываем первые 6 кейсов
        keyboard["inline_keyboard"].append([{
            "text": f"{case_info['emoji']} {case_info['name']} - {case_info['price']} монет",
            "callback_data": f"open_case_{case_id}"
        }])
    
    keyboard["inline_keyboard"].append([{"text": "🔙 Назад", "callback_data": "main_menu"}])
    
    edit_message(chat_id, message_id, text, keyboard)

def handle_open_case(chat_id, message_id, user_id, case_id, callback_id):
    user_data = get_user_data(user_id)
    
    if case_id not in CASES:
        answer_callback(callback_id, "❌ Кейс не найден")
        return
    
    case = CASES[case_id]
    
    if user_data['balance'] < case['price']:
        answer_callback(callback_id, "❌ Недостаточно монет")
        return
    
    # Списываем стоимость кейса
    user_data['balance'] -= case['price']
    user_data['cases_opened'] += 1
    
    # Получаем случайный предмет
    item = get_random_item_from_case(case)
    gift = REAL_TELEGRAM_GIFTS[item['id']]
    
    # Добавляем в инвентарь
    if item['id'] not in user_data['inventory']:
        user_data['inventory'][item['id']] = 0
    user_data['inventory'][item['id']] += 1
    
    # Добавляем опыт
    user_data['experience'] += gift['stars'] // 10
    
    rarity_emoji = {
        'common': '⚪',
        'uncommon': '🟢', 
        'rare': '🔵',
        'epic': '🟣',
        'legendary': '🟠',
        'mythic': '🔴'
    }
    
    text = f"""🎉 <b>Кейс открыт!</b>

{gift['emoji']} <b>{gift['name']}</b>
💫 <b>Звезд:</b> {gift['stars']}
{rarity_emoji.get(gift['rarity'], '⚪')} <b>Редкость:</b> {gift['rarity'].title()}

💰 <b>Баланс:</b> {user_data['balance']} монет
📦 <b>Кейсов открыто:</b> {user_data['cases_opened']}"""

    keyboard = {
        "inline_keyboard": [
            [{"text": "🎁 Открыть еще", "callback_data": f"open_case_{case_id}"}],
            [{"text": "🛍 Магазин", "callback_data": "gift_shop"}],
            [{"text": "🔙 Главное меню", "callback_data": "main_menu"}]
        ]
    }
    
    edit_message(chat_id, message_id, text, keyboard)
    answer_callback(callback_id, f"🎉 Получен {gift['name']}!")

def handle_daily_bonus(chat_id, message_id, user_id):
    user_data = get_user_data(user_id)
    now = datetime.now()
    
    if user_data['last_bonus']:
        last_bonus = datetime.fromisoformat(user_data['last_bonus'])
        if now - last_bonus < timedelta(hours=24):
            remaining = timedelta(hours=24) - (now - last_bonus)
            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60
            
            text = f"""⏰ <b>Ежедневный бонус</b>

❌ Вы уже получали бонус сегодня!

🕐 Следующий бонус через: {hours}ч {minutes}м"""
            
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🔙 Назад", "callback_data": "main_menu"}]
                ]
            }
            edit_message(chat_id, message_id, text, keyboard)
            return
    
    # Выдаем бонус
    bonus_amount = random.randint(100, 500)
    user_data['balance'] += bonus_amount
    user_data['last_bonus'] = now.isoformat()
    user_data['experience'] += 10
    
    text = f"""🎁 <b>Ежедневный бонус получен!</b>

💰 <b>Получено:</b> {bonus_amount} монет
⭐ <b>Получено:</b> 10 опыта

💎 <b>Текущий баланс:</b> {user_data['balance']} монет

🕐 <b>Следующий бонус через:</b> 24 часа"""

    keyboard = {
        "inline_keyboard": [
            [{"text": "🔙 Назад", "callback_data": "main_menu"}]
        ]
    }
    edit_message(chat_id, message_id, text, keyboard)

# Установка вебхука при запуске
def set_webhook():
    url = f"{API_URL}/setWebhook"
    webhook_url = f"{WEBHOOK_URL}/{TOKEN}"
    data = {"url": webhook_url}
    
    try:
        response = requests.post(url, data=data, timeout=10)
        result = response.json()
        logger.info(f"Webhook set result: {result}")
    except Exception as e:
        logger.error(f"Failed to set webhook: {e}")

if __name__ == '__main__':
    set_webhook()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
