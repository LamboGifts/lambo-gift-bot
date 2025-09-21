<p style="opacity: 0.8; margin-bottom: 30px;">
                    ${gift.collectible ? '🏆 Коллекционный подарок (может стать NFT)' : 'import os
import requests
import json
import random
import time
import threading
from flask import Flask, request, jsonify, render_template_string
import logging
from datetime import datetime, timedelta
import uuid

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

# Глобальные переменные
users = {}
active_gifts = {}
gift_history = []
leaderboard_cache = {"data": [], "last_update": 0}

# Официальные подарки Telegram с реальными ценами в звездах
TELEGRAM_GIFTS = {
    # Premium/Ultra Rare - Самые дорогие и редкие
    "delicious_cake": {"name": "🎂 Delicious Cake", "stars": 2500, "emoji": "🎂", "rarity": "ultra_rare", "collectible": True},
    "green_star": {"name": "💚 Green Star", "stars": 2000, "emoji": "💚", "rarity": "ultra_rare", "collectible": True},
    
    # Mythic/Legendary - Очень дорогие сезонные
    "santa_hat": {"name": "🎅 Santa Hat", "stars": 1500, "emoji": "🎅", "rarity": "mythic", "seasonal": "winter", "collectible": True},
    "spiced_wine": {"name": "🍷 Spiced Wine", "stars": 1200, "emoji": "🍷", "rarity": "mythic", "seasonal": "winter", "collectible": True},
    "jelly_bunny": {"name": "🐰 Jelly Bunny", "stars": 1000, "emoji": "🐰", "rarity": "mythic", "seasonal": "easter", "collectible": True},
    "ghost": {"name": "👻 Ghost", "stars": 900, "emoji": "👻", "rarity": "mythic", "seasonal": "halloween", "collectible": True},
    
    # Legendary - Дорогие праздничные
    "christmas_tree": {"name": "🎄 Christmas Tree", "stars": 800, "emoji": "🎄", "rarity": "legendary", "seasonal": "winter"},
    "jack_o_lantern": {"name": "🎃 Jack-o'-lantern", "stars": 750, "emoji": "🎃", "rarity": "legendary", "seasonal": "halloween"},
    "love_letter": {"name": "💌 Love Letter", "stars": 700, "emoji": "💌", "rarity": "legendary", "seasonal": "valentine"},
    "birthday_cake": {"name": "🧁 Birthday Cake", "stars": 650, "emoji": "🧁", "rarity": "legendary"},
    "fireworks": {"name": "🎆 Fireworks", "stars": 600, "emoji": "🎆", "rarity": "legendary"},
    
    # Epic - Средне-дорогие
    "golden_star": {"name": "⭐ Golden Star", "stars": 500, "emoji": "⭐", "rarity": "epic"},
    "party_hat": {"name": "🎉 Party Hat", "stars": 450, "emoji": "🎉", "rarity": "epic"},
    "champagne": {"name": "🥂 Champagne", "stars": 400, "emoji": "🥂", "rarity": "epic"},
    "gift_box": {"name": "🎁 Gift Box", "stars": 350, "emoji": "🎁", "rarity": "epic"},
    "chocolate": {"name": "🍫 Chocolate", "stars": 300, "emoji": "🍫", "rarity": "epic"},
    "balloon": {"name": "🎈 Balloon", "stars": 250, "emoji": "🎈", "rarity": "epic"},
    
    # Rare - Доступные подарки  
    "red_heart": {"name": "❤️ Red Heart", "stars": 200, "emoji": "❤️", "rarity": "rare"},
    "blue_heart": {"name": "💙 Blue Heart", "stars": 180, "emoji": "💙", "rarity": "rare"},
    "purple_heart": {"name": "💜 Purple Heart", "stars": 160, "emoji": "💜", "rarity": "rare"},
    "yellow_heart": {"name": "💛 Yellow Heart", "stars": 140, "emoji": "💛", "rarity": "rare"},
    "orange_heart": {"name": "🧡 Orange Heart", "stars": 120, "emoji": "🧡", "rarity": "rare"},
    "pink_heart": {"name": "💗 Pink Heart", "stars": 100, "emoji": "💗", "rarity": "rare"},
    
    # Common - Базовые подарки
    "rose": {"name": "🌹 Rose", "stars": 80, "emoji": "🌹", "rarity": "common"},
    "sunflower": {"name": "🌻 Sunflower", "stars": 60, "emoji": "🌻", "rarity": "common"},
    "tulip": {"name": "🌷 Tulip", "stars": 50, "emoji": "🌷", "rarity": "common"},
    "daisy": {"name": "🌼 Daisy", "stars": 40, "emoji": "🌼", "rarity": "common"},
    "star": {"name": "⭐ Star", "stars": 25, "emoji": "⭐", "rarity": "common"},
    "candy": {"name": "🍬 Candy", "stars": 15, "emoji": "🍬", "rarity": "common"},
    "lollipop": {"name": "🍭 Lollipop", "stars": 10, "emoji": "🍭", "rarity": "common"},
    "cookie": {"name": "🍪 Cookie", "stars": 5, "emoji": "🍪", "rarity": "common"},
    "kiss": {"name": "💋 Kiss", "stars": 1, "emoji": "💋", "rarity": "common"}
}

# Цвета редкости
RARITY_COLORS = {
    "common": "#9CA3AF",      # Gray
    "rare": "#22C55E",        # Green  
    "epic": "#3B82F6",        # Blue
    "legendary": "#A855F7",   # Purple
    "mythic": "#F97316",      # Orange
    "ultra_rare": "#EF4444"   # Red
}

RARITY_GRADIENTS = {
    "common": "linear-gradient(135deg, #9CA3AF 0%, #6B7280 100%)",
    "rare": "linear-gradient(135deg, #22C55E 0%, #16A34A 100%)",
    "epic": "linear-gradient(135deg, #3B82F6 0%, #2563EB 100%)",
    "legendary": "linear-gradient(135deg, #A855F7 0%, #9333EA 100%)",
    "mythic": "linear-gradient(135deg, #F97316 0%, #EA580C 100%)",
    "ultra_rare": "linear-gradient(135deg, #EF4444 0%, #DC2626 100%)"
}

def get_user_data(user_id):
    user_id = str(user_id)
    if user_id not in users:
        users[user_id] = {
            "balance": 0,
            "gifts_sent": 0,
            "gifts_received": 0,
            "total_spent": 0,
            "inventory": {},
            "referrals": [],
            "level": 1,
            "experience": 0,
            "daily_streak": 0,
            "last_daily": None,
            "achievements": [],
            "username": None,
            "first_name": "User",
            "join_date": datetime.now().isoformat(),
            "total_value": 0
        }
    return users[user_id]

def send_message(chat_id, text, reply_markup=None, parse_mode="HTML"):
    try:
        url = f"{API_URL}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        
        response = requests.post(url, data=data, timeout=10)
        return response.json()
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        return None

def main_menu_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🚀 Play", "web_app": {"url": f"{WEBHOOK_URL}/webapp"}}],
            [{"text": "👥 Рефералы", "callback_data": "referrals"}],
            [{"text": "ℹ️ Помощь", "callback_data": "help"}]
        ]
    }

def handle_start(chat_id, user_name, username=None, referrer_id=None):
    user_data = get_user_data(chat_id)
    user_data["first_name"] = user_name
    user_data["username"] = username
    
    # Реферальная система
    if referrer_id and str(referrer_id) != str(chat_id):
        referrer_data = get_user_data(referrer_id)
        if str(chat_id) not in referrer_data['referrals']:
            referrer_data['referrals'].append(str(chat_id))
            referrer_data['experience'] += 100
            user_data['experience'] += 50
            
            send_message(referrer_id, 
                f"🎉 <b>Новый реферал!</b>\n\n"
                f"👤 {user_name} присоединился\n"
                f"🎁 +100 XP")

    # Получение подарка
    if referrer_id and referrer_id.startswith('gift_'):
        gift_code = referrer_id[5:]
        handle_receive_gift(chat_id, user_name, username, gift_code)
        return

    text = f"""🎁 <b>Добро пожаловать в GiftUp!</b>

👋 Привет, <b>{user_name}</b>!

🎮 <b>GiftUp</b> - отправляйте подарки друзьям в Telegram!

✨ <b>Возможности:</b>
• 🎁 Отправка подарков любому пользователю
• 🎒 Коллекционирование редких предметов  
• 🏆 Соревнование в рейтингах
• 💫 Система уровней и достижений

🚀 Нажмите <b>"Play"</b> чтобы начать!"""

    send_message(chat_id, text, main_menu_keyboard())

def handle_receive_gift(chat_id, user_name, username, gift_code):
    """Получение подарка по коду"""
    if gift_code not in active_gifts:
        send_message(chat_id, 
            "❌ <b>Подарок недоступен</b>\n\n"
            "Возможные причины:\n"
            "• Подарок уже получен\n"
            "• Ссылка устарела\n"
            "• Неверная ссылка",
            main_menu_keyboard())
        return
    
    gift_info = active_gifts[gift_code]
    sender_id = gift_info["sender_id"]
    gift_id = gift_info["gift_id"]
    
    if str(chat_id) == str(sender_id):
        send_message(chat_id, "❌ <b>Нельзя получить свой подарок!</b>", main_menu_keyboard())
        return
    
    # Проверяем время (24 часа)
    if time.time() - gift_info["created_at"] > 24 * 3600:
        del active_gifts[gift_code]
        send_message(chat_id, "⏰ <b>Срок действия подарка истек!</b>", main_menu_keyboard())
        return
    
    gift = TELEGRAM_GIFTS[gift_id]
    
    # Обновляем данные
    sender_data = get_user_data(sender_id)
    receiver_data = get_user_data(chat_id)
    receiver_data["first_name"] = user_name
    receiver_data["username"] = username
    
    sender_data["gifts_sent"] += 1
    sender_data["total_spent"] += gift["stars"]
    sender_data["experience"] += gift["stars"] // 10
    
    if gift_id not in receiver_data["inventory"]:
        receiver_data["inventory"][gift_id] = 0
    receiver_data["inventory"][gift_id] += 1
    receiver_data["gifts_received"] += 1
    receiver_data["experience"] += gift["stars"] // 5
    receiver_data["total_value"] += gift["stars"]
    
    del active_gifts[gift_code]
    
    # Уведомления
    text = f"""🎉 <b>Подарок получен!</b>

{gift['emoji']} <b>{gift['name']}</b>
⭐ <b>Стоимость:</b> {gift['stars']} звезд
👤 <b>От:</b> {sender_data['first_name']}

🎒 Добавлено в инвентарь!"""

    send_message(chat_id, text, main_menu_keyboard())
    
    send_message(sender_id, 
        f"✅ <b>Подарок доставлен!</b>\n\n"
        f"{gift['emoji']} {gift['name']}\n"
        f"👤 {user_name}")

@app.route("/")
def home():
    return """
    <h1>🎁 GiftUp Clone</h1>
    <p>Telegram Gift Bot</p>
    """

@app.route("/webapp")
def webapp():
    return render_template_string('''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GiftUp</title>
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
            color: white;
            min-height: 100vh;
            padding: 0;
            overflow-x: hidden;
        }
        
        .container {
            max-width: 100%;
            margin: 0 auto;
            padding: 20px;
            min-height: 100vh;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px 0;
        }
        
        .header h1 {
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #FFD700, #FFA500);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .stats-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .nav-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .nav-item {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            border: none;
            border-radius: 15px;
            padding: 20px;
            color: white;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
            text-decoration: none;
        }
        
        .nav-item:hover {
            background: rgba(255, 255, 255, 0.25);
            transform: translateY(-2px);
        }
        
        .nav-item .icon {
            font-size: 24px;
        }
        
        .page {
            display: none;
        }
        
        .page.active {
            display: block;
        }
        
        .gift-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 15px;
            margin-top: 20px;
        }
        
        .gift-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .gift-card:hover {
            transform: translateY(-2px);
            background: rgba(255, 255, 255, 0.2);
        }
        
        .gift-emoji {
            font-size: 32px;
            min-width: 50px;
        }
        
        .gift-info {
            flex: 1;
        }
        
        .gift-name {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .gift-price {
            font-size: 14px;
            opacity: 0.8;
        }
        
        .rarity-badge {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
            margin-top: 5px;
            display: inline-block;
        }
        
        .btn-primary {
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            border: none;
            border-radius: 12px;
            color: white;
            font-size: 16px;
            font-weight: 600;
            padding: 15px 30px;
            cursor: pointer;
            transition: all 0.3s ease;
            width: 100%;
            margin-top: 20px;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(255, 107, 107, 0.3);
        }
        
        .btn-secondary {
            background: rgba(255, 255, 255, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 12px;
            color: white;
            font-size: 14px;
            padding: 10px 20px;
            cursor: pointer;
            transition: all 0.3s ease;
            margin: 5px;
        }
        
        .inventory-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        
        .inventory-item {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 15px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .inventory-emoji {
            font-size: 40px;
            margin-bottom: 10px;
        }
        
        .inventory-count {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 20px;
            padding: 2px 8px;
            font-size: 12px;
            margin-top: 5px;
        }
        
        .back-btn {
            position: fixed;
            top: 20px;
            left: 20px;
            background: rgba(0, 0, 0, 0.3);
            border: none;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            color: white;
            font-size: 18px;
            cursor: pointer;
            z-index: 1000;
        }
        
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 2000;
            padding: 20px;
        }
        
        .modal-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 20px;
            padding: 30px;
            max-width: 400px;
            margin: 50px auto;
            text-align: center;
            position: relative;
        }
        
        .modal-close {
            position: absolute;
            top: 15px;
            right: 20px;
            background: none;
            border: none;
            color: white;
            font-size: 24px;
            cursor: pointer;
        }
        
        .leaderboard-item {
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 15px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            margin-bottom: 10px;
        }
        
        .rank {
            font-size: 20px;
            font-weight: bold;
            min-width: 30px;
        }
        
        .user-info {
            flex: 1;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            font-size: 18px;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .loading {
            animation: pulse 2s infinite;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Главная страница -->
        <div id="home" class="page active">
            <div class="header">
                <h1>🎁 GiftUp</h1>
                <p>Отправляйте подарки друзьям!</p>
            </div>
            
            <div class="stats-card">
                <h3>👤 <span id="userName">Пользователь</span></h3>
                <p>🎒 Подарков в инвентаре: <span id="inventoryCount">0</span></p>
                <p>🎁 Отправлено: <span id="giftsSent">0</span></p>
                <p>📦 Получено: <span id="giftsReceived">0</span></p>
                <p>💫 Уровень: <span id="userLevel">1</span></p>
            </div>
            
            <div class="nav-grid">
                <button class="nav-item" onclick="showPage('send')">
                    <div class="icon">🎁</div>
                    <div>Отправить</div>
                </button>
                <button class="nav-item" onclick="showPage('inventory')">
                    <div class="icon">🎒</div>
                    <div>Инвентарь</div>
                </button>
                <button class="nav-item" onclick="showPage('shop')">
                    <div class="icon">🏪</div>
                    <div>Магазин</div>
                </button>
                <button class="nav-item" onclick="showPage('leaderboard')">
                    <div class="icon">🏆</div>
                    <div>Рейтинг</div>
                </button>
            </div>
        </div>
        
        <!-- Отправка подарков -->
        <div id="send" class="page">
            <button class="back-btn" onclick="showPage('home')">←</button>
            <div class="header">
                <h2>🎁 Отправить подарок</h2>
                <p>Выберите подарок для отправки</p>
            </div>
            
            <div class="btn-secondary" onclick="filterGifts('all')" style="background: rgba(255,255,255,0.3);">Все</div>
            <div class="btn-secondary" onclick="filterGifts('collectible')">🏆 Коллекционные</div>
            <div class="btn-secondary" onclick="filterGifts('seasonal')">🎄 Сезонные</div>
            <div class="btn-secondary" onclick="filterGifts('hearts')">💖 Сердечки</div>
            <div class="btn-secondary" onclick="filterGifts('flowers')">🌸 Цветы</div>
            
            <div class="gift-grid" id="sendGiftGrid">
                <!-- Подарки загружаются через JS -->
            </div>
        </div>
        
        <!-- Инвентарь -->
        <div id="inventory" class="page">
            <button class="back-btn" onclick="showPage('home')">←</button>
            <div class="header">
                <h2>🎒 Мой инвентарь</h2>
                <p id="inventoryValue">Общая стоимость: 0 ⭐</p>
            </div>
            
            <div class="inventory-grid" id="inventoryGrid">
                <!-- Инвентарь загружается через JS -->
            </div>
        </div>
        
        <!-- Магазин -->
        <div id="shop" class="page">
            <button class="back-btn" onclick="showPage('home')">←</button>
            <div class="header">
                <h2>🏪 Магазин подарков</h2>
                <p>Все доступные предметы</p>
            </div>
            
            <div class="gift-grid" id="shopGrid">
                <!-- Магазин загружается через JS -->
            </div>
        </div>
        
        <!-- Рейтинг -->
        <div id="leaderboard" class="page">
            <button class="back-btn" onclick="showPage('home')">←</button>
            <div class="header">
                <h2>🏆 Рейтинг игроков</h2>
                <p>Топ отправителей подарков</p>
            </div>
            
            <div id="leaderboardList">
                <div class="loading">Загрузка рейтинга...</div>
            </div>
        </div>
    </div>
    
    <!-- Модальное окно подарка -->
    <div id="giftModal" class="modal">
        <div class="modal-content">
            <button class="modal-close" onclick="closeGiftModal()">×</button>
            <div id="giftModalContent"></div>
        </div>
    </div>
    
    <script>
        // Telegram WebApp
        const tg = window.Telegram?.WebApp;
        if (tg) {
            tg.ready();
            tg.expand();
        }
        
        // Данные пользователя
        let userData = {
            id: tg?.initDataUnsafe?.user?.id || 'demo',
            first_name: tg?.initDataUnsafe?.user?.first_name || 'Demo User',
            username: tg?.initDataUnsafe?.user?.username || 'demo',
            inventory: {},
            gifts_sent: 0,
            gifts_received: 0,
            level: 1,
            total_value: 0
        };
        
        // Официальные подарки Telegram
        const gifts = {
            "delicious_cake": {"name": "🎂 Delicious Cake", "stars": 2500, "emoji": "🎂", "rarity": "ultra_rare", "collectible": true},
            "green_star": {"name": "💚 Green Star", "stars": 2000, "emoji": "💚", "rarity": "ultra_rare", "collectible": true},
            "santa_hat": {"name": "🎅 Santa Hat", "stars": 1500, "emoji": "🎅", "rarity": "mythic", "seasonal": "winter", "collectible": true},
            "spiced_wine": {"name": "🍷 Spiced Wine", "stars": 1200, "emoji": "🍷", "rarity": "mythic", "seasonal": "winter", "collectible": true},
            "jelly_bunny": {"name": "🐰 Jelly Bunny", "stars": 1000, "emoji": "🐰", "rarity": "mythic", "seasonal": "easter", "collectible": true},
            "ghost": {"name": "👻 Ghost", "stars": 900, "emoji": "👻", "rarity": "mythic", "seasonal": "halloween", "collectible": true},
            "christmas_tree": {"name": "🎄 Christmas Tree", "stars": 800, "emoji": "🎄", "rarity": "legendary", "seasonal": "winter"},
            "jack_o_lantern": {"name": "🎃 Jack-o'-lantern", "stars": 750, "emoji": "🎃", "rarity": "legendary", "seasonal": "halloween"},
            "love_letter": {"name": "💌 Love Letter", "stars": 700, "emoji": "💌", "rarity": "legendary", "seasonal": "valentine"},
            "birthday_cake": {"name": "🧁 Birthday Cake", "stars": 650, "emoji": "🧁", "rarity": "legendary"},
            "fireworks": {"name": "🎆 Fireworks", "stars": 600, "emoji": "🎆", "rarity": "legendary"},
            "golden_star": {"name": "⭐ Golden Star", "stars": 500, "emoji": "⭐", "rarity": "epic"},
            "party_hat": {"name": "🎉 Party Hat", "stars": 450, "emoji": "🎉", "rarity": "epic"},
            "champagne": {"name": "🥂 Champagne", "stars": 400, "emoji": "🥂", "rarity": "epic"},
            "gift_box": {"name": "🎁 Gift Box", "stars": 350, "emoji": "🎁", "rarity": "epic"},
            "chocolate": {"name": "🍫 Chocolate", "stars": 300, "emoji": "🍫", "rarity": "epic"},
            "balloon": {"name": "🎈 Balloon", "stars": 250, "emoji": "🎈", "rarity": "epic"},
            "red_heart": {"name": "❤️ Red Heart", "stars": 200, "emoji": "❤️", "rarity": "rare"},
            "blue_heart": {"name": "💙 Blue Heart", "stars": 180, "emoji": "💙", "rarity": "rare"},
            "purple_heart": {"name": "💜 Purple Heart", "stars": 160, "emoji": "💜", "rarity": "rare"},
            "yellow_heart": {"name": "💛 Yellow Heart", "stars": 140, "emoji": "💛", "rarity": "rare"},
            "orange_heart": {"name": "🧡 Orange Heart", "stars": 120, "emoji": "🧡", "rarity": "rare"},
            "pink_heart": {"name": "💗 Pink Heart", "stars": 100, "emoji": "💗", "rarity": "rare"},
            "rose": {"name": "🌹 Rose", "stars": 80, "emoji": "🌹", "rarity": "common"},
            "sunflower": {"name": "🌻 Sunflower", "stars": 60, "emoji": "🌻", "rarity": "common"},
            "tulip": {"name": "🌷 Tulip", "stars": 50, "emoji": "🌷", "rarity": "common"},
            "daisy": {"name": "🌼 Daisy", "stars": 40, "emoji": "🌼", "rarity": "common"},
            "star": {"name": "⭐ Star", "stars": 25, "emoji": "⭐", "rarity": "common"},
            "candy": {"name": "🍬 Candy", "stars": 15, "emoji": "🍬", "rarity": "common"},
            "lollipop": {"name": "🍭 Lollipop", "stars": 10, "emoji": "🍭", "rarity": "common"},
            "cookie": {"name": "🍪 Cookie", "stars": 5, "emoji": "🍪", "rarity": "common"},
            "kiss": {"name": "💋 Kiss", "stars": 1, "emoji": "💋", "rarity": "common"}
        };
        
        const rarityColors = {
            "common": "#9CA3AF",
            "rare": "#22C55E",
            "epic": "#3B82F6",
            "legendary": "#A855F7",
            "mythic": "#F97316",
            "ultra_rare": "#EF4444"
        };
        
        const rarityNames = {
            "common": "Обычный",
            "rare": "Редкий",
            "epic": "Эпический", 
            "legendary": "Легендарный",
            "mythic": "Мифический",
            "ultra_rare": "Ультра редкий"
        };
        
        // Инициализация
        function init() {
            loadUserData();
            updateUI();
            loadGifts();
        }
        
        function loadUserData() {
            // Загрузка данных пользователя с сервера
            fetch('/api/user/' + userData.id)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        userData = {...userData, ...data.user};
                        updateUI();
                        loadInventory();
                    }
                })
                .catch(error => {
                    console.log('Demo mode - using local data');
                    // Демо данные для тестирования
                    userData.inventory = {
                        "jelly_bunny": 1,
                        "santa_hat": 1, 
                        "chocolate": 2,
                        "red_heart": 3,
                        "rose": 5,
                        "cookie": 10
                    };
                    userData.gifts_sent = 15;
                    userData.gifts_received = 23;
                    userData.level = 5;
                    updateUI();
                    loadInventory();
                });
        }
        
        function updateUI() {
            document.getElementById('userName').textContent = userData.first_name;
            document.getElementById('inventoryCount').textContent = Object.keys(userData.inventory).length;
            document.getElementById('giftsSent').textContent = userData.gifts_sent;
            document.getElementById('giftsReceived').textContent = userData.gifts_received;
            document.getElementById('userLevel').textContent = userData.level;
            
            // Подсчет общей стоимости инвентаря
            let totalValue = 0;
            for (let giftId in userData.inventory) {
                if (gifts[giftId]) {
                    totalValue += gifts[giftId].stars * userData.inventory[giftId];
                }
            }
            userData.total_value = totalValue;
            
            const valueElement = document.getElementById('inventoryValue');
            if (valueElement) {
                valueElement.textContent = `Общая стоимость: ${totalValue} ⭐`;
            }
        }
        
        function showPage(pageId) {
            // Скрыть все страницы
            document.querySelectorAll('.page').forEach(page => {
                page.classList.remove('active');
            });
            
            // Показать нужную страницу
            document.getElementById(pageId).classList.add('active');
            
            // Загрузить данные страницы
            if (pageId === 'inventory') {
                loadInventory();
            } else if (pageId === 'send') {
                loadGifts('send');
            } else if (pageId === 'shop') {
                loadGifts('shop');
            } else if (pageId === 'leaderboard') {
                loadLeaderboard();
            }
        }
        
        function loadGifts(mode = 'send', filter = 'all') {
            const containerId = mode === 'send' ? 'sendGiftGrid' : 'shopGrid';
            const container = document.getElementById(containerId);
            container.innerHTML = '';
            
            // Сортировка подарков по стоимости
            const sortedGifts = Object.entries(gifts).sort((a, b) => b[1].stars - a[1].stars);
            
            for (let [giftId, gift] of sortedGifts) {
                // Фильтрация по категориям
                if (filter !== 'all') {
                    if (filter === 'collectible' && !gift.collectible) continue;
                    if (filter === 'seasonal' && !gift.seasonal) continue;
                    if (filter === 'hearts' && !giftId.includes('heart')) continue;
                    if (filter === 'flowers' && !['rose', 'sunflower', 'tulip', 'daisy'].includes(giftId)) continue;
                }
                
                const giftCard = document.createElement('div');
                giftCard.className = 'gift-card';
                giftCard.onclick = () => showGiftModal(giftId, mode);
                
                const rarityColor = rarityColors[gift.rarity];
                const rarityName = rarityNames[gift.rarity];
                
                // Специальные метки
                let badges = '';
                if (gift.collectible) badges += '<span style="background: #FFD700; color: black; padding: 2px 6px; border-radius: 8px; font-size: 10px; margin-left: 5px;">NFT</span>';
                if (gift.seasonal) badges += '<span style="background: #FF6B6B; color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px; margin-left: 5px;">СЕЗОН</span>';
                
                giftCard.innerHTML = `
                    <div class="gift-emoji">${gift.emoji}</div>
                    <div class="gift-info">
                        <div class="gift-name">${gift.name} ${badges}</div>
                        <div class="gift-price">⭐ ${gift.stars} звезд</div>
                        <span class="rarity-badge" style="background: ${rarityColor}; color: white;">
                            ${rarityName}
                        </span>
                    </div>
                `;
                
                container.appendChild(giftCard);
            }
        }
        
        function loadInventory() {
            const container = document.getElementById('inventoryGrid');
            container.innerHTML = '';
            
            if (Object.keys(userData.inventory).length === 0) {
                container.innerHTML = `
                    <div style="grid-column: 1/-1; text-align: center; padding: 40px;">
                        <div style="font-size: 64px; margin-bottom: 20px;">📦</div>
                        <h3>Инвентарь пуст</h3>
                        <p>Получите первый подарок от друзей!</p>
                    </div>
                `;
                return;
            }
            
            // Сортировка по редкости и стоимости
            const sortedInventory = Object.entries(userData.inventory)
                .map(([giftId, count]) => [giftId, gifts[giftId], count])
                .filter(([,gift,]) => gift)
                .sort((a, b) => {
                    const rarityOrder = {"ultra_rare": 6, "mythic": 5, "legendary": 4, "epic": 3, "rare": 2, "common": 1};
                    return rarityOrder[b[1].rarity] - rarityOrder[a[1].rarity] || b[1].stars - a[1].stars;
                });
            
            for (let [giftId, gift, count] of sortedInventory) {
                const inventoryItem = document.createElement('div');
                inventoryItem.className = 'inventory-item';
                inventoryItem.onclick = () => showGiftModal(giftId, 'inventory');
                
                const rarityColor = rarityColors[gift.rarity];
                
                inventoryItem.innerHTML = `
                    <div class="inventory-emoji">${gift.emoji}</div>
                    <div style="font-size: 14px; font-weight: bold;">${gift.name}</div>
                    <div style="font-size: 12px; opacity: 0.8;">⭐ ${gift.stars}</div>
                    <div class="inventory-count">×${count}</div>
                `;
                
                inventoryItem.style.border = `2px solid ${rarityColor}`;
                container.appendChild(inventoryItem);
            }
        }
        
        function loadLeaderboard() {
            const container = document.getElementById('leaderboardList');
            container.innerHTML = '<div class="loading">Загрузка рейтинга...</div>';
            
            fetch('/api/leaderboard')
                .then(response => response.json())
                .then(data => {
                    container.innerHTML = '';
                    
                    if (data.success && data.leaderboard.length > 0) {
                        data.leaderboard.forEach((user, index) => {
                            const item = document.createElement('div');
                            item.className = 'leaderboard-item';
                            
                            let medal = '';
                            if (index === 0) medal = '🥇';
                            else if (index === 1) medal = '🥈';
                            else if (index === 2) medal = '🥉';
                            else medal = `${index + 1}.`;
                            
                            const isCurrentUser = user.id === userData.id;
                            if (isCurrentUser) {
                                item.style.background = 'rgba(255, 215, 0, 0.2)';
                                item.style.border = '2px solid #FFD700';
                            }
                            
                            item.innerHTML = `
                                <div class="rank">${medal}</div>
                                <div class="user-info">
                                    <div style="font-weight: bold; ${isCurrentUser ? 'color: #FFD700;' : ''}">${user.first_name}</div>
                                    <div style="font-size: 14px; opacity: 0.8;">🎁 ${user.gifts_sent} подарков</div>
                                </div>
                                <div style="font-size: 18px;">💫 ${user.level}</div>
                            `;
                            
                            container.appendChild(item);
                        });
                    } else {
                        container.innerHTML = `
                            <div style="text-align: center; padding: 40px;">
                                <div style="font-size: 64px; margin-bottom: 20px;">🏆</div>
                                <h3>Рейтинг пуст</h3>
                                <p>Станьте первым!</p>
                            </div>
                        `;
                    }
                })
                .catch(error => {
                    // Демо рейтинг
                    container.innerHTML = '';
                    const demoLeaderboard = [
                        {id: 'user1', first_name: 'Алексей', gifts_sent: 127, level: 15},
                        {id: 'user2', first_name: 'Мария', gifts_sent: 89, level: 12},
                        {id: 'user3', first_name: 'Дмитрий', gifts_sent: 76, level: 11},
                        {id: userData.id, first_name: userData.first_name, gifts_sent: userData.gifts_sent, level: userData.level},
                        {id: 'user4', first_name: 'Анна', gifts_sent: 45, level: 8},
                    ];
                    
                    demoLeaderboard.sort((a, b) => b.gifts_sent - a.gifts_sent);
                    
                    demoLeaderboard.forEach((user, index) => {
                        const item = document.createElement('div');
                        item.className = 'leaderboard-item';
                        
                        let medal = '';
                        if (index === 0) medal = '🥇';
                        else if (index === 1) medal = '🥈';
                        else if (index === 2) medal = '🥉';
                        else medal = `${index + 1}.`;
                        
                        const isCurrentUser = user.id === userData.id;
                        if (isCurrentUser) {
                            item.style.background = 'rgba(255, 215, 0, 0.2)';
                            item.style.border = '2px solid #FFD700';
                        }
                        
                        item.innerHTML = `
                            <div class="rank">${medal}</div>
                            <div class="user-info">
                                <div style="font-weight: bold; ${isCurrentUser ? 'color: #FFD700;' : ''}">${user.first_name}</div>
                                <div style="font-size: 14px; opacity: 0.8;">🎁 ${user.gifts_sent} подарков</div>
                            </div>
                            <div style="font-size: 18px;">💫 ${user.level}</div>
                        `;
                        
                        container.appendChild(item);
                    });
                });
        }
        
        function filterGifts(category) {
            // Обновить активную кнопку фильтра
            document.querySelectorAll('.btn-secondary').forEach(btn => {
                btn.style.background = 'rgba(255, 255, 255, 0.2)';
            });
            event.target.style.background = 'rgba(255, 255, 255, 0.3)';
            
            loadGifts('send', category);
        }
        
        function showGiftModal(giftId, mode) {
            const gift = gifts[giftId];
            if (!gift) return;
            
            const modal = document.getElementById('giftModal');
            const content = document.getElementById('giftModalContent');
            
            const rarityColor = rarityColors[gift.rarity];
            const rarityName = rarityNames[gift.rarity];
            
            let actionButton = '';
            if (mode === 'send' || mode === 'shop') {
                actionButton = `
                    <button class="btn-primary" onclick="sendGift('${giftId}')">
                        🎁 Отправить подарок (${gift.stars} ⭐)
                    </button>
                `;
            } else if (mode === 'inventory') {
                const count = userData.inventory[giftId] || 0;
                actionButton = `
                    <p style="margin: 20px 0; font-size: 16px;">📦 У вас: ${count} шт.</p>
                    <button class="btn-primary" onclick="sendGift('${giftId}')">
                        🎁 Отправить этот подарок
                    </button>
                `;
            }
            
            content.innerHTML = `
                <div style="font-size: 80px; margin-bottom: 20px;">${gift.emoji}</div>
                <h2 style="margin-bottom: 10px;">${gift.name}</h2>
                <div style="background: ${rarityColor}; color: white; padding: 8px 16px; border-radius: 20px; display: inline-block; margin-bottom: 20px;">
                    ${rarityName}
                </div>
                <p style="font-size: 18px; margin: 20px 0;">⭐ ${gift.stars} звезд</p>
                <p style="opacity: 0.8; margin-bottom: 30px;">Категория: ${gift.category}</p>
                ${actionButton}
            `;
            
            modal.style.display = 'block';
        }
        
        function closeGiftModal() {
            document.getElementById('giftModal').style.display = 'none';
        }
        
        function sendGift(giftId) {
            const gift = gifts[giftId];
            
            // Отправка подарка на сервер
            fetch('/api/send-gift', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: userData.id,
                    gift_id: giftId
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Показываем ссылку для отправки
                    const content = document.getElementById('giftModalContent');
                    content.innerHTML = `
                        <div style="font-size: 80px; margin-bottom: 20px;">🎁</div>
                        <h2>Подарок готов к отправке!</h2>
                        <p style="margin: 20px 0;">${gift.emoji} ${gift.name}</p>
                        
                        <div style="background: rgba(255,255,255,0.1); border-radius: 12px; padding: 15px; margin: 20px 0;">
                            <p style="margin-bottom: 10px; font-size: 14px;">Ссылка для отправки:</p>
                            <input type="text" value="${data.gift_link}" readonly 
                                   style="width: 100%; padding: 10px; border: none; border-radius: 8px; background: rgba(0,0,0,0.2); color: white; text-align: center;"
                                   onclick="this.select()">
                        </div>
                        
                        <p style="font-size: 14px; opacity: 0.8; margin: 20px 0;">
                            📋 Скопируйте ссылку и отправьте другу<br>
                            ⏰ Ссылка действует 24 часа
                        </p>
                        
                        <button class="btn-primary" onclick="copyGiftLink('${data.gift_link}')">
                            📋 Скопировать ссылку
                        </button>
                    `;
                } else {
                    alert('Ошибка: ' + data.message);
                }
            })
            .catch(error => {
                // Демо режим - создаем локальную ссылку
                const giftCode = Math.random().toString(36).substr(2, 8);
                const giftLink = `https://t.me/YOUR_BOT_USERNAME?start=gift_${giftCode}`;
                
                const content = document.getElementById('giftModalContent');
                content.innerHTML = `
                    <div style="font-size: 80px; margin-bottom: 20px;">🎁</div>
                    <h2>Подарок готов к отправке!</h2>
                    <p style="margin: 20px 0;">${gift.emoji} ${gift.name}</p>
                    
                    <div style="background: rgba(255,255,255,0.1); border-radius: 12px; padding: 15px; margin: 20px 0;">
                        <p style="margin-bottom: 10px; font-size: 14px;">Ссылка для отправки:</p>
                        <input type="text" value="${giftLink}" readonly 
                               style="width: 100%; padding: 10px; border: none; border-radius: 8px; background: rgba(0,0,0,0.2); color: white; text-align: center; font-size: 12px;"
                               onclick="this.select()">
                    </div>
                    
                    <p style="font-size: 14px; opacity: 0.8; margin: 20px 0;">
                        📋 Скопируйте ссылку и отправьте другу<br>
                        ⏰ Ссылка действует 24 часа
                    </p>
                    
                    <button class="btn-primary" onclick="copyGiftLink('${giftLink}')">
                        📋 Скопировать ссылку
                    </button>
                `;
                
                // Обновляем статистику локально в демо режиме
                userData.gifts_sent++;
                updateUI();
            });
        }
        
        function copyGiftLink(link) {
            navigator.clipboard.writeText(link).then(() => {
                if (tg) {
                    tg.showAlert('Ссылка скопирована! Отправьте её другу.');
                } else {
                    alert('Ссылка скопирована!');
                }
                closeGiftModal();
                showPage('home');
            }).catch(() => {
                // Fallback для старых браузеров
                const textArea = document.createElement('textarea');
                textArea.value = link;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                
                if (tg) {
                    tg.showAlert('Ссылка готова к отправке!');
                } else {
                    alert('Ссылка готова к отправке!');
                }
                closeGiftModal();
                showPage('home');
            });
        }
        
        // Закрытие модального окна при клике вне его
        document.getElementById('giftModal').onclick = function(event) {
            if (event.target === this) {
                closeGiftModal();
            }
        }
        
        // Инициализация при загрузке
        document.addEventListener('DOMContentLoaded', init);
        
        // Telegram WebApp события
        if (tg) {
            tg.onEvent('backButtonClicked', () => {
                const activePageId = document.querySelector('.page.active').id;
                if (activePageId !== 'home') {
                    showPage('home');
                } else {
                    tg.close();
                }
            });
            
            // Показываем кнопку "Назад" когда не на главной странице
            const observer = new MutationObserver(() => {
                const activePageId = document.querySelector('.page.active').id;
                if (activePageId !== 'home') {
                    tg.BackButton.show();
                } else {
                    tg.BackButton.hide();
                }
            });
            
            observer.observe(document.body, {
                subtree: true,
                attributeFilter: ['class']
            });
        }
    </script>
</body>
</html>
    ''')

# API маршруты
@app.route('/api/user/<user_id>')
def get_user(user_id):
    user_data = get_user_data(user_id)
    return jsonify({"success": True, "user": user_data})

@app.route('/api/send-gift', methods=['POST'])
def api_send_gift():
    try:
        data = request.get_json()
        user_id = str(data.get('user_id'))
        gift_id = data.get('gift_id')
        
        if gift_id not in TELEGRAM_GIFTS:
            return jsonify({"success": False, "message": "Подарок не найден"})
        
        # Создаем код подарка
        gift_code = str(uuid.uuid4())[:8]
        
        # Сохраняем в активные подарки
        active_gifts[gift_code] = {
            "sender_id": user_id,
            "gift_id": gift_id,
            "created_at": time.time()
        }
        
        # Создаем ссылку
        bot_username = "your_bot_username"  # Замените на реальное имя бота
        gift_link = f"https://t.me/{bot_username}?start=gift_{gift_code}"
        
        return jsonify({
            "success": True,
            "gift_link": gift_link,
            "gift_code": gift_code
        })
        
    except Exception as e:
        logger.error(f"Send gift API error: {e}")
        return jsonify({"success": False, "message": "Ошибка сервера"})

@app.route('/api/leaderboard')
def get_leaderboard():
    try:
        # Кэширование рейтинга на 5 минут
        current_time = time.time()
        if current_time - leaderboard_cache["last_update"] > 300:  # 5 минут
            sorted_users = sorted(
                [(uid, data) for uid, data in users.items()],
                key=lambda x: x[1]['gifts_sent'],
                reverse=True
            )[:50]  # Топ 50
            
            leaderboard_cache["data"] = [
                {
                    "id": uid,
                    "first_name": data.get('first_name', 'User'),
                    "gifts_sent": data['gifts_sent'],
                    "level": data['level'],
                    "total_value": data.get('total_value', 0)
                }
                for uid, data in sorted_users
            ]
            leaderboard_cache["last_update"] = current_time
        
        return jsonify({
            "success": True,
            "leaderboard": leaderboard_cache["data"]
        })
        
    except Exception as e:
        logger.error(f"Leaderboard API error: {e}")
        return jsonify({"success": False, "message": "Ошибка загрузки рейтинга"})

# Webhook обработчик
@app.route(f"/{TOKEN}", methods=['POST'])
def webhook():
    try:
        update = request.get_json()
        
        if 'message' in update:
            message = update['message']
            chat_id = message['chat']['id']
            text = message.get('text', '')
            user_name = message['from'].get('first_name', 'User')
            username = message['from'].get('username')
            
            if text.startswith('/start'):
                if ' ' in text:
                    param = text.split()[1]
                    if param.startswith('gift_'):
                        gift_code = param[5:]
                        handle_receive_gift(chat_id, user_name, username, gift_code)
                        return jsonify({"ok": True})
                    elif param.startswith('ref_'):
                        referrer_id = param[4:]
                        handle_start(chat_id, user_name, username, referrer_id)
                        return jsonify({"ok": True})
                
                handle_start(chat_id, user_name, username)
                
        elif 'callback_query' in update:
            callback = update['callback_query']
            chat_id = callback['message']['chat']['id']
            data = callback['data']
            user_id = callback['from']['id']
            
            if data == "referrals":
                user_data = get_user_data(user_id)
                bot_username = "your_bot_username"  # Замените на реальное
                ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
                
                text = f"""👥 <b>Реферальная программа</b>

🔗 <b>Ваша ссылка:</b>
`{ref_link}`

📊 <b>Приглашено:</b> {len(user_data['referrals'])}
🎁 <b>Бонус за реферала:</b> 100 XP"""

                keyboard = {
                    "inline_keyboard": [
                        [{"text": "🔙 Назад", "callback_data": "back"}]
                    ]
                }
                
                send_message(chat_id, text, keyboard)
            
            elif data == "help":
                text = """ℹ️ <b>Как пользоваться GiftUp</b>

🎁 <b>Отправка подарков:</b>
1. Нажмите "Play" 
2. Выберите "Отправить"
3. Выберите подарок
4. Скопируйте ссылку
5. Отправьте другу

🎒 <b>Инвентарь:</b>
• Все полученные подарки
• Сортировка по редкости
• Просмотр деталей

🏆 <b>Рейтинг:</b>
• Топ отправителей
• Ваша позиция
• Уровни игроков"""

                keyboard = {
                    "inline_keyboard": [
                        [{"text": "🔙 Назад", "callback_data": "back"}]
                    ]
                }
                
                send_message(chat_id, text, keyboard)
            
            elif data == "back":
                user_data = get_user_data(user_id)
                text = f"""🎁 <b>GiftUp</b>

👋 Привет! Отправляйте подарки друзьям в Telegram.

🚀 Нажмите "Play" чтобы начать!"""
                
                send_message(chat_id, text, main_menu_keyboard())
        
        return jsonify({"ok": True})
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"ok": False})

# Очистка устаревших подарков
def cleanup_expired_gifts():
    while True:
        try:
            current_time = time.time()
            expired_gifts = []
            
            for gift_id, gift_info in active_gifts.items():
                if current_time - gift_info["created_at"] > 24 * 3600:  # 24 часа
                    expired_gifts.append(gift_id)
            
            for gift_id in expired_gifts:
                del active_gifts[gift_id]
                logger.info(f"Removed expired gift: {gift_id}")
            
            time.sleep(1800)  # 30 минут
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            time.sleep(300)

# Установка webhook
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

# Запуск фоновых процессов
cleanup_thread = threading.Thread(target=cleanup_expired_gifts)
cleanup_thread.daemon = True
cleanup_thread.start()

if __name__ == '__main__':
    set_webhook()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
