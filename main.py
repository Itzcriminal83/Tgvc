import os
import time
import random
import urllib.parse
import asyncio
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from livekit import api

# --- Configuration (Railway Variables Se Load Hoga) ---
API_ID = int(os.environ.get("API_ID", 12345))
API_HASH = os.environ.get("API_HASH", "your_api_hash")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_bot_token")

LIVEKIT_URL = os.environ.get("LIVEKIT_URL")
LIVEKIT_API_KEY = os.environ.get("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.environ.get("LIVEKIT_API_SECRET")

# App name jo aap BotFather me set karenge (jaise 'app')
BOT_APP_NAME = "app" 

app = FastAPI()
bot = Client("vc_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@bot.on_message(filters.command("vc start") & filters.group)
async def start_vc(client, message):
    chat_id = message.chat.id
    member = await client.get_chat_member(chat_id, message.from_user.id)
    
    if member.status not in ["administrator", "creator"]:
        await message.reply_text("❌ Sirf Admins hi Voice Chat start kar sakte hain!")
        return

    group_name = message.chat.title
    safe_group_name = urllib.parse.quote(group_name)
    unique_id = f"{int(time.time())}{random.randint(100, 999)}"
    
    # Format: name_Group%20Name_id_12345678
    room_param = f"name_{safe_group_name}_id_{unique_id}" 
    bot_username = (await client.get_me()).username
    
    # Exact URL format jo aapne manga tha
    join_url = f"https://t.me/{bot_username}/{BOT_APP_NAME}?startapp={room_param}"
    
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🎙️ Join Voice Chat", url=join_url)]])
    await message.reply_text(f"🎙️ **{group_name}** ka Virtual Voice Chat shuru ho gaya hai!\n\nJoin karne ke liye niche click karein:", reply_markup=keyboard)

@app.get("/get-token")
async def get_token(room: str = Query(...), identity: str = Query(...), name: str = Query(...)):
    token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET) \
        .with_identity(identity) \
        .with_name(name) \
        .with_grants(api.VideoGrants(room_join=True, room=room, video_less_room=True))
    
    return {"token": token.to_jwt(), "server_url": LIVEKIT_URL}

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(bot.start())

@app.on_event("shutdown")
async def shutdown_event():
    await bot.stop()
  
