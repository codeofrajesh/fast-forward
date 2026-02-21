import os
from dotenv import load_dotenv

# This tells Python to look for the hidden .env file and load the variables
load_dotenv() 

API_ID = int(os.environ.get("API_ID")) 
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
STRING_SESSION = os.environ.get("STRING_SESSION")

# Added the Database Link!
DB_URI = os.environ.get("DATABASE_URL")
DB_NAME = "CloneBotDB"