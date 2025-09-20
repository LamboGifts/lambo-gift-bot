// Запускаем все источники
                    this.mainEngine.start();
                    this.turbulence.start();
                    this.highFreq.start();
                },
                
                createNoiseBuffer: function(duration) {
                    const bufferSize = this.context.sampleRate * duration;
                    const buffer = this.context.createBuffer(1, bufferSize, this.context.sampleRate);
                    const output = buffer.getChannelData(0);
                    
                    // Создаем розовый шум (более реалистичный чем белый)
                    let b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0;
                    for (let i = 0; i < bufferSize; i++) {
                        const white = Math.random() * 2 - 1;
                        b0 = 0.99886 * b0 + white * 0.0555179;
                        b1 = 0.99332 * b1 + white * 0.0750759;
                        b2 = 0.96900 * b2 + white * 0.1538520;
                        b3 = 0.86650 * b3 + white * 0.3104856;
                        b4 = 0.55000 * b4 + white * 0.5329522;
                        b5 = -0.7616 * b5 - white * 0.0168980;
                        const pink = b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362;
                        b6 = white * 0.115926;
                        output[i] = pink * 0.11;
                    }
                    return buffer;
                },
                
                updatePitch: function(multiplier) {
                    if (!this.isPlaying) return;
                    
                    // Увеличиваем частоты и интенсивность с ростом множителя
                    const intensityFactor = 1 + (multiplier - 1) * 0.3;
                    const frequencyFactor = 1 + (multiplier - 1) * 0.2;
                    
                    if (this.mainEngine) {
                        const newFreq = 80 * frequencyFactor;
                        this.mainEngine.frequency.setValueAtTime(newFreq, this.context.currentTime);
                    }
                    
                    if (this.highFreq) {
                        const newHighFreq = 1200 * frequencyFactor;
                        this.highFreq.frequency.setValueAtTime(newHighFreq, this.context.currentTime);
                    }
                    
                    // Обновляем громкость
                    this.gainNodes.forEach((gainNode, index) => {
                        const baseGains = [0.15, 0.08, 0.05];
                        const newGain = baseGains[index] * intensityFactor;
                        gainNode.gain.setValueAtTime(Math.min(newGain, 0.25), this.context.currentTime);
                    });
                    
                    // Обновляем фильтры для более реалистичного звука
                    if (this.filterNodes[0]) { // main filter
                        const newCutoff = 400 + (multiplier - 1) * 100;
                        this.filterNodes[0].frequency.setValueAtTime(newCutoff, this.context.currentTime);
                    }
                    
                    if (this.filterNodes[1]) { // turbulence filter
                        const newBandpass = 800 + (multiplier - 1) * 200;
                        this.filterNodes[1].frequency.setValueAtTime(newBandpass, this.context.currentTime);
                    }
                },
                
                stop: function() {
                    if (!this.isPlaying) return;
                    this.isPlaying = false;
                    
                    // Плавное затухание
                    this.gainNodes.forEach(gainNode => {
                        gainNode.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + 0.5);
                    });
                    
                    // Останавливаем через 0.5 секунд
                    setTimeout(() => {
                        if (this.mainEngine) {
                            this.mainEngine.stop();
                            this.mainEngine = null;
                        }
                        if (this.turbulence) {
                            this.turbulence.stop();
                            this.turbulence = null;
                        }
                        if (this.highFreq) {
                            this.highFreq.stop();
                            this.highFreq = null;
                        }
                        this.gainNodes = [];
                        this.filterNodes = [];
                    }, 500);
                }
            };
            
            // Более реалистичный звук взрыва с несколькими фазами
            crashSound = {
                context: audioContext,
                play: function() {
                    // Фаза 1: Начальный взрыв
                    this.playInitialBang();
                    
                    // Фаза 2: Эхо и реверберация (через 200мс)
                    setTimeout(() => this.playEcho(), 200);
                    
                    // Фаза 3: Затухающие обломки (через 600мс)
                    setTimeout(() => this.playDebris(), 600);
                },
                
                playInitialBang: function() {
                    // Создаем импульсивный взрыв
                    const noiseBuffer = this.createExplosionBuffer(0.3);
                    const noiseSource = this.context.createBufferSource();
                    const noiseGain = this.context.createGain();
                    const noiseFilter = this.context.createBiquadFilter();
                    
                    noiseSource.buffer = noiseBuffer;
                    noiseFilter.type = "lowpass";
                    noiseFilter.frequency.setValueAtTime(1200, this.context.currentTime);
                    noiseFilter.Q.setValueAtTime(0.7, this.context.currentTime);
                    
                    noiseSource.connect(noiseFilter);
                    noiseFilter.connect(noiseGain);
                    noiseGain.connect(this.context.destination);
                    
                    noiseGain.gain.setValueAtTime(0.6, this.context.currentTime);
                    noiseGain.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + 0.3);
                    noiseFilter.frequency.exponentialRampToValueAtTime(80, this.context.currentTime + 0.25);
                    
                    // Низкочастотный удар
                    const bassOsc = this.context.createOscillator();
                    const bassGain = this.context.createGain();
                    
                    bassOsc.type = "sine";
                    bassOsc.frequency.setValueAtTime(30, this.context.currentTime);
                    bassOsc.frequency.exponentialRampToValueAtTime(5, this.context.currentTime + 0.4);
                    
                    bassOsc.connect(bassGain);
                    bassGain.connect(this.context.destination);
                    
                    bassGain.gain.setValueAtTime(0.8, this.context.currentTime);
                    bassGain.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + 0.4);
                    
                    noiseSource.start();
                    bassOsc.start();
                    
                    noiseSource.stop(this.context.currentTime + 0.3);
                    bassOsc.stop(this.context.currentTime + 0.4);
                },
                
                playEcho: function() {
                    // Эхо взрыва
                    const echoBuffer = this.createExplosionBuffer(0.2);
                    const echoSource = this.context.createBufferSource();
                    const echoGain = this.context.createGain();
                    const echoFilter = this.context.createBiquadFilter();
                    
                    echoSource.buffer = echoBuffer;
                    echoFilter.type = "highpass";
                    echoFilter.frequency.setValueAtTime(200, this.context.currentTime);
                    
                    echoSource.connect(echoFilter);
                    echoFilter.connect(echoGain);
                    echoGain.connect(this.context.destination);
                    
                    echoGain.gain.setValueAtTime(0.3, this.context.currentTime);
                    echoGain.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + 0.2);
                    
                    echoSource.start();
                    echoSource.stop(this.context.currentTime + 0.2);
                },
                
                playDebris: function() {
                    // Звук падающих обломков
                    for (let i = 0; i < 3; i++) {
                        setTimeout(() => {
                            const debris = this.context.createOscillator();
                            const debrisGain = this.context.createGain();
                            const debrisFilter = this.context.createBiquadFilter();
                            
                            debris.type = "sawtooth";
                            debris.frequency.setValueAtTime(150 + Math.random() * 300, this.context.currentTime);
                            debris.frequency.exponentialRampToValueAtTime(50 + Math.random() * 100, this.context.currentTime + 0.5);
                            
                            debrisFilter.type = "bandpass";
                            debrisFilter.frequency.setValueAtTime(400 + Math.random() * 800, this.context.currentTime);
                            debrisFilter.Q.setValueAtTime(2, this.context.currentTime);
                            
                            debris.connect(debrisFilter);
                            debrisFilter.connect(debrisGain);
                            debrisGain.connect(this.context.destination);
                            
                            debrisGain.gain.setValueAtTime(0.1, this.context.currentTime);
                            debrisGain.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + 0.5);
                            
                            debris.start();
                            debris.stop(this.context.currentTime + 0.5);
                        }, i * 150);
                    }
                },
                
                createExplosionBuffer: function(duration) {
                    const bufferSize = this.context.sampleRate * duration;
                    const buffer = this.context.createBuffer(1, bufferSize, this.context.sampleRate);
                    const output = buffer.getChannelData(0);
                    
                    // Создаем шум взрыва с затуханием
                    for (let i = 0; i < bufferSize; i++) {
                        const decay = 1 - (i / bufferSize);
                        const intensity = Math.pow(decay, 0.3);
                        output[i] = (Math.random() * 2 - 1) * intensity;
                    }
                    return buffer;
                }
            };
        }import os
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
    
    for case_id, case_info in CASES.items():
        keyboard["inline_keyboard"].append([{
            "text": f"{case_info['emoji']} {case_info['name']} - {case_info['price']} монет",
            "callback_data": f"open_{case_id}"
        }])
    
    keyboard["inline_keyboard"].append([{"text": "🔙 Назад", "callback_data": "main"}])
    
    text = f"""🎁 <b>Магазин подарков</b>

Выберите кейс для открытия:

💡 <b>Как работает:</b>
• Каждый кейс содержит разные подарки
• Чем дороже подарок, тем меньше шанс его получить
• Подарки оцениваются в звездах ⭐
• Собирайте редкие подарки!

🎯 <b>Типы редкости:</b>
• ⚪ Обычные (1-25 ⭐)
• 🟢 Необычные (26-100 ⭐) 
• 🔵 Редкие (101-500 ⭐)
• 🟣 Эпические (501-1000 ⭐)
• 🟡 Легендарные (1001-2000 ⭐)
• 🔴 Мифические (2000+ ⭐)"""

    edit_message(chat_id, message_id, text, keyboard)

def open_case(chat_id, message_id, case_id):
    user_data = get_user_data(chat_id)
    case = CASES.get(case_id)
    
    if not case:
        return
    
    if user_data['balance'] < case['price']:
        keyboard = {
            "inline_keyboard": [
                [{"text": "💰 Получить бонус", "callback_data": "daily_bonus"}],
                [{"text": "🔙 К кейсам", "callback_data": "gift_shop"}]
            ]
        }
        text = f"""❌ <b>Недостаточно средств!</b>

💰 <b>Баланс:</b> {user_data['balance']} монет
💸 <b>Нужно:</b> {case['price']} монет

{case['emoji']} <b>{
