import json
import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем токен из переменных окружения
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7678954168:AAG6755ngOoYcQfIt6viZKMRXRcv6dOd0vY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://lambo-gift.onrender.com")

# Файл для хранения данных
DATA_FILE = "data.json"

# Flask приложение
app = Flask(__name__)

def load_data():
    """Загружает данные из JSON файла"""
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    """Сохраняет данные в JSON файл"""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Ошибка сохранения данных: {e}")

def get_user_data(user_id):
    """Получает данные пользователя"""
    data = load_data()
    user_id = str(user_id)
    
    if user_id not in data:
        data[user_id] = {
            "balance": 100,
            "gifts_sent": 0,
            "gifts_received": 0,
            "total_spent": 0
        }
        save_data(data)
    
    return data[user_id]

def update_user_data(user_id, updates):
    """Обновляет данные пользователя"""
    data = load_data()
    user_id = str(user_id)
    
    if user_id not in data:
        get_user_data(user_id)
        data = load_data()
    
    data[user_id].update(updates)
    save_data(data)

# Каталог подарков
GIFTS_CATALOG = {
    "rose": {"name": "🌹 Роза", "price": 10, "emoji": "🌹"},
    "cake": {"name": "🎂 Торт", "price": 25, "emoji": "🎂"},
    "diamond": {"name": "💎 Бриллиант", "price": 50, "emoji": "💎"},
    "crown": {"name": "👑 Корона", "price": 100, "emoji": "👑"},
    "rocket": {"name": "🚀 Ракета", "price": 75, "emoji": "🚀"},
    "star": {"name": "⭐ Звезда", "price": 30, "emoji": "⭐"}
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    user_data = get_user_data(user.id)
    
    keyboard = [
        [InlineKeyboardButton("🎁 Каталог подарков", callback_data="catalog")],
        [InlineKeyboardButton("💳 Баланс", callback_data="balance")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"🎁 Добро пожаловать в GiftBot, {user.first_name}!\n\n"
        f"💰 Ваш баланс: {user_data['balance']} монет\n"
        f"🎉 Отправляйте виртуальные подарки друзьям!"
    )
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def show_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает каталог подарков"""
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for gift_id, gift_info in GIFTS_CATALOG.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{gift_info['emoji']} {gift_info['name']} - {gift_info['price']} монет",
                callback_data=f"select_gift:{gift_id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🎁 Выберите подарок для отправки:",
        reply_markup=reply_markup
    )

async def select_gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор подарка"""
    query = update.callback_query
    await query.answer()
    
    gift_id = query.data.split(":")[1]
    gift_info = GIFTS_CATALOG.get(gift_id)
    
    if not gift_info:
        await query.edit_message_text("❌ Подарок не найден!")
        return
    
    keyboard = [
        [InlineKeyboardButton("💸 Купить и отправить", callback_data=f"buy_gift:{gift_id}")],
        [InlineKeyboardButton("🔙 Назад к каталогу", callback_data="catalog")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🎁 {gift_info['name']}\n"
        f"💰 Цена: {gift_info['price']} монет\n\n"
        f"Готовы купить этот подарок?",
        reply_markup=reply_markup
    )

async def buy_gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Покупка подарка"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    gift_id = query.data.split(":")[1]
    gift_info = GIFTS_CATALOG.get(gift_id)
    
    if not gift_info:
        await query.edit_message_text("❌ Подарок не найден!")
        return
    
    user_data = get_user_data(user_id)
    
    if user_data['balance'] < gift_info['price']:
        keyboard = [
            [InlineKeyboardButton("💰 Пополнить баланс", callback_data="add_balance")],
            [InlineKeyboardButton("🔙 Назад", callback_data="catalog")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"❌ Недостаточно средств!\n"
            f"💰 Ваш баланс: {user_data['balance']} монет\n"
            f"💸 Нужно: {gift_info['price']} монет",
            reply_markup=reply_markup
        )
        return
    
    # Списываем деньги
    new_balance = user_data['balance'] - gift_info['price']
    update_user_data(user_id, {
        'balance': new_balance,
        'gifts_sent': user_data['gifts_sent'] + 1,
        'total_spent': user_data['total_spent'] + gift_info['price']
    })
    
    keyboard = [
        [InlineKeyboardButton("🔙 В главное меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"✅ Подарок куплен!\n\n"
        f"🎁 {gift_info['name']}\n"
        f"💰 Списано: {gift_info['price']} монет\n"
        f"💳 Остаток: {new_balance} монет\n\n"
        f"🎉 Подарок отправлен!",
        reply_markup=reply_markup
    )

async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает баланс"""
    query = update.callback_query
    await query.answer()
    
    user_data = get_user_data(query.from_user.id)
    
    keyboard = [
        [InlineKeyboardButton("💰 Пополнить", callback_data="add_balance")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"💳 Ваш баланс: {user_data['balance']} монет\n"
        f"💸 Потрачено всего: {user_data['total_spent']} монет",
        reply_markup=reply_markup
    )

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает статистику"""
    query = update.callback_query
    await query.answer()
    
    user_data = get_user_data(query.from_user.id)
    
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"📊 Ваша статистика:\n\n"
        f"💳 Баланс: {user_data['balance']} монет\n"
        f"🎁 Подарков отправлено: {user_data['gifts_sent']}\n"
        f"🎉 Подарков получено: {user_data['gifts_received']}\n"
        f"💸 Всего потрачено: {user_data['total_spent']} монет",
        reply_markup=reply_markup
    )

async def add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пополнение баланса"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = get_user_data(user_id)
    
    bonus = 50
    new_balance = user_data['balance'] + bonus
    update_user_data(user_id, {'balance': new_balance})
    
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🎉 Бонус получен!\n"
        f"💰 Начислено: {bonus} монет\n"
        f"💳 Новый баланс: {new_balance} монет\n\n"
        f"В реальной версии здесь была бы оплата 💳",
        reply_markup=reply_markup
    )

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Помощь"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    help_text = (
        "🆘 Помощь по использованию бота:\n\n"
        "🎁 Каталог - выберите и купите подарок\n"
        "💳 Баланс - проверьте свои монеты\n"
        "📊 Статистика - ваши достижения\n\n"
        "🔄 Как отправить подарок:\n"
        "1. Выберите подарок из каталога\n"
        "2. Купите его за монеты\n"
        "3. Подарок будет отправлен!\n\n"
        "💡 Команды:\n"
        "/start - главное меню"
    )
    
    await query.edit_message_text(help_text, reply_markup=reply_markup)

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат в главное меню"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_data = get_user_data(user.id)
    
    keyboard = [
        [InlineKeyboardButton("🎁 Каталог подарков", callback_data="catalog")],
        [InlineKeyboardButton("💳 Баланс", callback_data="balance")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"🎁 GiftBot - {user.first_name}!\n\n"
        f"💰 Ваш баланс: {user_data['balance']} монет\n"
        f"🎉 Выберите действие:"
    )
    
    await query.edit_message_text(welcome_text, reply_markup=reply_markup)

# Создаем приложение Telegram
telegram_app = Application.builder().token(TOKEN).build()

# Регистрируем обработчики
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CallbackQueryHandler(show_catalog, pattern="^catalog$"))
telegram_app.add_handler(CallbackQueryHandler(select_gift, pattern="^select_gift:"))
telegram_app.add_handler(CallbackQueryHandler(buy_gift, pattern="^buy_gift:"))
telegram_app.add_handler(CallbackQueryHandler(show_balance, pattern="^balance$"))
telegram_app.add_handler(CallbackQueryHandler(show_stats, pattern="^stats$"))
telegram_app.add_handler(CallbackQueryHandler(add_balance, pattern="^add_balance$"))
telegram_app.add_handler(CallbackQueryHandler(show_help, pattern="^help$"))
telegram_app.add_handler(CallbackQueryHandler(back_to_main, pattern="^back_to_main$"))

@app.route("/")
def index():
    return "🎁 GiftBot is running! ✅"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    """Webhook для получения обновлений"""
    try:
        update_data = request.get_json(force=True)
        update = Update.de_json(update_data, telegram_app.bot)
        
        # Обрабатываем обновление в новом event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(telegram_app.process_update(update))
        loop.close()
        
        return "OK"
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}")
        return "ERROR", 500

def setup_webhook():
    """Устанавливает webhook"""
    try:
        webhook_url = f"{WEBHOOK_URL}/{TOKEN}"
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(telegram_app.bot.set_webhook(url=webhook_url))
        loop.close()
        logger.info(f"Webhook установлен: {webhook_url}")
    except Exception as e:
        logger.error(f"Ошибка установки webhook: {e}")

if __name__ == "__main__":
    # Устанавливаем webhook при запуске
    setup_webhook()
    
    # Запуск Flask приложения
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
