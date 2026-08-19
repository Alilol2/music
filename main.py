import os
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
import yt_dlp

# ================= الإعدادات الأساسية =================
API_ID = 34566664
API_HASH = "94ba2e48816e662f5605deaf27665a44"
BOT_TOKEN = "5988798787:AAEYIxbqtPYQxH9Ooer8kIXFEbqNRheKOkc"
SESSION = "AQIPcggATAGPbZb3yAdNAqT82JDfUK95iAV1WrRFcCu2VnodRquz5IanjQ47pGOZ7z8Z-VHeAkCoh4_aTnso_7V0xb1sx7oLAS0Zg1w1LQtMQziAqlOAX8nbQlHZmHH5jBa5sxMPOb1QgcYq4Qrb4oUKFo8QV96A2trwZ6cKTNsdQQmtF5aCz0BwOOusy9i9zvwTqdxYoBBZe3hiCvi8xl3kIybrJOq4bfU3x00EmHDadjclHv_0IxYxzqSnjzcCAc0HZAw9P_YwM4CZO9QEzjrweUhT9d6El4j44-6lGbj9qAzNmLKsLHSIwfS5n9kZ0bHkwSArvHGkbyyzPNblLVIxJG6I5gAAAAH85aJ8AA"
# ======================================================

app = Client("MusicBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user = Client("Userbot", session_string=SESSION, api_id=API_ID, api_hash=API_HASH)
call = PyTgCalls(user)

@app.on_message(filters.text & filters.regex(r"^(/?تشغيل|/?play)\s+(.+)", re.IGNORECASE))
async def play_music(client, message):
    query = message.matches[0].group(2)
    chat_id = message.chat.id
    status_msg = await message.reply_text("⏳ جاري معالجة طلبك...")

    # ================= ميزة الدخول التلقائي للمساعد =================
    try:
        await user.get_chat(chat_id)
    except Exception:
        try:
            await status_msg.edit_text("⏳ الحساب المساعد مو موجود بالقروب، جاري إضافته...")
            chat = await app.get_chat(chat_id)
            if chat.username:
                await user.join_chat(chat.username)
            else:
                invite_link = await app.export_chat_invite_link(chat_id)
                await user.join_chat(invite_link)
            await status_msg.edit_text("✅ تم دخول المساعد للقروب! جاري البحث عن المقطع...")
        except Exception as e:
            return await status_msg.edit_text("❌ ما قدرت أضيف المساعد! تأكد إني (البوت) مشرف وعندي صلاحية 'دعوة المستخدمين عبر الرابط'.")
    # ==============================================================

    try:
        # البحث والتحميل من ساوند كلاود لتخطي حظر السيرفرات
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"scsearch:{query}", download=False)['entries'][0]
            audio_url = info['url']
            title = info['title']

        await call.play(
            chat_id,
            MediaStream(audio_url)
        )
        await status_msg.edit_text(f"✅ تم التشغيل في المكالمة:\n🎵 **{title}**")
        
    except Exception as e:
        print("Error during playback:", e)
        await status_msg.edit_text("❌ حدث خطأ! تأكد من فتح المكالمة الصوتية، أو جرب تبحث باسم مختلف.")

@app.on_message(filters.text & filters.regex(r"^(/?ايقاف|/?stop)", re.IGNORECASE))
async def stop_music(client, message):
    try:
        await call.leave_call(message.chat.id)
        await message.reply_text("✅ تم إيقاف الصوت ومغادرة المكالمة.")
    except Exception:
        await message.reply_text("❌ البوت غير متصل بالمكالمة أصلاً.")

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
