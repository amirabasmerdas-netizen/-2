import os
import aiohttp
from aiohttp import web

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not BOT_TOKEN or not WEBHOOK_URL:
    raise RuntimeError("ENV variables not set")

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

GROUP_ID = None
CHANNEL_ID = None
FORWARD_ENABLED = False
WAITING_FOR = None  # group | channel


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
                {"text": "▶️ شروع فروارد", "callback_data": "start_fw"},
                {"text": "⏸️ توقف فروارد", "callback_data": "stop_fw"},
            ],
        ]
    }


# ---------- Webhook ----------
async def webhook(request):
    global GROUP_ID, CHANNEL_ID, FORWARD_ENABLED, WAITING_FOR

    update = await request.json()

    # 👇 همه نوع پیام
    message = (
        update.get("message")
        or update.get("edited_message")
        or update.get("channel_post")
        or update.get("edited_channel_post")
    )

    # ---------- Handle Messages ----------
    if message:
        chat = message["chat"]
        chat_id = chat["id"]
        text = message.get("text", "")

        # /start
        if text == "/start":
            await tg("sendMessage", {
                "chat_id": chat_id,
                "text": "🎛 پنل مدیریت ربات فروارد",
                "reply_markup": panel()
            })
            return web.Response(text="ok")

        # تنظیم گروه / کانال
        if WAITING_FOR and text.startswith("@"):
            info = await tg("getChat", {"chat_id": text})
            if not info.get("ok"):
                await tg("sendMessage", {
                    "chat_id": chat_id,
                    "text": "❌ یوزرنیم نامعتبر"
                })
                return web.Response(text="ok")

            target_id = info["result"]["id"]

            me = await tg("getMe")
            member = await tg("getChatMember", {
                "chat_id": target_id,
                "user_id": me["result"]["id"]
            })

            if member["result"]["status"] not in ("administrator", "creator"):
                await tg("sendMessage", {
                    "chat_id": chat_id,
                    "text": "❌ ربات ادمین نیست"
                })
                return web.Response(text="ok")

            if WAITING_FOR == "group":
                GROUP_ID = target_id
                await tg("sendMessage", {
                    "chat_id": chat_id,
                    "text": "✅ گروه تنظیم شد"
                })

            elif WAITING_FOR == "channel":
                CHANNEL_ID = target_id
                await tg("sendMessage", {
                    "chat_id": chat_id,
                    "text": "✅ کانال تنظیم شد"
                })

            WAITING_FOR = None
            return web.Response(text="ok")

        # ---------- Forward Logic (اصل ماجرا) ----------
        if FORWARD_ENABLED and GROUP_ID and CHANNEL_ID:
            if chat_id == GROUP_ID:
                await tg("forwardMessage", {
                    "chat_id": CHANNEL_ID,
                    "from_chat_id": GROUP_ID,
                    "message_id": message["message_id"]
                })

    # ---------- Buttons ----------
    if "callback_query" in update:
        cq = update["callback_query"]
        data = cq["data"]
        cid = cq["message"]["chat"]["id"]

        if data == "set_group":
            WAITING_FOR = "group"
            await tg("sendMessage", {
                "chat_id": cid,
                "text": "یوزرنیم گروه را بفرست"
            })

        elif data == "set_channel":
            WAITING_FOR = "channel"
            await tg("sendMessage", {
                "chat_id": cid,
                "text": "یوزرنیم کانال را بفرست"
            })

        elif data == "start_fw":
            FORWARD_ENABLED = True
            await tg("sendMessage", {
                "chat_id": cid,
                "text": "▶️ فروارد فعال شد"
            })

        elif data == "stop_fw":
            FORWARD_ENABLED = False
            await tg("sendMessage", {
                "chat_id": cid,
                "text": "⏸️ فروارد متوقف شد"
            })

        await tg("answerCallbackQuery", {"callback_query_id": cq["id"]})

    return web.Response(text="ok")


# ---------- Startup ----------
async def on_startup(app):
    await tg("setWebhook", {
        "url": WEBHOOK_URL,
        "allowed_updates": [
            "message",
            "edited_message",
            "channel_post",
            "edited_channel_post",
            "callback_query"
        ]
    })


app = web.Application()
app.router.add_post("/", webhook)
app.on_startup.append(on_startup)

if __name__ == "__main__":
    web.run_app(app, port=int(os.environ.get("PORT", 10000)))
