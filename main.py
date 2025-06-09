import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# === 建立 SQLite 資料庫 ===
conn = sqlite3.connect("subscriptions.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS subscriptions (
        chat_id INTEGER,
        keyword TEXT
    )
''')
conn.commit()

# === 功能：新增關鍵字 ===
def add_keyword(chat_id: int, keyword: str):
    cursor.execute("INSERT INTO subscriptions (chat_id, keyword) VALUES (?, ?)", (chat_id, keyword))
    conn.commit()

# === 功能：刪除關鍵字 ===
def remove_keyword(chat_id: int, keyword: str):
    cursor.execute("DELETE FROM subscriptions WHERE chat_id=? AND keyword=?", (chat_id, keyword))
    conn.commit()

# === 功能：查詢已訂閱關鍵字 ===
def get_keywords(chat_id: int):
    cursor.execute("SELECT keyword FROM subscriptions WHERE chat_id=?", (chat_id,))
    return [row[0] for row in cursor.fetchall()]

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 歡迎使用 PTT 新文章提醒 Ticki Artino！請直接輸入你想訂閱的關鍵字💖")

# === 訂閱關鍵字（使用者傳文字）===
async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    keyword = update.message.text.strip()

    add_keyword(chat_id, keyword)
    await update.message.reply_text(f"✅ 已訂閱關鍵字：「{keyword}」")

# === /list 查看已訂閱 ===
async def list_keywords(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    keywords = get_keywords(chat_id)

    if keywords:
        await update.message.reply_text("📋 你訂閱的關鍵字：\n" + "\n".join(keywords))
    else:
        await update.message.reply_text("📭 你目前沒有訂閱任何關鍵字。")

# === /remove <keyword> 取消訂閱 ===
async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not context.args:
        await update.message.reply_text("❗請提供要取消的關鍵字，例如：/remove 五月天")
        return

    keyword = " ".join(context.args)
    keywords = get_keywords(chat_id)

    if keyword in keywords:
        remove_keyword(chat_id, keyword)
        await update.message.reply_text(f"❌ 已取消訂閱：「{keyword}」")
    else:
        await update.message.reply_text(f"⚠️ 你尚未訂閱「{keyword}」")

# === 啟動應用 ===
app = ApplicationBuilder().token("YOUR_BOT_TOKEN").build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("list", list_keywords))
app.add_handler(CommandHandler("remove", remove))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, subscribe))

app.run_polling()
