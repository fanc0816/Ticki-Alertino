from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import sqlite3, os
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from bs4 import BeautifulSoup

TOKEN = os.environ["TOKEN"]
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS subscriptions (chat_id TEXT, keyword TEXT)""")

# Bot 回應區
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("請輸入你想訂閱的關鍵字")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    keyword = update.message.text.strip()
    cursor.execute("INSERT INTO subscriptions (chat_id, keyword) VALUES (?, ?)", (chat_id, keyword))
    conn.commit()
    await update.message.reply_text(f"成功訂閱關鍵字：{keyword}")

# 爬蟲 + 比對
def get_latest_posts():
    url = "https://www.ptt.cc/bbs/Drama-Ticket/index.html"
    headers = {"cookie": "over18=1"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    articles = []
    for item in soup.select(".r-ent"):
        a_tag = item.select_one(".title a")
        if a_tag:
            title = a_tag.text.strip()
            link = "https://www.ptt.cc" + a_tag["href"]
            articles.append((title, link))
    return articles

def check_for_matches(app):
    posts = get_latest_posts()
    cursor.execute("SELECT DISTINCT chat_id, keyword FROM subscriptions")
    for chat_id, keyword in cursor.fetchall():
        for title, link in posts:
            if keyword in title:
                app.bot.send_message(chat_id=chat_id, text=f"🎫 有新票務文章符合關鍵字「{keyword}」！\n{title}\n{link}")

# 定時器
scheduler = BackgroundScheduler()
def start_scheduler(app):
    scheduler.add_job(lambda: check_for_matches(app), "interval", seconds=60)
    scheduler.start()

# 建立 bot
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

start_scheduler(app)
app.run_polling()
