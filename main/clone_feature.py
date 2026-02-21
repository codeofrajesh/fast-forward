from pyrogram import ContinuePropagation
import asyncio
import time
import re
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from pyrogram.errors import FloodWait
from bot import RazzeshUser
from config import API_ID, API_HASH
from database import db

user_sessions = {}
active_tasks = {}

# --- HELPER FUNCTIONS ---
def get_progress_bar(percentage):
    filled = int(percentage / 10)
    return "█" * filled + "░" * (10 - filled)

async def parse_chat_and_topic(link_or_id: str):
    link_or_id = link_or_id.strip()
    match_private = re.search(r"t\.me/c/(\d+)/(\d+)", link_or_id)
    if match_private: return int(f"-100{match_private.group(1)}"), int(match_private.group(2))
    match_private_chat = re.search(r"t\.me/c/(\d+)", link_or_id)
    if match_private_chat: return int(f"-100{match_private_chat.group(1)}"), None
    if link_or_id.replace("-", "").isdigit(): return int(link_or_id), None
    return link_or_id.split('/')[-1] if '/' in link_or_id else link_or_id, None

async def check_admin_rights(app: Client, chat_id, is_target=False):
    try:
        me = await app.get_me()
        async for admin in app.get_chat_members(chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
            if admin.user.id == me.id:
                if is_target:
                    if admin.status == enums.ChatMemberStatus.OWNER or (admin.privileges and admin.privileges.can_post_messages):
                        return True, "Success"
                    return False, "Bot lacks 'Post Messages' permission."
                return True, "Success"
        return False, "Bot is not in the Admin list."
    except Exception as e:
        return False, f"Error: {str(e)}"

# --- MENUS ---
@Client.on_message(filters.command("clone_menu"))
async def show_clone_menu(app: Client, message: Message):
    await message.reply_text("Select an option:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("CLONE", callback_data="start_clone")]]))

@Client.on_callback_query(filters.regex("start_clone"))
async def select_clone_type(app: Client, query: CallbackQuery):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("1. Channel", callback_data="clone_type_channel"), InlineKeyboardButton("2. Group", callback_data="clone_type_group")],
        [InlineKeyboardButton("3. Specific Topic", callback_data="clone_type_topic")],
        [InlineKeyboardButton("⚙️ USERBOT Settings", callback_data="userbot_settings")]
    ])
    await query.message.edit_text("Select source type:", reply_markup=keyboard)

@Client.on_callback_query(filters.regex("userbot_settings"))
async def userbot_menu(app: Client, query: CallbackQuery):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Session String", callback_data="add_userbot")],
        [InlineKeyboardButton("➖ Remove Session", callback_data="remove_userbot")],
        [InlineKeyboardButton("🔙 Back", callback_data="start_clone")]
    ])
    await query.message.edit_text("Manage your private cloning worker here:", reply_markup=keyboard)

# --- STATE MANAGER ---
@Client.on_callback_query(filters.regex(r"^(clone_type_|add_userbot|remove_userbot)"))
async def handle_callbacks(app: Client, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data
    
    if data == "add_userbot":
        user_sessions[user_id] = {"step": "awaiting_session_string"}
        await query.message.edit_text("Paste your Pyrogram Session String here.\n*(You can generate this using your VS Code script!)*")
    
    elif data == "remove_userbot":
        await db.remove_user_session(user_id)
        await query.answer("Session removed securely!", show_alert=True)
    
    elif data.startswith("clone_type_"):
        user_sessions[user_id] = {"step": "awaiting_source", "type": data.split("_")[2]}
        await query.message.edit_text("Send the **Source Link** or ID.")

@Client.on_message(filters.private & filters.text)
async def handle_inputs(app: Client, message: Message):
    if message.text.startswith("/"): raise ContinuePropagation
    user_id = message.from_user.id
    if user_id not in user_sessions: raise ContinuePropagation

    session = user_sessions[user_id]
    step = session["step"]

    if step == "awaiting_session_string":
        await db.set_user_session(user_id, message.text.strip())
        await message.reply_text("✅ Your personal Userbot Session has been saved securely! You can now clone from private chats.")
        del user_sessions[user_id]

    elif step == "awaiting_source":
        session["source"], session["source_topic_id"] = await parse_chat_and_topic(message.text)
        session["step"] = "awaiting_target"
        await message.reply_text("✅ Source accepted. Send the **Target Link**.")
    
    elif step == "awaiting_target":
        session["target"], session["target_topic_id"] = await parse_chat_and_topic(message.text)
        
        processing_msg = await message.reply_text("Checking permissions...")
        src_ok, src_err = await check_admin_rights(app, session["source"], is_target=False)
        tgt_ok, tgt_err = await check_admin_rights(app, session["target"], is_target=True)
        
        if not src_ok or not tgt_ok:
            await processing_msg.edit_text(f"❌ **Permission Error**\nSource: {src_err}\nTarget: {tgt_err}")
            del user_sessions[user_id]
            return

        session["step"] = "awaiting_filter"
        await processing_msg.edit_text("Select file type:", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎥 Videos", callback_data="filter_video"), InlineKeyboardButton("🖼 Photos", callback_data="filter_photo")],
            [InlineKeyboardButton("📁 Docs", callback_data="filter_document"), InlineKeyboardButton("♾ All Formats", callback_data="filter_all")]
        ]))

# --- THE CLONING ENGINE ---
@Client.on_callback_query(filters.regex(r"^filter_(.*)"))
async def start_cloning(app: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if user_id not in user_sessions: return
        
    media_filter = query.data.split("_")[1]
    session = user_sessions[user_id]
    
    src_chat = await app.get_chat(session["source"])
    tgt_chat = await app.get_chat(session["target"])
    
    status_msg = await query.message.edit_text("🔄 Initiating clone protocol...")
    
    task = asyncio.create_task(run_clone(app, user_id, session, src_chat, tgt_chat, media_filter, status_msg))
    active_tasks[user_id] = task
    del user_sessions[user_id]

async def run_clone(app, user_id, session, src_chat, tgt_chat, media_filter, status_msg):
    source_id = session["source"]
    source_topic_id = session.get("source_topic_id")
    target_id = session["target"]
    target_topic_id = session.get("target_topic_id")
    
    # DYNAMIC ROUTER: Check if the chat is Private (Integer ID) or Public (String Username)
    is_private = isinstance(source_id, int)
    scanner = None
    
    if is_private:
        user_session_string = await db.get_user_session(user_id)
        if not user_session_string:
            return await status_msg.edit_text("❌ **Private Chat Detected!**\nPlease use the '⚙️ USERBOT Settings' button to add your session string first.")
        
        await status_msg.edit_text("🔄 Booting temporary personal userbot...")
        scanner = Client(f"temp_{user_id}", api_id=API_ID, api_hash=API_HASH, session_string=user_session_string, no_updates=True)
        await scanner.start()
    else:
        scanner = RazzeshUser
        if not scanner:
            return await status_msg.edit_text("❌ Global Worker is offline. Cannot scan public chats.")

    await status_msg.edit_text("⏳ Scanning history...")
    messages_to_process = []
    
    try:
        history_iterator = scanner.get_discussion_replies(source_id, source_topic_id) if source_topic_id else scanner.get_chat_history(source_id)
        async for message in history_iterator:
            if media_filter == "all" or (media_filter == "video" and message.video) or (media_filter == "photo" and message.photo) or (media_filter == "document" and message.document):
                messages_to_process.append(message.id)
    except Exception as e:
        if is_private: await scanner.stop()
        return await status_msg.edit_text(f"❌ **Scanning Error:** {e}")

    messages_to_process.reverse() 
    total_msgs = len(messages_to_process)
    
    if total_msgs == 0:
        if is_private: await scanner.stop()
        return await status_msg.edit_text("❌ No files matching your filter were found.")

    processed = 0
    start_time = time.time()
    
    for msg_id in messages_to_process:
        try:
            await app.copy_message(chat_id=target_id, from_chat_id=source_id, message_id=msg_id, message_thread_id=target_topic_id)
            processed += 1
            await asyncio.sleep(3.2)
            
            if processed % 10 == 0 or processed == total_msgs:
                elapsed = time.time() - start_time
                speed = processed / elapsed if elapsed > 0 else 0
                eta = (total_msgs - processed) / speed if speed > 0 else 0
                percentage = (processed / total_msgs) * 100
                
                ui_text = (
                    f"**Source:** {src_chat.title}\n**Target:** {tgt_chat.title}\n━━━━━━━━━━━━━━━━━━\n"
                    f"**Processed:** {processed} / {total_msgs}\n**Speed:** {speed:.1f} msg/sec\n"
                    f"**ETA:** {time.strftime('%H:%M:%S', time.gmtime(eta))}\n\n"
                    f"`{get_progress_bar(percentage)}` {percentage:.1f}%\n*(Send /cancel to terminate)*"
                )
                await status_msg.edit_text(ui_text)
                
        except FloodWait as e:
            await asyncio.sleep(e.value + 1)
        except Exception:
            await asyncio.sleep(1)

    if is_private:
        await scanner.stop()

    await status_msg.reply_text(f"✅ **Process Completed!**\nTotal Cloned: {processed}/{total_msgs}")
    if user_id in active_tasks: del active_tasks[user_id]

@Client.on_message(filters.command("cancel"))
async def cancel_clone(app: Client, message: Message):
    user_id = message.from_user.id
    if user_id in active_tasks:
        active_tasks[user_id].cancel()
        del active_tasks[user_id]
        await message.reply_text("🛑 **Terminated.**")