import os
import sqlite3
import requests
import asyncio
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# === 資料庫設定 ===
conn = sqlite3.connect("subscriptions.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS subscriptions (
        chat_id INTEGER,
        keyword TEXT
    )
''')
conn.commit()

# === 關鍵字功能 ===
def add_keyword(chat_id: int, keyword: str):
    cursor.execute("INSERT INTO subscriptions (chat_id, keyword) VALUES (?, ?)", (chat_id, keyword))
    conn.commit()

def remove_keyword(chat_id: int, keyword: str):
    cursor.execute("DELETE FROM subscriptions WHERE chat_id=? AND keyword=?", (chat_id, keyword))
    conn.commit()

def get_keywords(chat_id: int):
    cursor.execute("SELECT keyword FROM subscriptions WHERE chat_id=?", (chat_id,))
    return [row[0] for row in cursor.fetchall()]

def get_all_subscriptions():
    cursor.execute("SELECT DISTINCT chat_id FROM subscriptions")
    return [row[0] for row in cursor.fetchall()]

# === 指令處理 ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 歡迎使用 PTT 新文章提醒 Ticki Artino！請直接輸入你想訂閱的關鍵字💖")

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    keyword = update.message.text.strip()
    add_keyword(chat_id, keyword)
    await update.message.reply_text(f"✅ 已訂閱關鍵字：「{keyword}」")

async def list_keywords(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    keywords = get_keywords(chat_id)
    if keywords:
        await update.message.reply_text("📋 你訂閱的關鍵字：\n" + "\n".join(keywords))
    else:
        await update.message.reply_text("📭 你目前沒有訂閱任何關鍵字。")

async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not context.args:
        await update.message.reply_text("❗請提供要取消的關鍵字，例如：/remove 五月天")
        return
    keyword = " ".join(context.args)
    if keyword in get_keywords(chat_id):
        remove_keyword(chat_id, keyword)
        await update.message.reply_text(f"❌ 已取消訂閱：「{keyword}」")
    else:
        await update.message.reply_text(f"⚠️ 你尚未訂閱「{keyword}」")

# === PTT 爬蟲部分 ===
notified_articles = set()

async def crawl_and_notify(app):
    while True:
        try:
            print("🔍 正在檢查 PTT 新文章...")
            resp = requests.get("https://www.ptt.cc/bbs/Drama-Ticket/index.html", headers={'cookie': 'over18=1'})
            soup = BeautifulSoup(resp.text, "html.parser")
            entries = soup.select("div.r-ent")

            for entry in entries:
                title_tag = entry.select_one("div.title a")
                if not title_tag:
                    continue
                title = title_tag.text.strip()
                link = "https://www.ptt.cc" + title_tag["href"]

                if link in notified_articles:
                    continue

                for chat_id in get_all_subscriptions():
                    keywords = get_keywords(chat_id)
                    for keyword in keywords:
                        if keyword in title:
                            await app.bot.send_message(chat_id=chat_id, text=f"📢 新文章關於「{keyword}」：\n{title}\n🔗 {link}")
                            notified_articles.add(link)
                            break  # 不重複通知同一個 chat_id 多次

            await asyncio.sleep(60)

        except Exception as e:
            print("❗錯誤發生：", e)
            await asyncio.sleep(60)

# === 主程式啟動 ===
TOKEN = os.getenv("TOKEN")
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("list", list_keywords))
app.add_handler(CommandHandler("remove", remove))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, subscribe))

# 加入定時爬蟲任務
async def main():
    asyncio.create_task(crawl_and_notify(app))
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
