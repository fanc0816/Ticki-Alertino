from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import sqlite3
import os

TOKEN = os.environ["TOKEN"]
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        chat_id TEXT,
        keyword TEXT
    )
""")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎵 請輸入你想訂閱的關鍵字（如：lady gaga、五月天）")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    keyword = update.message.text.strip()
    cursor.execute("INSERT INTO subscriptions (chat_id, keyword) VALUES (?, ?)", (chat_id, keyword))
    conn.commit()
    await update.message.reply_text(f"✅ 成功訂閱關鍵字：{keyword}")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

app.run_polling()
