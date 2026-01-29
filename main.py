import os
import telebot
from telebot import types
import json
from flask import Flask, request

# ---------- ENV ----------
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TOKEN or not WEBHOOK_URL:
    raise RuntimeError("BOT_TOKEN یا WEBHOOK_URL تنظیم نشده")

OWNER_ID = 601668306
DB_FILE = "db.json"

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# ---------- دیتابیس ----------
try:
    with open(DB_FILE, "r") as f:
        db = json.load(f)
except:
    db = {
        "owners": [OWNER_ID],
        "admins": [],
        "users": [],
        "groups": [],
        "channels": {}
    }

owners = set(db["owners"])
admins = set(db["admins"])
allowed_users = set(db["users"])
groups = db["groups"]
user_channels = db["channels"]

def save_db():
    db["owners"] = list(owners)
    db["admins"] = list(admins)
    db["users"] = list(allowed_users)
    db["groups"] = groups
    db["channels"] = user_channels
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

# ---------- پنل ----------
def panel(is_owner=False):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ افزودن کاربر", "➖ حذف کاربر")
    kb.add("➕ افزودن گروه", "➖ حذف گروه")
    kb.add("➕ افزودن کانال", "➖ حذف کانال")
    if is_owner:
        kb.add("➕ افزودن ادمین", "➖ حذف ادمین")
    kb.add("📋 لیست کل")
    return kb

# ---------- استارت ----------
@bot.message_handler(commands=["start"])
def start(msg):
    uid = msg.from_user.id

    if uid in owners:
        bot.send_message(uid, "👑 پنل مالک", reply_markup=panel(True))
        return

    if uid in admins:
        bot.send_message(uid, "🛠 پنل ادمین", reply_markup=panel(False))
        return

    if uid not in allowed_users:
        bot.send_message(
            uid,
            "❌ ربات برای شما فعال نیست\nبرای فعال‌سازی پیام دهید"
        )
        return

    bot.send_message(uid, "✅ ربات برای شما فعال است")

# ---------- دکمه‌ها ----------
@bot.message_handler(func=lambda m: True)
def buttons(msg):
    uid = msg.from_user.id
    text = msg.text

    if uid not in owners and uid not in admins:
        return

    is_owner = uid in owners

    if text == "➕ افزودن کاربر":
        bot.send_message(uid, "آیدی عددی کاربر را ارسال کنید")
        bot.register_next_step_handler(msg, add_user)

    elif text == "➖ حذف کاربر":
        bot.send_message(uid, "آیدی عددی کاربر را ارسال کنید")
        bot.register_next_step_handler(msg, remove_user)

    elif text == "➕ افزودن گروه":
        bot.send_message(uid, "یوزرنیم گروه با @")
        bot.register_next_step_handler(msg, add_group)

    elif text == "➖ حذف گروه":
        bot.send_message(uid, "یوزرنیم گروه با @")
        bot.register_next_step_handler(msg, remove_group)

    elif text == "➕ افزودن کانال":
        bot.send_message(uid, "یوزرنیم کانال با @")
        bot.register_next_step_handler(msg, add_channel)

    elif text == "➖ حذف کانال":
        bot.send_message(uid, "یوزرنیم کانال با @")
        bot.register_next_step_handler(msg, remove_channel)

    elif text == "➕ افزودن ادمین" and is_owner:
        bot.send_message(uid, "آیدی عددی ادمین")
        bot.register_next_step_handler(msg, add_admin)

    elif text == "➖ حذف ادمین" and is_owner:
        bot.send_message(uid, "آیدی عددی ادمین")
        bot.register_next_step_handler(msg, remove_admin)

# ---------- توابع ----------
def add_user(msg):
    try:
        allowed_users.add(int(msg.text))
        save_db()
        bot.send_message(msg.chat.id, "✅ اضافه شد")
    except:
        bot.send_message(msg.chat.id, "❌ نامعتبر")

def remove_user(msg):
    try:
        allowed_users.discard(int(msg.text))
        save_db()
        bot.send_message(msg.chat.id, "✅ حذف شد")
    except:
        bot.send_message(msg.chat.id, "❌ نامعتبر")

def add_admin(msg):
    try:
        admins.add(int(msg.text))
        save_db()
        bot.send_message(msg.chat.id, "✅ اضافه شد")
    except:
        bot.send_message(msg.chat.id, "❌ نامعتبر")

def remove_admin(msg):
    try:
        admins.discard(int(msg.text))
        save_db()
        bot.send_message(msg.chat.id, "✅ حذف شد")
    except:
        bot.send_message(msg.chat.id, "❌ نامعتبر")

def add_group(msg):
    g = msg.text.strip()
    try:
        bot.get_chat_member(g, bot.get_me().id)
        if g not in groups:
            groups.append(g)
            save_db()
            bot.send_message(msg.chat.id, "✅ گروه اضافه شد")
    except:
        bot.send_message(msg.chat.id, "❌ ربات عضو نیست")

def remove_group(msg):
    if msg.text in groups:
        groups.remove(msg.text)
        save_db()
        bot.send_message(msg.chat.id, "✅ حذف شد")

def add_channel(msg):
    c = msg.text.strip()
    try:
        bot.get_chat_member(c, bot.get_me().id)
        user_channels[str(msg.from_user.id)] = c
        save_db()
        bot.send_message(msg.chat.id, "✅ کانال اضافه شد")
    except:
        bot.send_message(msg.chat.id, "❌ ربات ادمین نیست")

def remove_channel(msg):
    for k, v in list(user_channels.items()):
        if v == msg.text:
            del user_channels[k]
            save_db()
            bot.send_message(msg.chat.id, "✅ حذف شد")

# ---------- فوروارد ----------
@bot.message_handler(content_types=["text", "photo", "video", "document", "audio", "voice", "sticker"])
def forward_all(msg):
    if msg.chat.type not in ["group", "supergroup"]:
        return
    if not msg.chat.username:
        return

    g = "@" + msg.chat.username
    if g not in groups:
        return

    for ch in user_channels.values():
        try:
            bot.forward_message(ch, msg.chat.id, msg.message_id)
        except:
            pass

# ---------- Webhook ----------
@app.route("/", methods=["POST"])
def webhook():
    bot.process_new_updates(
        [telebot.types.Update.de_json(request.stream.read().decode("utf-8"))]
    )
    return "OK", 200

@app.route("/", methods=["GET"])
def index():
    return "Bot is running", 200

# ---------- RUN ----------
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
