from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.db import add_user, is_user_exist

@Client.on_message(filters.command("start") & filters.private)
async def send_start(app: Client, message: Message):
    if message.from_user:
        user_id = message.from_user.id
        if not await is_user_exist(user_id):
            await add_user(user_id)
    
    welcome_text = (
        "👋 **Welcome to the Ultimate Clone Bot!**\n\n"
        "I can migrate files between groups, channels, and topics."
    )
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Start Cloning", callback_data="start_clone")],
        [InlineKeyboardButton("⚙️ Userbot Settings", callback_data="userbot_settings")]
    ])
    
    await message.reply_text(welcome_text, reply_markup=buttons)

@Client.on_message(filters.command("help"))
async def send_help(app: Client, message: Message):
    await message.reply_text("Send /clone_menu to start cloning!")