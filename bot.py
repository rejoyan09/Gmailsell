
import os
import sqlite3
from telebot import TeleBot, types
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
MIN_WITHDRAW = int(os.getenv("MIN_WITHDRAW"))
TASK_PRICE = int(os.getenv("TASK_PRICE"))

bot = TeleBot(BOT_TOKEN)
conn = sqlite3.connect("botdata.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 0,
    pending INTEGER DEFAULT 0,
    tasks_done INTEGER DEFAULT 0
)
""")
conn.commit()

@bot.message_handler(commands=["start"])
def handle_start(msg):
    uid = msg.from_user.id
    username = msg.from_user.username or "unknown"

    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users (user_id, username) VALUES (?,?)", (uid, username))
        conn.commit()

    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("📋 Tasks", callback_data="tasks"),
        types.InlineKeyboardButton("💰 Balance", callback_data="balance")
    )
    markup.row(
        types.InlineKeyboardButton("📤 Withdraw", callback_data="withdraw"),
        types.InlineKeyboardButton("👤 Profile", callback_data="profile")
    )
    bot.send_message(uid, "👋 স্বাগতম! নিচের মেনু ব্যবহার করুন:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    uid = call.from_user.id
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    user = cur.fetchone()
    if not user:
        bot.send_message(uid, "❌ /start দিয়ে শুরু করুন")
        return

    if call.data == "balance":
        bot.send_message(uid, f"💰 Balance: ৳{user[2]}
⏳ Pending: ৳{user[3]}")
    elif call.data == "profile":
        bot.send_message(uid, f"👤 Username: @{user[1]}
✅ Task Done: {user[4]}")
    elif call.data == "withdraw":
        if user[2] < MIN_WITHDRAW:
            bot.send_message(uid, f"❌ মিনিমাম উইথড্র ৳{MIN_WITHDRAW} দরকার")
        else:
            bot.send_message(uid, "✅ `/withdraw method number amount` লিখুন")
    elif call.data == "tasks":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"Gmail Create - ৳{TASK_PRICE}", callback_data="do_task"))
        bot.send_message(uid, "📋 কাজ বেছে নিন:", reply_markup=markup)
    elif call.data == "do_task":
        bot.send_message(uid, "🔰 `/submit gmail:pass:recovery_email` লিখুন")
        cur.execute("UPDATE users SET pending = pending + ? WHERE user_id=?", (TASK_PRICE, uid))
        conn.commit()

@bot.message_handler(commands=["submit"])
def submit_task(msg):
    uid = msg.from_user.id
    cur.execute("SELECT pending FROM users WHERE user_id=?", (uid,))
    user = cur.fetchone()
    if not user or user[0] == 0:
        bot.reply_to(msg, "❌ কোনো pending task নেই")
        return
    cur.execute("UPDATE users SET balance = balance + pending, tasks_done = tasks_done + 1, pending = 0 WHERE user_id=?", (uid,))
    conn.commit()
    bot.reply_to(msg, "✅ কাজ সফলভাবে সাবমিট হয়েছে")

@bot.message_handler(commands=["withdraw"])
def withdraw_handler(msg):
    uid = msg.from_user.id
    cur.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    balance = cur.fetchone()[0]
    if balance < MIN_WITHDRAW:
        bot.reply_to(msg, f"❌ মিনিমাম ব্যালেন্স দরকার ৳{MIN_WITHDRAW}")
    else:
        bot.reply_to(msg, "📨 তোমার উইথড্র রিকোয়েস্ট রিভিউ হচ্ছে")

bot.infinity_polling()
