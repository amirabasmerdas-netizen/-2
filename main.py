import os
import json
import aiohttp
from aiohttp import web

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not BOT_TOKEN or not WEBHOOK_URL:
    raise RuntimeError("BOT_TOKEN یا WEBHOOK_URL تنظیم نشده")

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

GROUP_USERNAME = None
CHANNEL_USERNAME = None
FORWARD_ENABLED = False
WAITING_FOR = None


# ---------- Telegram API ----------
async def tg(method, data=None):
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_URL}/{method}", json=data) as r:
            return await r.json()


# ---------- UI ----------
def panel():
    return {
        "inline_keyboard": [
            [{"text": "⚙️ تنظیم گروه", "callback_data": "set_group"}],
            [{"text": "📢 تنظیم کانال", "callback_data": "set_channel"}],
            [
                {"text": "▶️ شروع", "callback_data": "start_fw"},
                {"text": "⏸️ توقف", "callback_data": "stop_fw"},
            ],
        ]
    }


# ---------- Webhook ----------
async def webhook(request):
    global GROUP_USERNAME, CHANNEL_USERNAME, FORWARD_ENABLED, WAITING_FOR

    update = await request.json()

    # پیام
    if "message" in update:
        msg = update["message"]
        chat = msg["chat"]
        chat_id = chat["id"]

        # /start
        if msg.get("text") == "/start":
            await tg("sendMessage", {
                "chat_id": chat_id,
                "text": "🎛 پنل مدیریت ربات",
                "reply_markup": panel()
            })
            return web.Response(text="ok")

        # تنظیم یوزرنیم
        if WAITING_FOR and msg.get("text", "").startswith("@"):
            username = msg["text"]

            info = await tg("getChat", {"chat_id": username})
            if not info.get("ok"):
                await tg("sendMessage", {
                    "chat_id": chat_id,
                    "text": "❌ یوزرنیم نامعتبر"
                })
                return web.Response(text="ok")

            member = await tg("getChatMember", {
                "chat_id": username,
                "user_id": (await tg("getMe"))["result"]["id"]
            })

            if member["result"]["status"] not in ("administrator", "creator"):
                await tg("sendMessage", {
                    "chat_id": chat_id,
                    "text": "❌ ربات ادمین نیست"
                })
                return web.Response(text="ok")

            if WAITING_FOR == "group":
                GROUP_USERNAME = username
                await tg("sendMessage", {"chat_id": chat_id, "text": "✅ گروه تنظیم شد"})

            if WAITING_FOR == "channel":
                CHANNEL_USERNAME = username
                await tg("sendMessage", {"chat_id": chat_id, "text": "✅ کانال تنظیم شد"})

            WAITING_FOR = None
            return web.Response(text="ok")

        # فروارد
        if FORWARD_ENABLED and GROUP_USERNAME and CHANNEL_USERNAME:
            if chat.get("username") and f"@{chat['username']}" == GROUP_USERNAME:
                await tg("forwardMessage", {
                    "chat_id": CHANNEL_USERNAME,
                    "from_chat_id": chat_id,
                    "message_id": msg["message_id"]
                })

    # دکمه‌ها
    if "callback_query" in update:
        cq = update["callback_query"]
        data = cq["data"]
        cid = cq["message"]["chat"]["id"]

        if data == "set_group":
            WAITING_FOR = "group"
            await tg("sendMessage", {"chat_id": cid, "text": "یوزرنیم گروه را بفرست"})

        elif data == "set_channel":
            WAITING_FOR = "channel"
            await tg("sendMessage", {"chat_id": cid, "text": "یوزرنیم کانال را بفرست"})

        elif data == "start_fw":
            FORWARD_ENABLED = True
            await tg("sendMessage", {"chat_id": cid, "text": "▶️ فروارد فعال شد"})

        elif data == "stop_fw":
            FORWARD_ENABLED = False
            await tg("sendMessage", {"chat_id": cid, "text": "⏸️ فروارد متوقف شد"})

        await tg("answerCallbackQuery", {"callback_query_id": cq["id"]})

    return web.Response(text="ok")


# ---------- Startup ----------
async def on_startup(app):
    await tg("setWebhook", {"url": WEBHOOK_URL})


app = web.Application()
app.router.add_post("/", webhook)
app.on_startup.append(on_startup)

if __name__ == "__main__":
    web.run_app(app, port=int(os.environ.get("PORT", 10000)))
