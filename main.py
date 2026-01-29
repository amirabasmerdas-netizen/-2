import os
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from aiogram.filters import CommandStart

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

bot = Bot(TOKEN)
dp = Dispatcher()

GROUP_USERNAME = None
CHANNEL_USERNAME = None
FORWARD_ENABLED = False
WAITING_FOR = None


def panel():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚙️ تنظیم گروه", callback_data="set_group")],
        [InlineKeyboardButton(text="📢 تنظیم کانال", callback_data="set_channel")],
        [
            InlineKeyboardButton(text="▶️ شروع", callback_data="start_fw"),
            InlineKeyboardButton(text="⏸️ توقف", callback_data="stop_fw"),
        ]
    ])


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("🎛 پنل مدیریت ربات", reply_markup=panel())


@dp.callback_query()
async def callbacks(call: CallbackQuery):
    global WAITING_FOR, FORWARD_ENABLED

    data = call.data
    await call.answer()

    if data == "set_group":
        WAITING_FOR = "group"
        await call.message.answer("یوزرنیم گروه رو بفرست (مثال: @mygroup)")

    elif data == "set_channel":
        WAITING_FOR = "channel"
        await call.message.answer("یوزرنیم کانال رو بفرست (مثال: @mychannel)")

    elif data == "start_fw":
        FORWARD_ENABLED = True
        await call.message.answer("▶️ فروارد فعال شد")

    elif data == "stop_fw":
        FORWARD_ENABLED = False
        await call.message.answer("⏸️ فروارد متوقف شد")


@dp.message(F.text)
async def set_usernames(message: Message):
    global GROUP_USERNAME, CHANNEL_USERNAME, WAITING_FOR

    if not WAITING_FOR:
        return

    text = message.text.strip()
    if not text.startswith("@"):
        await message.answer("❌ یوزرنیم باید با @ شروع بشه")
        return

    try:
        chat = await bot.get_chat(text)
        member = await bot.get_chat_member(chat.id, bot.id)

        if member.status not in ("administrator", "creator"):
            await message.answer("❌ ربات ادمین نیست")
            return

        if WAITING_FOR == "group":
            GROUP_USERNAME = text
            await message.answer("✅ گروه تنظیم شد")

        elif WAITING_FOR == "channel":
            CHANNEL_USERNAME = text
            await message.answer("✅ کانال تنظیم شد")

        WAITING_FOR = None

    except Exception:
        await message.answer("❌ خطا در بررسی یوزرنیم یا دسترسی")


@dp.message()
async def forward_messages(message: Message):
    if not FORWARD_ENABLED:
        return
    if not GROUP_USERNAME or not CHANNEL_USERNAME:
        return

    if message.chat.username and f"@{message.chat.username}" == GROUP_USERNAME:
        try:
            await message.forward(CHANNEL_USERNAME)
        except:
            pass


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
