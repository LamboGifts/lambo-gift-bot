import os
import requests
import json
import random
from flask import Flask, request

# Настройки
TOKEN = "7678954168:AAG6755ngOoYcQfIt6viZKMRXRcv6dOd0vY"
API_URL = f"https://api.telegram.org/bot{TOKEN}"
WEBHOOK_URL = "https://lambo-gift-bot.onrender.com"  # ✅ правильный URL

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
    if user_id not in users:
        get_user_data(user_id)
    users[user_id]["balance"] += amount

def send_message(chat_id, text, reply_markup=None):
    url = f"{API_URL}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    requests.post(url, data=data)

def edit_message(chat_id, message_id, text, reply_markup=None):
    url = f"{API_URL}/editMessageText"
    data = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    requests.post(url, data=data)

def answer_callback(callback_query_id):
    url = f"{API_URL}/answerCallbackQuery"
    requests.post(url, data={"callback_query_id": callback_query_id})

def main_menu_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🎮 Открыть WebApp", "web_app": {"url": f"{WEBHOOK_URL}/webapp"}}],
            [{"text": "🎁 Каталог подарков", "callback_data": "catalog"}],
            [{"text": "🎲 Плинко", "callback_data": "plinko"}],
            [{"text": "💳 Баланс", "callback_data": "balance"}],
            [{"text": "📊 Статистика", "callback_data": "stats"}]
        ]
    }

# --- остальной код GiftBot и Plinko из предыдущей версии ---

if __name__ == "__main__":
    webhook_url = f"{WEBHOOK_URL}/{TOKEN}"
    try:
        response = requests.post(f"{API_URL}/setWebhook", data={"url": webhook_url})
        print(f"Установка webhook: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Ошибка при установке webhook: {e}")

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
