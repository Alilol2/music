import os
import re  # <--- هذا هو السطر اللي نسيته وسبب المشكلة!
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
import yt_dlp

# ================= الإعدادات الأساسية =================
API_ID = 34566664
API_HASH = "94ba2e48816e662f5605deaf27665a44"
BOT_TOKEN = "5988798787:AAFwDzeX-aGiPDMpn6M3zF3VOK5bxmX5ZGg"
SESSION = "AQIPcggATAGPbZb3yAdNAqT82JDfUK95iAV1WrRFcCu2VnodRquz5IanjQ47pGOZ7z8Z-VHeAkCoh4_aTnso_7V0xb1sx7oLAS0Zg1w1LQtMQziAqlOAX8nbQlHZmHH5jBa5sxMPOb1QgcYq4Qrb4oUKFo8QV96A2trwZ6cKTNsdQQmtF5aCz0BwOOusy9i9zvwTqdxYoBBZe3hiCvi8xl3kIybrJOq4bfU3x00EmHDadjclHv_0IxYxzqSnjzcCAc0HZAw9P_YwM4CZO9QEzjrweUhT9d6El4j44-6lGbj9qAzNmLKsLHSIwfS5n9kZ0bHkwSArvHGkbyyzPNblLVIxJG6I5gAAAAH85aJ8AA"
# ======================================================

app = Client("MusicBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user = Client("Userbot", session_string=SESSION, api_id=API_ID, api_hash=API_HASH)
call = PyTgCalls(user)

def format_duration(seconds):
    if not seconds: 
        return "0:00"
    seconds = int(seconds)
    m = seconds // 60
    s = seconds % 60
    return f"{m}:{s:02d}"

@app.on_message(filters.text & filters.regex(r"^(/?تشغيل|/?play)\s+(.+)", re.IGNORECASE))
async def play_music(client, message):
    query = message.matches[0].group(2)
    chat_id = message.chat.id
    user_mention = message.from_user.mention
    
    status_msg = await message.reply_text("⏳ جاري معالجة طلبك من يوتيوب...")

    try:
        await user.get_chat(chat_id)
    except Exception:
        try:
            await status_msg.edit_text("⏳ الحساب المساعد غير موجود بالقروب، جاري إضافته...")
            chat = await app.get_chat(chat_id)
            if chat.username:
                await user.join_chat(chat.username)
            else:
                invite_link = await app.export_chat_invite_link(chat_id)
                await user.join_chat(invite_link)
            await status_msg.edit_text("✅ تم دخول المساعد. جاري البحث في يوتيوب...")
        except Exception as e:
            return await status_msg.edit_text(f"❌ لم أتمكن من إضافة المساعد. تأكد أن البوت مشرف.\nالخطأ: `{e}`")

    try:
        # العودة ליوتيوب مع كود التخطي
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'extractor_args': {'youtube': ['client=ANDROID_MUSIC', 'player_client=android']}
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
            audio_url = info['url']
            title = info['title']
            thumbnail = info.get('thumbnail')
            duration_sec = info.get('duration', 0)
            duration_str = format_duration(duration_sec)

        await call.play(
            chat_id,
            MediaStream(audio_url)
        )

        caption = (
            "| - تم بدء التشغيل\n\n"
            f"• العنوان : {title}\n"
            f"• مدة التشغيل : {duration_str}\n"
            "-\n"
            f"• طلب بواسطة : {user_mention}"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("مؤقت", callback_data="pause"),
                InlineKeyboardButton("استئناف", callback_data="resume"),
                InlineKeyboardButton("إيقاف", callback_data="stop")
            ],
            [
                InlineKeyboardButton(f"0:00 ───────◯────── {duration_str}", callback_data="none")
            ],
            [
                InlineKeyboardButton("تحديثات ماريا", url="https://t.me/suooc")
            ]
        ])

        if thumbnail:
            await message.reply_photo(photo=thumbnail, caption=caption, reply_markup=keyboard)
            await status_msg.delete()
        else:
            await status_msg.edit_text(text=caption, reply_markup=keyboard)
        
    except Exception as e:
        error_str = str(e)
        if "Sign in to confirm" in error_str:
            error_str = "يوتيوب قام بحظر سيرفرات المنصة مؤقتاً. (حماية يوتيوب)."
        await status_msg.edit_text(f"❌ حدث خطأ:\n`{error_str}`")

@app.on_message(filters.text & filters.regex(r"^(/?ايقاف|/?stop)", re.IGNORECASE))
async def stop_music_cmd(client, message):
    try:
        await call.leave_call(message.chat.id)
        await message.reply_text("✅ تم إيقاف الصوت ومغادرة المكالمة.")
    except Exception:
        await message.reply_text("❌ البوت غير متصل بالمكالمة.")

@app.on_callback_query()
async def handle_callbacks(client, query: CallbackQuery):
    chat_id = query.message.chat.id
    data = query.data

    if data == "none":
        return await query.answer()

    try:
        if data == "pause":
            await call.pause(chat_id)
            await query.answer("تم إيقاف المقطع مؤقتاً")
        elif data == "resume":
            await call.resume(chat_id)
            await query.answer("تم استئناف المقطع")
        elif data == "stop":
            await call.leave_call(chat_id)
            await query.answer("تم إيقاف التشغيل")
            await query.message.delete()
    except Exception:
        await query.answer("حدث خطأ أو البوت غير متصل", show_alert=True)

class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write("البوت شغال 100%".encode('utf-8'))
    def log_message(self, format, *args):
        pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

async def start_services():
    print("🚀 جاري تشغيل البوت والمساعد...")
    await app.start()
    await user.start()
    await call.start()
    print("✅ تم التشغيل بنجاح، البوت والمساعد جاهزين!")
    await idle()

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    app.run(start_services())
