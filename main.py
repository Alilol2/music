import os
import re
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped
import yt_dlp

# ================= الإعدادات الأساسية =================
API_ID = 12345678  # ضع الـ API_ID الخاص بك هنا كـ int
API_HASH = "أضف_الهاش_هنا" 
BOT_TOKEN = "توكن_البوت_الجديد" 
SESSION = "كود_الجلسة_SESSION_STRING" 
# ======================================================

# إعداد البوت والحساب المساعد
app = Client("MusicBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user = Client("Userbot", session_string=SESSION, api_id=API_ID, api_hash=API_HASH)
call = PyTgCalls(user)

# فلتر تشغيل الأغاني
@app.on_message(filters.text & filters.regex(r"^(/?تشغيل|/?play)\s+(.+)", re.IGNORECASE))
async def play_music(client, message):
    query = message.matches[0].group(2)
    chat_id = message.chat.id
    status_msg = await message.reply_text(f"⏳ جاري البحث عن: **{query}**...")

    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
            audio_url = info['url']
            title = info['title']

        await call.join_group_call(
            chat_id,
            AudioPiped(audio_url)
        )
        await status_msg.edit_text(f"✅ تم التشغيل في المكالمة:\n🎵 **{title}**")
        
    except Exception as e:
        print("Error during playback:", e)
        await status_msg.edit_text("❌ حدث خطأ! تأكد من بدء المكالمة ووجود الحساب المساعد كمشرف.")

# فلتر الإيقاف
@app.on_message(filters.text & filters.regex(r"^(/?ايقاف|/?stop)", re.IGNORECASE))
async def stop_music(client, message):
    try:
        await call.leave_group_call(message.chat.id)
        await message.reply_text("✅ تم إيقاف الصوت ومغادرة المكالمة.")
    except Exception:
        await message.reply_text("❌ البوت غير متصل بالمكالمة.")

# ================= خادم الويب الوهمي للحفاظ على السيرفر =================
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write("بوت المكالمات شغال 100%!".encode('utf-8'))

    def log_message(self, format, *args):
        pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    print("🚀 جاري تشغيل بوت الصوتيات...")
    call.start()
    app.run()
