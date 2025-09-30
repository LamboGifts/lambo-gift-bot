import os
import logging
from flask import Flask, request, send_from_directory, jsonify
import requests

# --- Настройки ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
PORT = int(os.environ.get("PORT", 5000))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# --- Flask-приложение ---
app = Flask(__name__, static_folder="static", static_url_path="/static")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Telegram webhook ---
@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    update = request.get_json()
    if not update:
        return jsonify({"ok": False}), 400

    try:
        if "message" in update:
            chat_id = update["message"]["chat"]["id"]
            text = update["message"].get("text", "")

            if text == "/start":
                send_message(
                    chat_id,
                    "👋 Привет! Добро пожаловать в Lambo Gift.\nНажми кнопку ниже, чтобы открыть WebApp.",
                    reply_markup={
                        "inline_keyboard": [
                            [
                                {
                                    "text": "🚀 Открыть Lambo Gift",
                                    "web_app": {"url": f"{WEBHOOK_URL}/webapp"},
                                }
                            ]
                        ]
                    },
                )
    except Exception as e:
        logger.error(f"Error handling update: {e}")

    return jsonify({"ok": True})


def send_message(chat_id, text, reply_markup=None):
    try:
        url = f"{API_URL}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        logger.error(f"send_message error: {e}")
        return None


# --- WebApp (React build) ---
@app.route("/webapp")
def serve_webapp():
    return send_from_directory(app.static_folder, "index.html")


@app.errorhandler(404)
def not_found(_):
    """Раздача статики (JS, CSS и т.д.)"""
    path = request.path.lstrip("/")
    file_path = os.path.join(app.static_folder, path)
    if os.path.exists(file_path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")


# --- Healthcheck для Render ---
@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# --- Установка вебхука ---
def set_webhook():
    if not WEBHOOK_URL:
        logger.warning("WEBHOOK_URL is not set, skipping webhook setup")
        return
    url = f"{API_URL}/setWebhook"
    webhook_url = f"{WEBHOOK_URL}/webhook/{BOT_TOKEN}"
    try:
        response = requests.post(url, json={"url": webhook_url}, timeout=10)
        result = response.json()
        if result.get("ok"):
            logger.info(f"Webhook set successfully: {webhook_url}")
        else:
            logger.error(f"Failed to set webhook: {result}")
    except Exception as e:
        logger.error(f"Webhook setup error: {e}")


# --- Запуск ---
if __name__ == "__main__":
    set_webhook()
    app.run(host="0.0.0.0", port=PORT)
