import logging
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN, STRING_SESSION

logging.basicConfig(level=logging.INFO)

# --- GLOBAL WORKER (For Public Chats) ---
RazzeshUser = None
if STRING_SESSION:
    try:
        RazzeshUser = Client(
            "GlobalWorker", 
            api_id=API_ID, 
            api_hash=API_HASH, 
            session_string=STRING_SESSION,
            no_updates=True
        )
    except Exception as e:
        print(f"❌ Global Userbot Error: {e}")

class Bot(Client):
    def __init__(self):
        super().__init__(
            "CloneBot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="main"),
            workers=150
        )

    async def start(self):
        await super().start()
        if RazzeshUser:
            await RazzeshUser.start()
            print("✅ Global Userbot Worker Linked!")
        print('✅ Bot is Online!')

    async def stop(self, *args):
        await super().stop()
        if RazzeshUser:
            await RazzeshUser.stop()
        print('🛑 Bot Stopped.')

if __name__ == "__main__":
    bot = Bot()
    bot.run()