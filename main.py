import json
import os
import logging
import asyncio
import random
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен и адрес вебхука (захардкожены)
TOKEN = "7678954168:AAG6755ngOoYcQfIt6viZKMRXRcv6dOd0vY"
WEBHOOK_URL = "https://lambo-gift-bot.onrender.com"

# Файл для хранения данных
DATA_FILE = "data.json"

# Flask приложение
app = Flask(__name__)

# =============== Работа с данными ===============

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Ошибка сохранения данных: {e}")

def get_user_data(user_id):
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
    data = load_data()
    user_id = str(user_id)
    if user_id not in data:
        get_user_data(user_id)
        data = load_data()
    data[user_id].update(updates)
    save_data(data)

# =============== Каталог подарков ===============

GIFTS_CATALOG = {
    "rose": {"name": "🌹 Роза", "price": 10, "emoji": "🌹"},
    "cake": {"name": "🎂 Торт", "price": 25, "emoji": "🎂"},
    "diamond": {"name": "💎 Бриллиант", "price": 50, "emoji": "💎"},
    "crown": {"name": "👑 Корона", "price": 100, "emoji": "👑"},
    "rocket": {"name": "🚀 Ракета", "price": 75, "emoji": "🚀"},
    "star": {"name": "⭐ Звезда", "price": 30, "emoji": "⭐"}
}

# =============== Plinko ===============

PLINKO_MULTIPLIERS = [0, 0.5, 1, 2, 5, 10]

async def plinko_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("10", callback_data="plinko_bet:10"),
         InlineKeyboardButton("25", callback_data="plinko_bet:25")],
        [InlineKeyboardButton("50", callback_data="plinko_bet:50"),
         InlineKeyboardButton("100", callback_data="plinko_bet:100")],
        [InlineKeyboardButton("🔢 Ввести вручную", callback_data="plinko_custom")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text("🎮 Выберите ставку для игры в Plinko (мин. 10):", reply_markup=reply_markup)

async def plinko_custom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["awaiting_custom_bet"] = True
    await query.edit_message_text("💬 Введите ставку (минимум 10):")

async def handle_custom_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_custom_bet"):
        return

    try:
        bet = int(update.message.text)
        if bet < 10:
            await update.message.reply_text("❌ Минимальная ставка 10 монет!")
            return
        await play_plinko(update, context, bet)
    except ValueError:
        await update.message.reply_text("❌ Введите число!")
    finally:
        context.user_data["awaiting_custom_bet"] = False

async def plinko_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    bet = int(query.data.split(":")[1])
    await play_plinko(update, context, bet, query)

async def play_plinko(update: Update, context: ContextTypes.DEFAULT_TYPE, bet: int, query=None):
    user_id = (query.from_user.id if query else update.message.from_user.id)
    user_data = get_user_data(user_id)

    if user_data['balance'] < bet:
        if query:
            await query.edit_message_text(
                f"❌ Недостаточно средств! Баланс: {user_data['balance']} монет",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💰 Пополнить", callback_data="add_balance")]])
            )
        else:
            await update.message.reply_text(f"❌ Недостаточно средств! Баланс: {user_data['balance']} монет")
        return

    # списываем ставку
    new_balance = user_data['balance'] - bet

    # случайный множитель
    multiplier = random.choice(PLINKO_MULTIPLIERS)
    win = int(bet * multiplier)
    new_balance += win

    update_user_data(user_id, {"balance": new_balance})

    result_text = (
        f"🎮 Plinko!\n\n"
        f"💸 Ставка: {bet} монет\n"
        f"🎯 Множитель: x{multiplier}\n"
        f"🏆 Выигрыш: {win} монет\n\n"
        f"💰 Баланс: {new_balance} монет"
    )

    keyboard = [[InlineKeyboardButton("🎮 Играть снова", callback_data="plinko")],
                [InlineKeyboardButton("🔙 В меню", callback_data="back_to_main")]]

    if query:
        await query.edit_message_text(result_text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(result_text, reply_markup=InlineKeyboardMarkup(keyboard))

# =============== GiftBot стандартные функции ===============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = get_user_data(user.id)

    keyboard = [
        [InlineKeyboardButton("🎁 Каталог подарков", callback_data="catalog")],
        [InlineKeyboardButton("💳 Баланс", callback_data="balance")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("🎮 Plinko", callback_data="plinko")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        f"🎁 Добро пожаловать, {user.first_name}!\n\n"
        f"💰 Ваш баланс: {user_data['balance']} монет\n"
        f"🎉 Отправляйте подарки и играйте в Plinko!"
    )

    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def show_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    await query.edit_message_text("🎁 Выберите подарок:", reply_markup=InlineKeyboardMarkup(keyboard))

async def select_gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    gift_id = query.data.split(":")[1]
    gift_info = GIFTS_CATALOG.get(gift_id)
    if not gift_info:
        await query.edit_message_text("❌ Подарок не найден!")
        return
    keyboard = [
        [InlineKeyboardButton("💸 Купить", callback_data=f"buy_gift:{gift_id}")],
        [InlineKeyboardButton("🔙 Назад", callback_data="catalog")]
    ]
    await query.edit_message_text(
        f"🎁 {gift_info['name']}\n💰 Цена: {gift_info['price']} монет",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def buy_gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        await query.edit_message_text("❌ Недостаточно средств!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💰 Пополнить", callback_data="add_balance")]]))
        return
    new_balance = user_data['balance'] - gift_info['price']
    update_user_data(user_id, {
        'balance': new_balance,
        'gifts_sent': user_data['gifts_sent'] + 1,
        'total_spent': user_data['total_spent'] + gift_info['price']
    })
    await query.edit_message_text(
        f"✅ Куплен подарок: {gift_info['name']}\n💳 Остаток: {new_balance} монет",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 В меню", callback_data="back_to_main")]])
    )

async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data = get_user_data(query.from_user.id)
    await query.edit_message_text(
        f"💳 Баланс: {user_data['balance']} монет\n💸 Потрачено: {user_data['total_spent']} монет",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💰 Пополнить", callback_data="add_balance")],[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]])
    )

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data = get_user_data(query.from_user.id)
    await query.edit_message_text(
        f"📊 Статистика:\n💳 Баланс: {user_data['balance']}\n🎁 Подарков отправлено: {user_data['gifts_sent']}\n🎉 Подарков получено: {user_data['gifts_received']}\n💸 Потрачено: {user_data['total_spent']}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]])
    )

async def add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_data = get_user_data(user_id)
    bonus = 50
    new_balance = user_data['balance'] + bonus
    update_user_data(user_id, {'balance': new_balance})
    await query.edit_message_text(f"🎉 Пополнение! +{bonus} монет. Новый баланс: {new_balance}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]]))

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🆘 Помощь: /start — главное меню, 🎁 — подарки, 🎮 — Plinko", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]]))

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    user_data = get_user_data(user.id)
    keyboard = [
        [InlineKeyboardButton("🎁 Каталог подарков", callback_data="catalog")],
        [InlineKeyboardButton("💳 Баланс", callback_data="balance")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("🎮 Plinko", callback_data="plinko")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    await query.edit_message_text(f"🎁 GiftBot — {user.first_name}\n💰 Баланс: {user_data['balance']} монет", reply_markup=InlineKeyboardMarkup(keyboard))

# =============== Flask + Webhook ===============

telegram_app = Application.builder().token(TOKEN).build()

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CallbackQueryHandler(show_catalog, pattern="^catalog$"))
telegram_app.add_handler(CallbackQueryHandler(select_gift, pattern="^select_gift:"))
telegram_app.add_handler(CallbackQueryHandler(buy_gift, pattern="^buy_gift:"))
telegram_app.add_handler(CallbackQueryHandler(show_balance, pattern="^balance$"))
telegram_app.add_handler(CallbackQueryHandler(show_stats, pattern="^stats$"))
telegram_app.add_handler(CallbackQueryHandler(add_balance, pattern="^add_balance$"))
telegram_app.add_handler(CallbackQueryHandler(show_help, pattern="^help$"))
telegram_app.add_handler(CallbackQueryHandler(back_to_main, pattern="^back_to_main$"))

telegram_app.add_handler(CallbackQueryHandler(plinko_menu, pattern="^plinko$"))
telegram_app.add_handler(CallbackQueryHandler(plinko_bet, pattern="^plinko_bet:"))
telegram_app.add_handler(CallbackQueryHandler(plinko_custom, pattern="^plinko_custom$"))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_bet))

@app.route("/")
def index():
    return "🎁 GiftBot with Plinko is running! ✅"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    try:
        update_data = request.get_json(force=True)
        update = Update.de_json(update_data, telegram_app.bot)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(telegram_app.process_update(update))
        loop.close()
        return "OK"
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}")
        return "ERROR", 500

def setup_webhook():
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
    setup_webhook()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
