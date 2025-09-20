import os
import requests
import json
import random
import time
import threading
from flask import Flask, request, jsonify
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

# Система подарков как в GiftUp
GIFTS = {
    "delicious_cake": {"name": "🎂 Вкусный торт", "price": 1, "emoji": "🎂", "rarity": "common"},
    "green_star": {"name": "💚 Зеленая звезда", "price": 2, "emoji": "💚", "rarity": "common"},
    "fireworks": {"name": "🎆 Фейерверк", "price": 5, "emoji": "🎆", "rarity": "uncommon"},
    "blue_star": {"name": "💙 Синяя звезда", "price": 10, "emoji": "💙", "rarity": "uncommon"},
    "red_heart": {"name": "❤️ Красное сердце", "price": 25, "emoji": "❤️", "rarity": "rare"},
    "golden_premium": {"name": "👑 Золото Премиум", "price": 100, "emoji": "👑", "rarity": "epic"},
    "platinum_premium": {"name": "💎 Платина Премиум", "price": 250, "emoji": "💎", "rarity": "legendary"},
    "limited_gift": {"name": "🔮 Лимитированный подарок", "price": 500, "emoji": "🔮", "rarity": "mythic"}
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
            "referrals": []
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
            [{"text": "🏆 Достижения", "callback_data": "achievements"}, {"text": "👥 Рефералы", "callback_data": "referrals"}],
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

def handle_crash_game(chat_id, message_id):
    global current_crash_game
    
    user_data = get_user_data(chat_id)
    
    if current_crash_game and current_crash_game.is_running:
        game_status = f"🚀 Игра идет! x{current_crash_game.multiplier:.2f}"
        if str(chat_id) in current_crash_game.bets:
            bet_info = current_crash_game.bets[str(chat_id)]
            game_status += f"\n💰 Ваша ставка: {bet_info['amount']} монет"
            if str(chat_id) in current_crash_game.cashed_out:
                game_status += f"\n✅ Выведено при x{current_crash_game.cashed_out[str(chat_id)]:.2f}"
    elif current_crash_game and current_crash_game.is_crashed:
        game_status = f"💥 Краш при x{current_crash_game.multiplier:.2f}!\nСледующая игра через 10 секунд..."
    else:
        game_status = "⏳ Ожидание начала игры..."
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🎯 Ставка 10", "callback_data": "bet_10"}, {"text": "🎯 Ставка 50", "callback_data": "bet_50"}],
            [{"text": "🎯 Ставка 100", "callback_data": "bet_100"}, {"text": "🎯 Ставка 500", "callback_data": "bet_500"}],
            [{"text": "💸 Вывести", "callback_data": "cashout"}],
            [{"text": "📈 История игр", "callback_data": "game_history"}],
            [{"text": "🔙 Назад", "callback_data": "main"}]
        ]
    }
    
    text = f"""🚀 <b>Crash Game</b>

💰 <b>Ваш баланс:</b> {user_data['balance']} монет

🎮 <b>Статус игры:</b>
{game_status}

📊 <b>Ваша статистика:</b>
• Игр сыграно: {user_data['games_played']}
• Побед: {user_data['games_won']}
• Поражений: {user_data['games_lost']}
• Выиграно: {user_data['total_won']} монет

❓ <b>Как играть:</b>
1. Сделайте ставку до начала раунда
2. Следите за растущим множителем
3. Выведите до краша!"""

    edit_message(chat_id, message_id, text, keyboard)

def handle_bet(chat_id, message_id, amount):
    global current_crash_game
    
    if not current_crash_game or current_crash_game.is_running:
        return
    
    success, message = current_crash_game.place_bet(chat_id, amount)
    
    if success:
        handle_crash_game(chat_id, message_id)

def handle_cashout(chat_id, callback_query_id):
    global current_crash_game
    
    if not current_crash_game:
        answer_callback(callback_query_id, "Игра не идет")
        return
    
    success, message = current_crash_game.cashout(chat_id)
    answer_callback(callback_query_id, message)

def handle_gift_shop(chat_id, message_id):
    keyboard = {"inline_keyboard": []}
    
    rarities = {
        "common": [],
        "uncommon": [],
        "rare": [],
        "epic": [],
        "legendary": [],
        "mythic": []
    }
    
    for gift_id, gift_info in GIFTS.items():
        rarities[gift_info['rarity']].append((gift_id, gift_info))
    
    for rarity, gifts in rarities.items():
        if gifts:
            rarity_names = {
                "common": "⚪ Обычные",
                "uncommon": "🟢 Необычные", 
                "rare": "🔵 Редкие",
                "epic": "🟣 Эпические",
                "legendary": "🟡 Легендарные",
                "mythic": "🔴 Мифические"
            }
            keyboard["inline_keyboard"].append([{
                "text": rarity_names[rarity],
                "callback_data": f"rarity_{rarity}"
            }])
    
    keyboard["inline_keyboard"].append([{"text": "🔙 Назад", "callback_data": "main"}])
    
    text = """🎁 <b>Магазин подарков</b>

Выберите категорию подарков:

⚪ <b>Обычные</b> - доступные подарки
🟢 <b>Необычные</b> - более редкие
🔵 <b>Редкие</b> - ценные подарки
🟣 <b>Эпические</b> - очень редкие
🟡 <b>Легендарные</b> - эксклюзивные
🔴 <b>Мифические</b> - уникальные

💡 <i>Подарки можно отправлять друзьям!</i>"""

    edit_message(chat_id, message_id, text, keyboard)

def handle_rarity_selection(chat_id, message_id, rarity):
    keyboard = {"inline_keyboard": []}
    
    for gift_id, gift_info in GIFTS.items():
        if gift_info['rarity'] == rarity:
            keyboard["inline_keyboard"].append([{
                "text": f"{gift_info['emoji']} {gift_info['name']} - {gift_info['price']} монет",
                "callback_data": f"buy_{gift_id}"
            }])
    
    keyboard["inline_keyboard"].append([
        {"text": "🔙 К категориям", "callback_data": "gift_shop"},
        {"text": "🏠 Главное меню", "callback_data": "main"}
    ])
    
    rarity_names = {
        "common": "⚪ Обычные",
        "uncommon": "🟢 Необычные", 
        "rare": "🔵 Редкие",
        "epic": "🟣 Эпические",
        "legendary": "🟡 Легендарные",
        "mythic": "🔴 Мифические"
    }
    
    text = f"""🎁 <b>{rarity_names[rarity]} подарки</b>

Выберите подарок для покупки:"""

    edit_message(chat_id, message_id, text, keyboard)

def handle_buy_gift(chat_id, message_id, gift_id):
    user_data = get_user_data(chat_id)
    gift = GIFTS.get(gift_id)
    
    if not gift:
        return
    
    if user_data['balance'] < gift['price']:
        keyboard = {
            "inline_keyboard": [
                [{"text": "💰 Получить бонус", "callback_data": "daily_bonus"}],
                [{"text": "🔙 К подаркам", "callback_data": "gift_shop"}]
            ]
        }
        text = f"""❌ <b>Недостаточно средств!</b>

💰 <b>Баланс:</b> {user_data['balance']} монет
💸 <b>Нужно:</b> {gift['price']} монет

{gift['emoji']} <b>{gift['name']}</b>"""
        edit_message(chat_id, message_id, text, keyboard)
        return
    
    user_data['balance'] -= gift['price']
    user_data['gifts_sent'] += 1
    user_data['total_spent'] += gift['price']
    user_data['experience'] += gift['price'] // 10
    
    if gift_id not in user_data['inventory']:
        user_data['inventory'][gift_id] = 0
    user_data['inventory'][gift_id] += 1
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🎁 Купить еще", "callback_data": "gift_shop"}],
            [{"text": "🏠 Главное меню", "callback_data": "main"}]
        ]
    }
    
    text = f"""✅ <b>Подарок куплен!</b>

🎁 <b>{gift['name']}</b>
💰 <b>Списано:</b> {gift['price']} монет  
💳 <b>Остаток:</b> {user_data['balance']} монет
⭐ <b>Получено XP:</b> {gift['price'] // 10}

🎉 <b>Подарок добавлен в инвентарь!</b>"""

    edit_message(chat_id, message_id, text, keyboard)

def handle_daily_bonus(chat_id, message_id):
    user_data = get_user_data(chat_id)
    
    # Проверяем, можно ли получить бонус
    now = datetime.now()
    last_bonus = user_data.get('last_bonus')
    
    if last_bonus:
        last_bonus_date = datetime.fromisoformat(last_bonus)
        if (now - last_bonus_date).days < 1:
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🔙 Назад", "callback_data": "main"}]
                ]
            }
            hours_left = 24 - (now - last_bonus_date).seconds // 3600
            text = f"""⏰ <b>Ежедневный бонус уже получен!</b>

Следующий бонус через {hours_left} часов

💰 <b>Текущий баланс:</b> {user_data['balance']} монет"""
            edit_message(chat_id, message_id, text, keyboard)
            return
    
    # Выдаем бонус
    bonus_amount = random.randint(100, 500)
    user_data['balance'] += bonus_amount
    user_data['last_bonus'] = now.isoformat()
    user_data['experience'] += 50
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🚀 Играть", "callback_data": "play_crash"}],
            [{"text": "🏠 Главное меню", "callback_data": "main"}]
        ]
    }
    
    text = f"""🎉 <b>Ежедневный бонус получен!</b>

💰 <b>Получено:</b> {bonus_amount} монет
⭐ <b>Получено XP:</b> 50
💳 <b>Новый баланс:</b> {user_data['balance']} монет

🎁 Возвращайтесь завтра за новым бонусом!"""

    edit_message(chat_id, message_id, text, keyboard)

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

def handle_webhook_callback(chat_id, message_id, callback_data, user_name):
    try:
        if callback_data == "main":
            user_data = get_user_data(chat_id)
            text = f"""🎁 <b>GiftBot - {user_name}</b>

💰 <b>Баланс:</b> {user_data['balance']} монет
🎯 <b>Уровень:</b> {user_data['level']} ({user_data['experience']} XP)

Выберите действие:"""
            edit_message(chat_id, message_id, text, main_menu_keyboard())
            
        elif callback_data == "play_crash":
            handle_crash_game(chat_id, message_id)
            
        elif callback_data.startswith("bet_"):
            amount = int(callback_data.split("_")[1])
            handle_bet(chat_id, message_id, amount)
            
        elif callback_data == "cashout":
            handle_cashout(chat_id, "")
            handle_crash_game(chat_id, message_id)
            
        elif callback_data == "gift_shop":
            handle_gift_shop(chat_id, message_id)
            
        elif callback_data.startswith("rarity_"):
            rarity = callback_data.replace("rarity_", "")
            handle_rarity_selection(chat_id, message_id, rarity)
            
        elif callback_data.startswith("buy_"):
            gift_id = callback_data.replace("buy_", "")
            handle_buy_gift(chat_id, message_id, gift_id)
            
        elif callback_data == "daily_bonus":
            handle_daily_bonus(chat_id, message_id)
            
        elif callback_data in ["balance", "stats"]:
            user_data = get_user_data(chat_id)
            win_rate = (user_data['games_won'] / max(user_data['games_played'], 1)) * 100
            
            text = f"""📊 <b>Статистика - {user_name}</b>

💰 <b>Баланс:</b> {user_data['balance']} монет
🎯 <b>Уровень:</b> {user_data['level']} (XP: {user_data['experience']})

🎮 <b>Игровая статистика:</b>
• Игр сыграно: {user_data['games_played']}
• Побед: {user_data['games_won']}
• Поражений: {user_data['games_lost']}
• Винрейт: {win_rate:.1f}%

💸 <b>Финансы:</b>
• Поставлено: {user_data['total_bet']} монет
• Выиграно: {user_data['total_won']} монет
• Потеряно: {user_data['total_lost']} монет

🎁 <b>Подарки:</b>
• Отправлено: {user_data['gifts_sent']}
• Потрачено: {user_data['total_spent']} монет"""

            keyboard = {
                "inline_keyboard": [
                    [{"text": "🚀 Играть", "callback_data": "play_crash"}],
                    [{"text": "🔙 Назад", "callback_data": "main"}]
                ]
            }
            edit_message(chat_id, message_id, text, keyboard)
            
        elif callback_data == "referrals":
            user_data = get_user_data(chat_id)
            referral_count = len(user_data.get('referrals', []))
            
            text = f"""👥 <b>Реферальная система</b>

👥 <b>Ваши рефералы:</b> {referral_count}
💰 <b>Заработано:</b> {referral_count * 500} монет

🔗 <b>Ваша реферальная ссылка:</b>
https://t.me/lambo_gift_bot?start={chat_id}

💡 <b>За каждого реферала:</b>
• Вы получаете 500 монет
• Реферал получает 200 монет"""

            keyboard = {
                "inline_keyboard": [
                    [{"text": "🔙 Назад", "callback_data": "main"}]
                ]
            }
            edit_message(chat_id, message_id, text, keyboard)
            
    except Exception as e:
        logger.error(f"Callback handling error: {e}")

@app.route("/webapp")  
def webapp():
    html_content = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GiftBot Crash Game</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e, #16213e, #0f3460);
            color: #fff; min-height: 100vh; overflow: hidden;
        }
        .container { max-width: 400px; margin: 0 auto; padding: 20px; position: relative; }
        .game-header { 
            text-align: center; margin-bottom: 20px; background: rgba(255,255,255,0.1);
            padding: 20px; border-radius: 20px; backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        .balance { font-size: 20px; font-weight: bold; color: #ffd700; }
        .crash-display {
            position: relative; height: 300px; background: linear-gradient(45deg, #1e3c72, #2a5298);
            border-radius: 20px; margin-bottom: 20px; overflow: hidden; border: 2px solid #ffd700;
            display: flex; align-items: center; justify-content: center;
        }
        .multiplier { 
            font-size: 48px; font-weight: bold; color: #00ff00; 
            text-shadow: 0 0 20px #00ff00; transition: all 0.1s ease;
        }
        .multiplier.crashed { color: #ff0000; text-shadow: 0 0 20px #ff0000; }
        .controls { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px; }
        .bet-input { 
            padding: 15px; background: rgba(255,255,255,0.1); 
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 15px; color: #fff; font-size: 16px; text-align: center;
        }
        .btn { 
            padding: 15px; border: none; border-radius: 15px; font-weight: bold; 
            font-size: 16px; cursor: pointer; transition: all 0.3s ease; text-transform: uppercase;
        }
        .btn-bet { background: linear-gradient(45deg, #00ff00, #32cd32); color: #000; }
        .btn-cashout { background: linear-gradient(45deg, #ff6b6b, #ff4757); color: #fff; }
        .btn:disabled { background: rgba(255,255,255,0.3); cursor: not-allowed; }
        .game-info { 
            background: rgba(255,255,255,0.1); padding: 15px; 
            border-radius: 15px; margin-bottom: 20px; 
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="game-header">
            <div class="balance">💰 <span id="balance">1000</span> монет</div>
            <div>🚀 Crash Game</div>
        </div>
        
        <div class="crash-display">
            <div class="multiplier" id="multiplier">1.00x</div>
        </div>
        
        <div class="controls">
            <input type="number" class="bet-input" id="betAmount" placeholder="Ставка" min="1" value="10">
            <button class="btn btn-bet" id="betButton" onclick="placeBet()">Ставка</button>
            <input type="number" class="bet-input" id="autoCashout" placeholder="Авто-вывод" min="1.01" step="0.01">
            <button class="btn btn-cashout" id="cashoutButton" onclick="cashOut()" disabled>Вывести</button>
        </div>
        
        <div class="game-info">
            <div>Статус: <span id="gameStatus">Ожидание...</span></div>
            <div>Ваша ставка: <span id="currentBet">-</span></div>
            <div>Потенциальный выигрыш: <span id="potentialWin">-</span></div>
        </div>
    </div>
    
    <script>
        if (window.Telegram && window.Telegram.WebApp) {
            window.Telegram.WebApp.ready();
            window.Telegram.WebApp.expand();
        }
        
        let gameData = {
            balance: 1000, currentBet: 0, multiplier: 1.0,
            isPlaying: false, gameRunning: false
        };
        
        function updateDisplay() {
            document.getElementById("balance").textContent = gameData.balance;
            document.getElementById("multiplier").textContent = gameData.multiplier.toFixed(2) + "x";
            document.getElementById("currentBet").textContent = gameData.currentBet || "-";
            
            if (gameData.currentBet) {
                const potential = Math.floor(gameData.currentBet * gameData.multiplier);
                document.getElementById("potentialWin").textContent = potential + " монет";
            }
        }
        
        function placeBet() {
            const betAmount = parseInt(document.getElementById("betAmount").value);
            
            if (!betAmount || betAmount < 1 || gameData.balance < betAmount || gameData.gameRunning) {
                return;
            }
            
            gameData.balance -= betAmount;
            gameData.currentBet = betAmount;
            gameData.isPlaying = true;
            
            document.getElementById("betButton").disabled = true;
            document.getElementById("cashoutButton").disabled = false;
            document.getElementById("gameStatus").textContent = "Ставка принята";
            
            updateDisplay();
        }
        
        function cashOut() {
            if (!gameData.isPlaying || !gameData.gameRunning) return;
            
            const winAmount = Math.floor(gameData.currentBet * gameData.multiplier);
            gameData.balance += winAmount;
            gameData.isPlaying = false;
            
            document.getElementById("cashoutButton").disabled = true;
            document.getElementById("gameStatus").textContent = "Выведено: " + winAmount + " монет";
            
            updateDisplay();
        }
        
        function simulateGame() {
            gameData.multiplier = 1.0;
            gameData.gameRunning = false;
            
            document.getElementById("betButton").disabled = false;
            document.getElementById("cashoutButton").disabled = true;
            document.getElementById("gameStatus").textContent = "Прием ставок...";
            
            setTimeout(function() {
                gameData.gameRunning = true;
                document.getElementById("betButton").disabled = true;
                document.getElementById("gameStatus").textContent = "Игра началась!";
                
                const crashPoint = Math.random() * 3 + 1.01;
                
                const gameInterval = setInterval(function() {
                    gameData.multiplier += 0.01 + (gameData.multiplier * 0.001);
                    
                    if (gameData.multiplier >= crashPoint) {
                        crash();
                        clearInterval(gameInterval);
                    }
                    
                    updateDisplay();
                }, 100);
                
            }, 5000);
        }
        
        function crash() {
            gameData.gameRunning = false;
            
            const multiplierElement = document.getElementById("multiplier");
            multiplierElement.classList.add("crashed");
            multiplierElement.textContent = "КРАШ!";
            
            if (gameData.isPlaying) {
                gameData.isPlaying = false;
                document.getElementById("gameStatus").textContent = "Краш - проигрыш!";
            }
            
            setTimeout(function() {
                multiplierElement.classList.remove("crashed");
                gameData.currentBet = 0;
                gameData.isPlaying = false;
                updateDisplay();
                simulateGame();
            }, 3000);
        }
        
        updateDisplay();
        simulateGame();
    </script>
</body>
</html>'''
    return html_content

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        
        if "message" in data:
            message = data["message"]
            chat_id = message["chat"]["id"]
            user_name = message["from"].get("first_name", "Пользователь")
            text = message.get("text", "")
            
            if text.startswith("/start"):
                referrer_id = None
                if " " in text:
                    try:
                        referrer_id = int(text.split()[1])
                    except:
                        pass
                handle_start(chat_id, user_name, referrer_id)
        
        elif "callback_query" in data:
            callback = data["callback_query"]
            chat_id = callback["message"]["chat"]["id"]
            message_id = callback["message"]["message_id"]
            callback_data = callback["data"]
            user_name = callback["from"].get("first_name", "Пользователь")
            
            answer_callback(callback["id"])
            
            handle_webhook_callback(chat_id, message_id, callback_data, user_name)
        
        return "OK"
    
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "ERROR", 500

def setup_webhook():
    try:
        webhook_url = f"{WEBHOOK_URL}/webhook"
        response = requests.post(f"{API_URL}/setWebhook", data={"url": webhook_url})
        result = response.json()
        
        if result.get("ok"):
            logger.info(f"Webhook установлен успешно: {webhook_url}")
            return True
        else:
            logger.error(f"Ошибка установки webhook: {result}")
            return False
    except Exception as e:
        logger.error(f"Failed to setup webhook: {e}")
        return False

if __name__ == "__main__":
    setup_webhook()
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
