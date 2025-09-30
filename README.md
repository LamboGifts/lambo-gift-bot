# 🚀 Lambo Gift — Telegram WebApp Bot

Этот проект — Telegram-бот с WebApp интерфейсом.  
Бэкенд написан на **Flask**, фронтенд можно собрать через **React** и положить в папку `static/`.

---

## 📦 Что внутри
- `main.py` — Flask + Telegram webhook + WebApp
- `requirements.txt` — зависимости
- `runtime.txt` — версия Python
- `static/` — здесь хранится React build (сейчас заглушка)

---

## 🚀 Деплой на Render

### 1. Подготовь GitHub репозиторий
Создай новый репозиторий с именем:
```
lambo-gift
```

Залей в него файлы:
- `main.py`
- `requirements.txt`
- `runtime.txt`
- папку `static/`

```bash
git init
git remote add origin https://github.com/ТВОЙ_АККАУНТ/lambo-gift.git
git add .
git commit -m "Initial commit for Lambo Gift bot"
git push origin master
```

---

### 2. Настрой Render
1. Создай новый **Web Service**.  
2. Подключи свой репозиторий **lambo-gift**.  
3. В настройках **Environment Variables** добавь:
   - `BOT_TOKEN=твой_токен_бота`
   - `WEBHOOK_URL=https://имя-сервиса.onrender.com`
   - `PORT` Render задаст сам.  

4. Нажми **Deploy**.  

---

### 3. Проверка
- Открой:
  ```
  https://имя-сервиса.onrender.com/health
  ```
  Ответ:
  ```json
  {"status": "ok"}
  ```

- В Telegram напиши `/start`.  
- Бот пришлёт кнопку «🚀 Открыть Lambo Gift».  
- Откроется WebApp (`/webapp`).  

---

### 4. React WebApp
Когда сделаешь фронтенд:
```bash
npm run build
```
Скопируй содержимое `build/` в `static/` → закоммить → задеплой.  

---

✨ Теперь у тебя работает **Lambo Gift**!
