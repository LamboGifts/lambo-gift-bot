import os
import requests
import json
import random
import time
import threading
from flask import Flask, request, jsonify
import logging
from datetime import datetime

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
        
        for user_id in self.bets:
            if user_id not in self.cashed_out:
                user_data = get_user_data(user_id)
                user_data['total_lost'] += self.bets[user_id]['amount']
                user_data['games_lost'] += 1
    
    def place_bet(self, user_id, amount, auto_cashout=None):
        if self.is_running:
            return False, "Игра уже идет"
        
        user_data = get_user_data(user_id)
        if user_data['balance'] < amount:
            return False, "Недостаточно средств"
        
        user_data['balance'] -= amount
        user_data['total_bet'] += amount
        user_data['games_played'] += 1
        
        self.bets[user_id] = {
            'amount': amount,
            'auto_cashout': auto_cashout
        }
        return True, "Ставка принята"
    
    def cashout(self, user_id):
        if not self.is_running or self.is_crashed:
            return False, "Игра не идет"
        
        if user_id not in self.bets:
            return False, "У вас нет ставки"
        
        if user_id in self.cashed_out:
            return False, "Вы уже вывели"
        
        bet_amount = self.bets[user_id]['amount']
        win_amount = int(bet_amount * self.multiplier)
        
        user_data = get_user_data(user_id)
        user_data['balance'] += win_amount
        user_data['total_won'] += win_amount
        user_data['games_won'] += 1
        
        self.cashed_out[user_id] = self.multiplier
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
            "inventory": {}
        }
    return users[user_id]

# ... остальной код без изменений (handle_*, game_loop и т.д.) ...

@app.route("/webapp")  
def webapp():
    return """<!DOCTYPE html>
<html lang=\"ru\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>GiftBot Crash Game</title>
    <script src=\"https://telegram.org/js/telegram-web-app.js\"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #1a1a2e, #16213e, #0f3460); color: #fff; min-height: 100vh; overflow: hidden; }
        .container { max-width: 400px; margin: 0 auto; padding: 20px; position: relative; }
        .game-header { text-align: center; margin-bottom: 20px; background: rgba(255,255,255,0.1); padding: 20px; border-radius: 20px; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.2); }
        .balance { font-size: 20px; font-weight: bold; color: #ffd700; }
        .crash-display { position: relative; height: 300px; background: linear-gradient(45deg, #1e3c72, #2a5298); border-radius: 20px; margin-bottom: 20px; overflow: hidden; border: 2px solid #ffd700; display: flex; align-items: center; justify-content: center; }
        .multiplier { font-size: 48px; font-weight: bold; color: #00ff00; text-shadow: 0 0 20px #00ff00; transition: all 0.1s ease; }
        .multiplier.crashed { color: #ff0000; text-shadow: 0 0 20px #ff0000; }
        .rocket { position: absolute; bottom: 10px; font-size: 40px; transition: transform 0.2s linear; }
        .explosion { display: none; position: absolute; font-size: 60px; animation: explode 0.6s ease forwards; }
        @keyframes explode { 0% { transform: scale(0.5); opacity: 1; } 50% { transform: scale(2); opacity: 1; } 100% { transform: scale(3); opacity: 0; } }
    </style>
</head>
<body>
    <div class=\"container\">
        <div class=\"game-header\">
            <div class=\"balance\">💰 <span id=\"balance\">1000</span> монет</div>
            <div>🚀 Crash Game</div>
        </div>
        <div class=\"crash-display\">
            <div class=\"rocket\" id=\"rocket\">🚀</div>
            <div class=\"explosion\" id=\"explosion\">💥</div>
            <div class=\"multiplier\" id=\"multiplier\">1.00x</div>
        </div>
        <audio id=\"boomSound\" src=\"https://www.myinstants.com/media/sounds/explosion.mp3\"></audio>
        <audio id=\"rocketSound\" src=\"https://www.myinstants.com/media/sounds/missile.mp3\" loop></audio>
        <div class=\"controls\">
            <input type=\"number\" class=\"bet-input\" id=\"betAmount\" placeholder=\"Ставка\" min=\"1\" value=\"10\">
            <button class=\"btn btn-bet\" id=\"betButton\" onclick=\"placeBet()\">Ставка</button>
            <input type=\"number\" class=\"bet-input\" id=\"autoCashout\" placeholder=\"Авто-вывод\" min=\"1.01\" step=\"0.01\">
            <button class=\"btn btn-cashout\" id=\"cashoutButton\" onclick=\"cashOut()\" disabled>Вывести</button>
        </div>
        <div class=\"game-info\">
            <div>Статус: <span id=\"gameStatus\">Ожидание...</span></div>
            <div>Ваша ставка: <span id=\"currentBet\">-</span></div>
            <div>Потенциальный выигрыш: <span id=\"potentialWin\">-</span></div>
        </div>
    </div>
    <script>
        window.Telegram.WebApp.ready(); window.Telegram.WebApp.expand();
        let gameData = { balance: 1000, currentBet: 0, multiplier: 1.0, isPlaying: false, gameRunning: false };
        const rocket = document.getElementById('rocket');
        const explosion = document.getElementById('explosion');
        const boomSound = document.getElementById('boomSound');
        const rocketSound = document.getElementById('rocketSound');
        function updateDisplay() { document.getElementById('balance').textContent = gameData.balance; document.getElementById('multiplier').textContent = gameData.multiplier.toFixed(2) + 'x'; document.getElementById('currentBet').textContent = gameData.currentBet || '-'; if (gameData.currentBet) { const potential = Math.floor(gameData.currentBet * gameData.multiplier); document.getElementById('potentialWin').textContent = potential + ' монет'; } }
        function updateRocketPosition(multiplier) { const maxHeight = 200; const y = Math.min(multiplier * 20, maxHeight); rocket.style.transform = `translateY(-${y}px)`; }
        function placeBet() { const betAmount = parseInt(document.getElementById('betAmount').value); if (!betAmount || betAmount < 1 || gameData.balance < betAmount || gameData.gameRunning) { return; } gameData.balance -= betAmount; gameData.currentBet = betAmount; gameData.isPlaying = true; document.getElementById('betButton').disabled = true; document.getElementById('cashoutButton').disabled = false; document.getElementById('gameStatus').textContent = 'Ставка принята'; updateDisplay(); }
        function cashOut() { if (!gameData.isPlaying || !gameData.gameRunning) return; const winAmount = Math.floor(gameData.currentBet * gameData.multiplier); gameData.balance += winAmount; gameData.isPlaying = false; document.getElementById('cashoutButton').disabled = true; document.getElementById('gameStatus').textContent = `Выведено: ${winAmount} монет`; updateDisplay(); }
        function simulateGame() { gameData.multiplier = 1.0; gameData.gameRunning = false; document.getElementById('betButton').disabled = false; document.getElementById('cashoutButton').disabled = true; document.getElementById('gameStatus').textContent = 'Прием ставок...'; rocket.style.transform = 'translateY(0)'; setTimeout(() => { gameData.gameRunning = true; document.getElementById('betButton').disabled = true; document.getElementById('gameStatus').textContent = 'Игра началась!'; rocketSound.play(); const crashPoint = Math.random() * 3 + 1.01; const gameInterval = setInterval(() => { gameData.multiplier += 0.01 + (gameData.multiplier * 0.001); updateRocketPosition(gameData.multiplier); if (gameData.multiplier >= crashPoint) { crash(); clearInterval(gameInterval); } updateDisplay(); }, 100); }, 5000); }
        function crash() { gameData.gameRunning = false; const multiplierElement = document.getElementById('multiplier'); multiplierElement.classList.add('crashed'); multiplierElement.textContent = 'КРАШ!'; rocket.style.display = 'none'; explosion.style.display = 'block'; rocketSound.pause(); rocketSound.currentTime = 0; boomSound.play(); if (gameData.isPlaying) { gameData.isPlaying = false; document.getElementById('gameStatus').textContent = 'Краш - проигрыш!'; } setTimeout(() => { multiplierElement.classList.remove('crashed'); explosion.style.display = 'none'; rocket.style.display = 'block'; rocket.style.transform = 'translateY(0)'; gameData.currentBet = 0; gameData.isPlaying = false; updateDisplay(); simulateGame(); }, 3000); }
        updateDisplay(); simulateGame();
    </script>
</body>
</html>"""
