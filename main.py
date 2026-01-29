import os
from flask import Flask, request
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

GROUP_USERNAME = None
CHANNEL_USERNAME = None
FORWARD_ENABLED = False
WAITING_FOR = None

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

# ---------- Keyboards ----------

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ تنظیم گروه", callback_data="set_group")],
        [InlineKeyboardButton("📢 تنظیم کانال", callback_data="set_channel")],
        [
            InlineKeyboardButton("▶️ شروع فروارد", callback_data="start_fw"),
            InlineKeyboardButton("⏸️ توقف فروارد", callback_data="stop_fw")
        ]
    ])

# ---------- Commands ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎛 پنل مدیریت ربات فروارد\n"
        "همه تنظیمات با دکمه انجام میشه",
        reply_markup=main_keyboard()
    )

# ---------- Buttons ----------

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global WAITING_FOR, FORWARD_ENABLED
    query = update.callback_query
    await query.answer()

    if query.data == "set_group":
        WAITING_FOR = "group"
        await query.message.reply_text("یوزرنیم گروه رو بفرست (مثال: @mygroup)")

    elif query.data == "set_channel":
        WAITING_FOR = "channel"
        await query.message.reply_text("یوزرنیم کانال رو بفرست (مثال: @mychannel)")

    elif query.data == "start_fw":
        FORWARD_ENABLED = True
        await query.message.reply_text("▶️ فروارد فعال شد")

    elif query.data == "stop_fw":
        FORWARD_ENABLED = False
        await query.message.reply_text("⏸️ فروارد متوقف شد")

# ---------- Username Handler ----------

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global GROUP_USERNAME, CHANNEL_USERNAME, WAITING_FOR

    text = update.message.text.strip()

    if not text.startswith("@"):
        await update.message.reply_text("❌ یوزرنیم باید با @ شروع بشه")
        return

    try:
        chat = await context.bot.get_chat(text)
        member = await context.bot.get_chat_member(chat.id, context.bot.id)

        if member.status not in ["administrator", "creator"]:
            await update.message.reply_text("❌ ربات ادمین نیست")
            return

        if WAITING_FOR == "group":
            GROUP_USERNAME = text
            await update.message.reply_text("✅ گروه تنظیم شد")

        elif WAITING_FOR == "channel":
            CHANNEL_USERNAME = text
            await update.message.reply_text("✅ کانال تنظیم شد")

        WAITING_FOR = None

    except:
        await update.message.reply_text("❌ یوزرنیم نامعتبر یا ربات عضو نیست")

# ---------- Forward ----------

async def forward_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not FORWARD_ENABLED:
        return
    if not GROUP_USERNAME or not CHANNEL_USERNAME:
        return

    if update.effective_chat.username and f"@{update.effective_chat.username}" == GROUP_USERNAME:
        try:
            await update.message.forward(chat_id=CHANNEL_USERNAME)
        except:
            pass

# ---------- Webhook ----------

@app.route("/", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok"

async def main():
    await application.initialize()
    await application.bot.set_webhook(WEBHOOK_URL)
    await application.start()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
    app.run(host="0.0.0.0", port=10000)
