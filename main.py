import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

GROUP_USERNAME = None
CHANNEL_USERNAME = None
FORWARD_ENABLED = False
WAITING_FOR = None

def panel():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ تنظیم گروه", callback_data="set_group")],
        [InlineKeyboardButton("📢 تنظیم کانال", callback_data="set_channel")],
        [
            InlineKeyboardButton("▶️ شروع", callback_data="start_fw"),
            InlineKeyboardButton("⏸️ توقف", callback_data="stop_fw"),
        ],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("پنل مدیریت ربات", reply_markup=panel())

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global WAITING_FOR, FORWARD_ENABLED
    q = update.callback_query
    await q.answer()

    if q.data == "set_group":
        WAITING_FOR = "group"
        await q.message.reply_text("یوزرنیم گروه را ارسال کن")

    elif q.data == "set_channel":
        WAITING_FOR = "channel"
        await q.message.reply_text("یوزرنیم کانال را ارسال کن")

    elif q.data == "start_fw":
        FORWARD_ENABLED = True
        await q.message.reply_text("▶️ فروارد فعال شد")

    elif q.data == "stop_fw":
        FORWARD_ENABLED = False
        await q.message.reply_text("⏸️ فروارد متوقف شد")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global GROUP_USERNAME, CHANNEL_USERNAME, WAITING_FOR

    if not WAITING_FOR:
        return

    text = update.message.text.strip()
    if not text.startswith("@"):
        await update.message.reply_text("یوزرنیم باید با @ شروع شود")
        return

    try:
        chat = await context.bot.get_chat(text)
        member = await context.bot.get_chat_member(chat.id, context.bot.id)
        if member.status not in ("administrator", "creator"):
            await update.message.reply_text("ربات ادمین نیست")
            return

        if WAITING_FOR == "group":
            GROUP_USERNAME = text
            await update.message.reply_text("✅ گروه تنظیم شد")

        elif WAITING_FOR == "channel":
            CHANNEL_USERNAME = text
            await update.message.reply_text("✅ کانال تنظیم شد")

        WAITING_FOR = None
    except:
        await update.message.reply_text("خطا در بررسی یوزرنیم")

async def forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not FORWARD_ENABLED:
        return
    if not GROUP_USERNAME or not CHANNEL_USERNAME:
        return

    if update.effective_chat.username and f"@{update.effective_chat.username}" == GROUP_USERNAME:
        await update.message.forward(CHANNEL_USERNAME)

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_handler(MessageHandler(filters.ALL, forward))

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=WEBHOOK_URL,
    )

if __name__ == "__main__":
    main()
