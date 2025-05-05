import telebot
import yt_dlp
import re
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Telegram Bot Token (it will be set as an environment variable in Railway)
BOT_TOKEN = os.getenv('BOT_TOKEN')  # Make sure you set this in Railway environment variables
bot = telebot.TeleBot(BOT_TOKEN)

# Store video URLs temporarily
user_video_urls = {}

def is_youtube_link(text):
    return bool(re.search(r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/', text))

def create_quality_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("High Quality", callback_data="quality_high"),
        InlineKeyboardButton("Medium Quality", callback_data="quality_medium")
    )
    keyboard.row(
        InlineKeyboardButton("Low Quality", callback_data="quality_low"),
        InlineKeyboardButton("Audio Only", callback_data="quality_audio")
    )
    return keyboard

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if is_youtube_link(message.text):
        user_video_urls[message.chat.id] = message.text
        bot.reply_to(message, "Please select video quality:", reply_markup=create_quality_keyboard())
    else:
        bot.send_message(message.chat.id, "Hi 👋 Welcome to *wahabBlitz YT Downloader (A.A.W)*.\nPlease paste a valid YouTube link.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('quality_'))
def handle_quality_selection(call):
    chat_id = call.message.chat.id
    quality = call.data.split('_')[1]
    video_url = user_video_urls.get(chat_id)

    if not video_url:
        bot.answer_callback_query(call.id, "Please send the YouTube link again.")
        return

    bot.edit_message_text("⬇️ Downloading video...", chat_id, call.message.message_id)

    try:
        ydl_opts = {
            'outtmpl': f'{chat_id}_%(ext)s',
            'format': 'mp4'
        }

        if quality == 'high':
            ydl_opts['format'] = 'bestvideo+bestaudio/best'
        elif quality == 'medium':
            ydl_opts['format'] = 'best[height<=720]+bestaudio/best'
        elif quality == 'low':
            ydl_opts['format'] = 'worstvideo+bestaudio/best'
        elif quality == 'audio':
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['outtmpl'] = f'{chat_id}_audio.%(ext)s'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        if quality == 'audio':
            with open(f'{chat_id}_audio.m4a', 'rb') as audio:
                bot.send_audio(chat_id, audio)
            os.remove(f'{chat_id}_audio.m4a')
        else:
            with open(f'{chat_id}_video.mp4', 'rb') as video:
                bot.send_video(chat_id, video)
            os.remove(f'{chat_id}_video.mp4')

        del user_video_urls[chat_id]

    except Exception as e:
        bot.send_message(chat_id, f"❌ Error downloading: {str(e)}")

# Start polling
bot.infinity_polling()
