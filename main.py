import os
import requests
import json
import random
from flask import Flask, request

# Настройки
TOKEN = "7678954168:AAG6755ngOoYcQfIt6viZKMRXRcv6dOd0vY"
API_URL = f"https://api.telegram.org/bot{TOKEN}"
WEBHOOK_URL = "https://lambo-gift.onrender.com"  # <- убедись, что это твой хост

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
    """Обновление баланса (плюс/минус)"""
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
    """Главное меню — используем WEBHOOK_URL чтобы WebApp указывал на правильный хост"""
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
    """Логика игры Плинко (при использовании кнопок, старый режим)"""
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
    """Меню Плинко (старый режим с кнопками)"""
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
    """Играть в Плинко (старый режим)"""
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
    
    # Анимация падения шарика (текстовая)
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
    """WebApp интерфейс — Plinko (встроенный HTML)"""
    # Обратите внимание: поставлен min=10 для ставки
    webapp_html = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GiftBot WebApp - Plinko</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        /* Стили для Plinko — адаптированы под мобильный WebApp */
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg,#667eea 0%,#764ba2 100%); color:#fff; min-height:100vh; }
        .container { max-width:420px; margin: 10px auto; padding: 16px; }
        .header { text-align:center; margin-bottom:18px; background:rgba(255,255,255,0.06); padding:12px; border-radius:12px; }
        .balance { font-size:20px; font-weight:700; margin-bottom:6px; }
        .plinko-visual { background: linear-gradient(135deg,#1e3a8a,#3730a3); border-radius:12px; padding:16px; min-height:380px; margin-bottom:12px; }
        .plinko-pyramid { width:100%; height:240px; display:flex; align-items:center; justify-content:center; flex-direction:column; gap:8px; }
        .peg-row { display:flex; gap:14px; justify-content:center; }
        .peg { width:8px; height:8px; background:#fff; border-radius:50%; box-shadow:0 0 6px rgba(255,255,255,0.6); }
        .plinko-animation { position:relative; height:220px; margin-top:8px; overflow:hidden; }
        .plinko-ball { width:18px; height:18px; border-radius:50%; position:absolute; top:6px; left:50%; transform:translateX(-50%); box-shadow:0 0 12px rgba(59,130,246,0.8); transition: all 0.18s ease; z-index:20; background: radial-gradient(circle at 30% 30%, #60a5fa, #3b82f6); }
        .multipliers-bottom { display:grid; grid-template-columns: repeat(11, 1fr); gap:6px; margin-top:8px; }
        .multiplier { padding:8px 6px; border-radius:8px; font-weight:700; font-size:12px; text-align:center; border:1px solid rgba(255,255,255,0.12); background:rgba(255,255,255,0.03); }
        .btn { margin-top:12px; width:100%; padding:12px; border-radius:10px; border:none; font-weight:700; cursor:pointer; background:linear-gradient(45deg,#ff6b6b,#ee5a24); color:#fff; }
        .bet-input-section { display:flex; gap:8px; align-items:center; justify-content:center; margin-bottom:8px; }
        .bet-input { width:110px; padding:8px; border-radius:8px; border:1px solid rgba(255,255,255,0.12); background:rgba(255,255,255,0.03); color:#fff; text-align:center; }
        .total-bet { text-align:center; margin-top:8px; color:#ffeb3b; font-weight:700; }
        .result { margin-top:12px; padding:12px; border-radius:10px; background:rgba(255,255,255,0.06); display:none; text-align:center; }
        .result.show { display:block; animation:fadeIn 0.36s ease; }
        @keyframes fadeIn { from { opacity:0; transform:translateY(8px);} to { opacity:1; transform:none; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="balance">💰 <span id="balance">100</span> монет</div>
            <div>GiftBot — Plinko</div>
        </div>

        <div class="bet-input-section">
            <input id="betAmount" type="number" min="10" value="10" class="bet-input" />
            <input id="ballCount" type="number" min="1" max="5" value="1" class="bet-input" />
        </div>
        <div class="total-bet">Общая ставка: <span id="totalBet">10</span> монет</div>

        <div class="plinko-visual">
            <div class="plinko-pyramid" aria-hidden="true">
                <div class="peg-row"><div class="peg"></div><div class="peg"></div><div class="peg"></div></div>
                <div class="peg-row"><div class="peg"></div><div class="peg"></div><div class="peg"></div><div class="peg"></div></div>
                <div class="peg-row"><div class="peg"></div><div class="peg"></div><div class="peg"></div><div class="peg"></div><div class="peg"></div></div>
                <div class="peg-row"><div class="peg"></div><div class="peg"></div><div class="peg"></div><div class="peg"></div><div class="peg"></div><div class="peg"></div></div>
                <div class="peg-row"><div class="peg"></div><div class="peg"></div><div class="peg"></div><div class="peg"></div><div class="peg"></div><div class="peg"></div><div class="peg"></div></div>
                <div class="peg-row"><div class="peg"></div><div class="peg"></div><div class="peg"></div><div class="peg"></div><div class="peg"></div><div class="peg"></div><div class="peg"></div><div class="peg"></div></div>
                <div class="peg-row"><div class="peg"></div><div class="peg"></div><div class="peg"></div><div class="peg"></div><div class="peg"></div><div class="peg"></div><div class="peg"></div><div class="peg"></div><div class="peg"></div></div>
            </div>

            <div class="plinko-animation" id="plinkoAnimation"><!-- шарики будут сюда --></div>

            <div class="multipliers-bottom" id="multipliersBottom">
                <!-- 11 слотов -->
                <div class="multiplier">7x</div>
                <div class="multiplier">2x</div>
                <div class="multiplier">1x</div>
                <div class="multiplier">0.8x</div>
                <div class="multiplier">0.7x</div>
                <div class="multiplier">0.7x</div>
                <div class="multiplier">0.8x</div>
                <div class="multiplier">1x</div>
                <div class="multiplier">2x</div>
                <div class="multiplier">7x</div>
                <div class="multiplier">1x</div>
            </div>
        </div>

        <button class="btn" id="playBtn">🎲 Bet</button>

        <div id="result" class="result"></div>
    </div>

    <script>
        // Telegram WebApp ready
        if (window.Telegram && window.Telegram.WebApp) {
            window.Telegram.WebApp.ready();
            window.Telegram.WebApp.expand();
        }

        const userId = window.Telegram?.WebApp?.initDataUnsafe?.user?.id || 'demo_user';

        let userData = { balance: 100, plinkoPlayed: 0, plinkoWon: 0 };

        function loadLocal() {
            const saved = localStorage.getItem('giftbot_' + userId);
            if (saved) userData = JSON.parse(saved);
            updateUI();
        }
        function saveLocal() { localStorage.setItem('giftbot_' + userId, JSON.stringify(userData)); }
        function updateUI() { document.getElementById('balance').textContent = userData.balance; }

        loadLocal();

        document.getElementById('betAmount').addEventListener('input', updateTotal);
        document.getElementById('ballCount').addEventListener('input', updateTotal);
        function updateTotal() {
            const bet = parseInt(document.getElementById('betAmount').value) || 0;
            const balls = parseInt(document.getElementById('ballCount').value) || 0;
            document.getElementById('totalBet').textContent = bet * balls;
        }
        updateTotal();

        // multipliers array must match bottom slots order
        const multipliers = [7,2,1,0.8,0.7,0.7,0.8,1,2,7,1];

        document.getElementById('playBtn').addEventListener('click', () => {
            const bet = parseInt(document.getElementById('betAmount').value);
            const balls = parseInt(document.getElementById('ballCount').value) || 1;

            if (isNaN(bet) || bet < 10) {
                showResult('Минимальная ставка 10 монет', false);
                return;
            }
            if (isNaN(balls) || balls < 1) {
                showResult('Некорректное количество шариков', false);
                return;
            }
            const total = bet * balls;
            if (userData.balance < total) {
                showResult('Недостаточно средств для этой ставки', false);
                return;
            }

            // списываем локально (сервер проверит тоже)
            userData.balance -= total;
            userData.plinkoPlayed += balls;
            saveLocal();
            updateUI();

            // проводим симуляцию каждого шарика
            let completed = 0;
            let totalWin = 0;
            const results = [];

            for (let i=0;i<balls;i++) {
                setTimeout(() => {
                    playOne(bet, (res) => {
                        totalWin += res.winAmount;
                        results.push(res);
                        completed++;
                        // отправляем каждую итерацию? нет — ждём всех шариков
                        if (completed === balls) {
                            // начисляем выигрыш локально
                            userData.balance += totalWin;
                            userData.plinkoWon += totalWin;
                            saveLocal();
                            updateUI();

                            // посылаем данные в бота
                            const payload = { bet: bet, balls: balls, totalBet: total, totalWin: totalWin, results: results };
                            if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.sendData) {
                                window.Telegram.WebApp.sendData(JSON.stringify(payload));
                            }

                            // показываем результат пользователю в WebApp
                            let html = `<strong>Итог:</strong><br>Ставка: ${total} монет<br>Выигрыш: ${totalWin} монет`;
                            showResult(html, totalWin > 0);
                        }
                    });
                }, i * 220);
            }
        });

        function playOne(bet, cb) {
            const anim = document.getElementById('plinkoAnimation');
            const ball = document.createElement('div');
            ball.className = 'plinko-ball';
            anim.appendChild(ball);

            // start in center slot index = 5
            let pos = 5;
            const drops = 7;
            for (let i=0;i<drops;i++) {
                setTimeout(() => {
                    // случайный рикошет
                    const dev = Math.random() < 0.5 ? -1 : 1;
                    pos = Math.max(0, Math.min(multipliers.length-1, pos + dev));
                    // позиционируем визуально (проценты)
                    const leftPerc = (pos/(multipliers.length-1))*88 + 6; // отступы
                    ball.style.left = leftPerc + '%';
                    ball.style.top = (20 + i*28) + 'px';
                }, i * 180);
            }

            setTimeout(() => {
                const finalMultiplier = multipliers[pos];
                const win = Math.floor(bet * finalMultiplier);
                // подсветка слота
                const slots = document.querySelectorAll('.multiplier');
                if (slots[pos]) {
                    slots[pos].style.transform = 'scale(1.08)';
                    setTimeout(()=>{ slots[pos].style.transform = ''; }, 900);
                }
                // remove ball
                setTimeout(()=>{ ball.remove(); }, 1200);
                cb({ position: pos, multiplier: finalMultiplier, winAmount: win });
            }, drops * 180 + 160);
        }

        function showResult(html, ok=true) {
            const r = document.getElementById('result');
            r.innerHTML = html;
            r.classList.add('show');
            setTimeout(()=> r.classList.remove('show'), 5000);
        }
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
        
        # Если пришло сообщение
        if "message" in data:
            message = data["message"]
            chat_id = message["chat"]["id"]
            user_name = message["from"].get("first_name", "User")
            text = message.get("text", "")

            # --- Обработка WebApp sendData (message.web_app_data) ---
            if "web_app_data" in message:
                try:
                    raw = message["web_app_data"].get("data")
                    payload = json.loads(raw)
                    # payload ожидает: { bet, balls, totalBet, totalWin, results }
                    bet = int(payload.get("bet", 0))
                    total_bet = int(payload.get("totalBet", 0))
                    total_win = int(payload.get("totalWin", 0))
                    balls = int(payload.get("balls", 1))
                except Exception as e:
                    send_message(chat_id, "Ошибка при получении данных из WebApp.")
                    return "OK"

                user_data = get_user_data(chat_id)

                # серверная проверка минимальной ставки и баланса
                if bet < 10:
                    send_message(chat_id, "❌ Минимальная ставка — 10 монет.")
                    return "OK"
                if user_data["balance"] < total_bet:
                    send_message(chat_id, f"❌ Недостаточно средств на балансе. Нужны {total_bet}, у вас {user_data['balance']}.")
                    return "OK"

                # применяем транзакцию: списываем total_bet и начисляем total_win
                user_data["balance"] -= total_bet
                user_data["plinko_played"] += balls
                if total_win > 0:
                    user_data["balance"] += total_win
                    user_data["plinko_won"] += total_win

                # Ответ пользователю в чате с итогом
                msg = (f"🎮 <b>Plinko — результат</b>\n\n"
                       f"💸 Ставка за шарик: {bet} монет\n"
                       f"🎲 Шариков: {balls}\n"
                       f"🏆 Выигрыш: {total_win} монет\n\n"
                       f"💳 Баланс: {user_data['balance']} монет")
                send_message(chat_id, msg)
                return "OK"

            # Обычное текстовое сообщение
            print(f"Сообщение от {user_name}: {text}")
            if text == "/start":
                handle_start(chat_id, user_name)
            else:
                send_message(chat_id, f"Получил: {text}\nИспользуйте /start для начала")
        
        # Обработка callback_query (inline кнопки)
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
    # Устанавливаем webhook (проверь WEBHOOK_URL)
    webhook_url = f"{WEBHOOK_URL}/{TOKEN}"
    try:
        response = requests.post(f"{API_URL}/setWebhook", data={"url": webhook_url})
        print(f"Установка webhook: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Ошибка при установке webhook: {e}")
    
    # Запускаем Flask
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
