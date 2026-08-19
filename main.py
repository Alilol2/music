import os
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
import yt_dlp

# ================= الإعدادات الأساسية =================
API_ID = 34566664  # حط الـ API_ID حقك (رقم بدون تنصيص)
API_HASH = "94ba2e48816e662f5605deaf27665a44" 
BOT_TOKEN = "5988798787:AAEYIxbqtPYQxH9Ooer8kIXFEbqNRheKOkc" 
SESSION = "AQIPcggAP3nzfv36pp-RXwzZQC9b24NDtZyGJ2Ur44teisnVj-306uiGKG5sOtPKDtRK9RNTa2xg2BLgH8dXTJaPD4sRquTIAAW-QNCzAlM4e1M4yP1ZOOvyZzeQFSP0GmuidUomRe9IfB3dZzK0Ph5NFh0Rndq8bGEMjbEmZ-Tu_OK0fRFxH653QMNd38S31wRvrH9BAzbdgaY4rN9Xd2EPKhzOEqgCEQPzGP4g6hZnQlZErysuixMrpBFC-oUjVdCdQpthfn6fRN9BJ0EQj9TwiH9E6T-yLt5QVoXqP3KlY2EkL_gg1GUvy8WShia1q2h8nBTGypaEgO3vXFUBzl-FHJj3TgAAAAH85aJ8AA" 
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
    status_msg = await message.reply_text(f"⏳ ابشر، جاري البحث عن: **{query}**...")

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
            MediaStream(audio_url)
        )
        await status_msg.edit_text(f"✅ تم التشغيل في المكالمة:\n🎵 **{title}**")
        
    except Exception as e:
        print(e)
        await status_msg.edit_text("❌ حدث خطأ! تأكد إن المكالمة شغالة، والحساب المساعد موجود بالقروب كمشرف.")

# فلتر الإيقاف
@app.on_message(filters.text & filters.regex(r"^(/?ايقاف|/?stop)", re.IGNORECASE))
async def stop_music(client, message):
    try:
        await call.leave_group_call(message.chat.id)
        await message.reply_text("✅ تم إيقاف الصوت ومغادرة المكالمة.")
    except:
        await message.reply_text("❌ البوت مو موجود في المكالمة أصلاً.")

# ================= إعداد السيرفر الوهمي (عشان Render) =================
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write("بوت الأغاني شغال 100%!".encode('utf-8'))
    def log_message(self, format, *args):
        pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

if __name__ == "__main__":
    # تشغيل السيرفر الوهمي في الخلفية
    threading.Thread(target=run_server, daemon=True).start()
    
    print("🚀 جاري تشغيل بوت الصوتيات...")
    call.start()
    app.run()
