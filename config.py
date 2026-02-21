import os

# Get these from my.telegram.org
API_ID = int(os.environ.get("API_ID", "15994272")) 
API_HASH = os.environ.get("API_HASH", "263d77e0667afeab36319bd20f80ab2e")

# Get this from @BotFather
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8564404461:AAEAC5QuxxBDyZOTxsbNeM8PKzoVvx45pD0")

# Your Global Userbot Session (For public channels)
STRING_SESSION = os.environ.get("STRING_SESSION", "BQFYBuUAkVftQ55QQUs1ajQaKxUWme4pi_5egbyvbzObupXYBjzrQjzThrDZfw64efrdkiqyGn_KESzXoODTK-cldGLdR_frF9LzwQUmAHFM0m3u21PsRP52uEzUhaMlqd_tV8SNudre7__aAFVR_lXAGbbbBwBBy-KQqCT-8QIWYES7yfBpHHRMkBeic_n1c9emdrMSgX1Tzv4P_GwCXXN6eROzeggMlEyub8pICT-73kH7yg4ZvVtj3kxuI7HywEGdADSkL4K1AsXoNMCpD6emLsEc4mbs7SvU0fR5HcYoM2PPsJwN6rnqjFHftmAKrJUBqHBKYn5QnyRyyj0O8UHGXap26wAAAAHkhfl1AA")

# MongoDB Database URL
DB_URI = os.environ.get("DATABASE_URL", "mongodb+srv://codebyrazzesh:<AXETFpfSASQXz5Gy>@forwarder.r3d0flp.mongodb.net/?appName=forwarder")
DB_NAME = "CloneBotDB"
