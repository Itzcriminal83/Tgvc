import os
import time
import random
import urllib.parse
from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Update
from livekit import api

# --- Environment Variables ---
API_ID = int(os.environ.get("API_ID", 12345))
API_HASH = os.environ.get("API_HASH", "your_hash")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_token")
LIVEKIT_URL = os.environ.get("LIVEKIT_URL")
LIVEKIT_API_KEY = os.environ.get("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.environ.get("LIVEKIT_API_SECRET")

BOT_APP_NAME = "app"

app = FastAPI()

# Pyrogram Client Initialization
bot = Client("vc_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- BOT HANDLERS (Vercel me process karne ke liye) ---

async def handle_bot_message(message):
    """Jab koi group me message bhejega, yeh function execute hoga"""
    chat_id = message.chat.id
    text = message.text or ""

    # Command: /vc start
    if text.startswith("/vc start"):
        try:
            # Check if user is admin
            member = await bot.get_chat_member(chat_id, message.from_user.id)
            if member.status not in ["administrator", "creator"]:
                await bot.send_message(chat_id, "❌ Sirf Admins hi Voice Chat start kar sakte hain!")
                return

            group_name = message.chat.title
            safe_group_name = urllib.parse.quote(group_name)
            unique_id = f"{int(time.time())}{random.randint(100, 999)}"
            room_param = f"name_{safe_group_name}_id_{unique_id}" 
            bot_username = (await bot.get_me()).username
            
            # Link generation
            join_url = f"https://t.me/{bot_username}/{BOT_APP_NAME}?startapp={room_param}"
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🎙️ Join Voice Chat", url=join_url)]])
            
            # Send Message to group
            await bot.send_message(
                chat_id, 
                f"🎙️ **{group_name}** ka Virtual Voice Chat shuru ho gaya hai!\n\nJoin karne ke liye niche click karein:", 
                reply_markup=keyboard
            )
        except Exception as e:
            print(f"Error handling /vc start: {e}")

    # Command: /vc (For regular users)
    elif text.startswith("/vc"):
        await bot.send_message(chat_id, "ℹ️ Agar admin ne voice chat start ki hai, toh purane message ke button se join karein.")


# --- FASTAPI ENDPOINTS ---

@app.post("/api/webhook")
async def telegram_webhook(request: Request):
    """Telegram jab bhi koi naya message is URL par bhejega, ye chalu hoga"""
    try:
        if not bot.is_connected:
            await bot.start()

        # Update ko dictionary form me lena
        update_dict = await request.json()
        
        # Pyrogram me update parse karna
        update = Update.parse(bot, update_dict)
        
        # Agar update me koi naya message aaya hai
        if update and update.message:
            await handle_bot_message(update.message)
            
    except Exception as e:
        print(f"Webhook Error: {e}")
        
    return {"status": "ok"}


@app.get("/api/get-token")
async def get_token(room: str = Query(...), identity: str = Query(...), name: str = Query(...)):
    """Mini App ke liye LiveKit Token Token create karna"""
    if not bot.is_connected:
        await bot.start()
        
    token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET) \
        .with_identity(identity) \
        .with_name(name) \
        .with_grants(api.VideoGrants(room_join=True, room=room, video_less_room=True))
    
    return {"token": token.to_jwt(), "server_url": LIVEKIT_URL}
    
