import asyncio
import json
import os
import sys

# Фикс кодировки для Windows консоли
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID") or os.getenv("SPOTIPY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET") or os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI") or os.getenv("SPOTIPY_REDIRECT_URI") or "http://127.0.0.1:8888/callback"

# Отладка: проверяем что переменные загрузились
print(f"CLIENT_ID set: {bool(SPOTIFY_CLIENT_ID)}")
print(f"CLIENT_SECRET set: {bool(SPOTIFY_CLIENT_SECRET)}")
print(f"TELEGRAM_BOT_TOKEN set: {bool(os.getenv('TELEGRAM_BOT_TOKEN'))}")
print(f"CHANNEL_ID: {os.getenv('TELEGRAM_CHANNEL_ID')}")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "10"))

# Если есть SPOTIFY_TOKEN_CACHE (для Railway), записываем его в файл
SPOTIFY_TOKEN_CACHE = os.getenv("SPOTIFY_TOKEN_CACHE")
CACHE_PATH = ".spotify_cache"

if SPOTIFY_TOKEN_CACHE:
    with open(CACHE_PATH, "w") as f:
        f.write(SPOTIFY_TOKEN_CACHE)

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope="user-read-currently-playing user-read-playback-state",
    cache_path=CACHE_PATH,
))

bot = Bot(token=TELEGRAM_BOT_TOKEN)

last_track_id = None


def get_current_track():
    """Получить текущий играющий трек из Spotify."""
    try:
        current = sp.current_user_playing_track()
        if current and current.get("is_playing"):
            track = current["item"]
            return {
                "id": track["id"],
                "name": track["name"],
                "artists": ", ".join(a["name"] for a in track["artists"]),
                "album": track["album"]["name"],
                "url": track["external_urls"]["spotify"],
                "image": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
            }
    except Exception as e:
        print(f"Ошибка Spotify: {e}")
    return None


async def send_to_channel(track: dict):
    """Отправить информацию о треке в Telegram-канал."""
    text = (
        f"🎵 <b>{track['name']}</b>\n"
        f"👤 {track['artists']}\n"
        f"💿 {track['album']}\n\n"
        f"<a href=\"{track['url']}\">Слушать в Spotify</a>"
    )

    if track["image"]:
        await bot.send_photo(
            chat_id=TELEGRAM_CHANNEL_ID,
            photo=track["image"],
            caption=text,
            parse_mode="HTML",
        )
    else:
        await bot.send_message(
            chat_id=TELEGRAM_CHANNEL_ID,
            text=text,
            parse_mode="HTML",
        )


async def main():
    global last_track_id
    print("Бот запущен! Отслеживаю Spotify...")

    while True:
        track = get_current_track()

        if track and track["id"] != last_track_id:
            last_track_id = track["id"]
            print(f"Новый трек: {track['artists']} - {track['name']}", flush=True)
            await send_to_channel(track)

        await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
