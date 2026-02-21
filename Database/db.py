import motor.motor_asyncio
from config import DB_URI, DB_NAME

client = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
db = client[DB_NAME]
user_data = db.users

async def is_user_exist(user_id):
    user = await user_data.find_one({'id': user_id})
    return True if user else False

async def add_user(user_id):
    if not await is_user_exist(user_id):
        await user_data.insert_one({'id': user_id})

async def set_user_session(user_id, session_string):
    # Saves or updates the user's personal session string
    await user_data.update_one({'id': user_id}, {'$set': {'session': session_string}}, upsert=True)

async def get_user_session(user_id):
    user = await user_data.find_one({'id': user_id})
    return user.get('session') if user else None

async def remove_user_session(user_id):
    await user_data.update_one({'id': user_id}, {'$unset': {'session': ""}})