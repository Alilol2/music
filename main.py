import os
import json
import asyncio
import random
import time
import html
from datetime import datetime, timedelta
import nest_asyncio
from g4f.client import Client
from telegram import Update, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ChatMemberHandler, CallbackQueryHandler
from http.server import BaseHTTPRequestHandler, HTTPServer
import threadingimport os
import json
import asyncio
import random
import time
import html
from datetime import datetime, timedelta
import nest_asyncio
from g4f.client import Client
from telegram import Update, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ChatMemberHandler, CallbackQueryHandler
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# تفعيل التوافق مع بيئة الاستضافات السحابية
nest_asyncio.apply()

# ================= الإعدادات الأساسية =================
TOKEN = "5845566822:AAGJGPGclHybO3r-0mL1I9kGDxduR7R6nr8"
DEVELOPER_ID = 5543325412
BOT_NAME = "ماريا"
DEV_NAME = "محمد الهاشمي"
DEV_BIO = "Software Developer"
# =======================================================

ai_client = Client()
DATA_FILE = 'data.json'

# قواميس حفظ حالات المستخدمين
adding_reply_state = {}
changing_word_state = {}
creating_button_state = {}
adding_alias_state = {}
changing_template_state = {}

active_word_game = {}
active_math_game = {}
active_tafkik_game = {}
active_tarkib_game = {}
active_capitals_game = {}
active_speed_game = {}
xo_games = {}
pending_whispers = {}

CAPITALS = {
    "السعودية": "الرياض", "مصر": "القاهرة", "الامارات": "ابوظبي", "الكويت": "الكويت",
    "قطر": "الدوحة", "البحرين": "المنامة", "عمان": "مسقط", "سوريا": "دمشق",
    "فلسطين": "القدس", "العراق": "بغداد", "اليمن": "صنعاء", "فرنسا": "باريس",
    "بريطانيا": "لندن", "ايطاليا": "روما", "اسبانيا": "مدريد", "المانيا": "برلين"
}

CUT_TWEET = ["وش طموحك بالحياة؟", "عمرك ندمت على معرفة شخص؟", "تفضل الشاي ولا القهوة؟", "أكثر تطبيق تستخدمه؟", "كلمة لشخص ببالك؟"]
SARAHA = ["متى آخر مرة بكيت؟", "أكبر كذبة كذبتها؟", "مين أقرب شخص لقلبك؟", "شيء تخاف منه؟"]
KHYROK = ["تخسر كل فلوسك أو تخسر أعز أصدقائك؟", "تطير ولا تختفي؟", "تاكل بيتزا طول عمرك ولا شاورما؟"]
EQAB = ["ارسل آخر صورة بجوالك", "اعترف بشيء غبي سويته بالقروب", "اكتب انا غبي 10 مرات", "أرسل نكتة سامجة"]

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # التأكد من وجود كل الأقسام
            for k in ["custom_replies", "group_replies", "msg_count", "bank", "group_games", "group_msgs", "group_names", "user_names", "link_disabled", "settings", "word_replacements", "whispers", "command_aliases", "chat_settings", "marriages", "chat_templates", "global_templates"]:
                if k not in data: data[k] = {}
            if "stats" not in data: data["stats"] = {"users": [], "groups": []}
            if "market" not in data: data["market"] = {"price": 100, "last_update": 0}
            if "game_words" not in data: data["game_words"] = ["مدرسة", "تليجرام", "سيارة", "مبرمج", "هاكر"]
            if "top_btn" not in data["settings"]: data["settings"]["top_btn"] = {"text": "اخفاء التوب", "emoji": ""}
            return data

    return {
        "roles": {}, "muted": {}, "custom_replies": {}, "group_replies": {}, "msg_count": {},
        "stats": {"users": [], "groups": []}, "bank": {}, "market": {"price": 100, "last_update": 0},
        "group_games": {}, "group_msgs": {}, "group_names": {}, "user_names": {},
        "link_disabled": {}, "game_words": ["مدرسة", "تليجرام", "سيارة", "برمجة", "حماية"],
        "settings": {"top_btn": {"text": "اخفاء التوب", "emoji": ""}}, "word_replacements": {},
        "whispers": {}, "command_aliases": {}, "chat_settings": {}, "marriages": {}, "chat_templates": {}, "global_templates": {}
    }

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = load_data()

# دالة ذكية لإرسال الرسائل تدعم الرموز المتحركة (HTML) بأمان
async def safe_reply(message_obj, text, **kwargs):
    try:
        return await message_obj.reply_text(text, parse_mode="HTML", **kwargs)
    except Exception:
        return await message_obj.reply_text(text, **kwargs)

async def safe_reply_photo(message_obj, photo, caption, **kwargs):
    try:
        return await message_obj.reply_photo(photo, caption=caption, parse_mode="HTML", **kwargs)
    except Exception:
        return await message_obj.reply_photo(photo, caption=caption, **kwargs)

def t(text):
    if not isinstance(text, str): return text
    for old_w, new_w in db.get("word_replacements", {}).items():
        text = text.replace(old_w, new_w)
    return text

ROLES = {"Dev": 6, "مالك اساسي": 5, "مالك": 4, "مدير": 3, "ادمن": 2, "مميز": 1, "عضو": 0}
ITEMS_PRICES = {"سيارة": 1000000, "ماسة": 5000000, "قصر": 15000000}
WHEEL_COST = 5000000

def get_user_role(chat_id, user_id):
    if str(user_id) == str(DEVELOPER_ID): return "Dev"
    chat_id, user_id = str(chat_id), str(user_id)
    if chat_id in db["roles"] and user_id in db["roles"][chat_id]:
        return db["roles"][chat_id][user_id]
    return "عضو"

def check_jail(user_id):
    u_bank = db["bank"].get(str(user_id))
    if not u_bank: return False
    if u_bank.get("is_jailed"): return True
    if u_bank.get("loan_due", 0) > 0 and time.time() > u_bank["loan_due"]:
        u_bank["is_jailed"] = True
        save_data(db)
        return True
    return False

def get_multiplier(user_id):
    u_bank = db["bank"].get(str(user_id))
    if u_bank and u_bank.get("x2_expiry", 0) > time.time(): return 2
    return 1

def win_game(uid, amount):
    if uid in db["bank"]:
        prize = amount * get_multiplier(uid)
        db["bank"][uid]["balance"] += prize
        save_data(db)
        return prize
    return 0

async def delete_after(message, seconds):
    await asyncio.sleep(seconds)
    try: await message.delete()
    except Exception: pass

def generate_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("الالعاب", callback_data="cmd_games"), InlineKeyboardButton("البنك", callback_data="cmd_bank")],
        [InlineKeyboardButton("الحماية", callback_data="cmd_protect"), InlineKeyboardButton("الادارة", callback_data="cmd_admin")],
        [InlineKeyboardButton("العامة", callback_data="cmd_general"), InlineKeyboardButton("المطور", callback_data="cmd_dev")],
        [InlineKeyboardButton("اغلاق القائمة", callback_data="hide_top")]
    ])

def generate_xo_board(game_id):
    board = xo_games[game_id]["board"]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(board[0], callback_data=f"xo_{game_id}_0"), InlineKeyboardButton(board[1], callback_data=f"xo_{game_id}_1"), InlineKeyboardButton(board[2], callback_data=f"xo_{game_id}_2")],
        [InlineKeyboardButton(board[3], callback_data=f"xo_{game_id}_3"), InlineKeyboardButton(board[4], callback_data=f"xo_{game_id}_4"), InlineKeyboardButton(board[5], callback_data=f"xo_{game_id}_5")],
        [InlineKeyboardButton(board[6], callback_data=f"xo_{game_id}_6"), InlineKeyboardButton(board[7], callback_data=f"xo_{game_id}_7"), InlineKeyboardButton(board[8], callback_data=f"xo_{game_id}_8")]
    ])

def check_xo_win(board):
    lines = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
    for a, b, c in lines:
        if board[a] == board[b] == board[c] and board[a] != "-": return board[a]
    if "-" not in board: return "Draw"
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if args and args[0].startswith("w_"):
        w_id = args[0][2:]
        if w_id in db["whispers"]:
            if db["whispers"][w_id]["from_id"] == str(update.message.from_user.id):
                pending_whispers[update.message.from_user.id] = w_id
                await safe_reply(update.message, t("اكتب همستك الحين:"))
                return
    await safe_reply(update.message, t(f"هلا ومرحبا بك في بوت {BOT_NAME}"))

def get_fast_ai_response(prompt):
    try:
        response = ai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "أنت مساعد ذكي تسولف باللهجة السعودية البحتة والعامية وبأسلوب عفوي وسريع. ممنوع استخدام أي رموز تعبيرية."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.replace("*", "").replace("`", "").strip()
    except Exception:
        return "ابشر بس فيه ضغط بسيط جرب ثانية"

def format_reply_text(text, user, chat_id="المجموعة"):
    name = html.escape(user.first_name or "المستخدم")
    username = html.escape(f"@{user.username}" if user.username else "بدون يوزر")
    msg_cnt = db["msg_count"].get(str(user.id), 1)
    role = get_user_role(chat_id, user.id)
    pts = db['bank'].get(str(user.id), {}).get('balance', 0)
    return text.replace("#الاسم", name).replace("#يوزره", username).replace("#اليوزر", username).replace("#الايدي", str(user.id)).replace("#الرتبة", str(role)).replace("#الرسائل", str(msg_cnt)).replace("#النقاط", str(pts))

async def track_bot_joins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.my_chat_member
    if result.new_chat_member.status in ["member", "administrator"]:
        chat = result.chat
        if str(chat.id) not in db["stats"]["groups"]:
            db["stats"]["groups"].append(str(chat.id))
            save_data(db)
        link = "الرابط غير متوفر"
        if result.new_chat_member.status == "administrator":
            try: link = await context.bot.export_chat_invite_link(chat.id)
            except Exception: pass
        msg = f"تمت اضافة البوت لمجموعة جديدة\nاسم المجموعة: {chat.title}\nرابط المجموعة: {link}\n\nعدد المجموعات: {len(db['stats']['groups'])}"
        await context.bot.send_message(chat_id=DEVELOPER_ID, text=t(msg))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    data = query.data

    if data == "hide_top":
        try:
            await query.answer()
            await query.message.delete()
        except Exception: pass
        return

    # --- لعبة اكس او ---
    if data.startswith("xo_"):
        parts = data.split("_")
        game_id, pos = parts[1], int(parts[2])

        if game_id not in xo_games:
            return await query.answer("اللعبة هذي منتهية او محذوفة.", show_alert=True)
        game = xo_games[game_id]
        if user_id not in [game["p1"], game["p2"]]:
            return await query.answer("اللعبة مو لك، لا تتدخل!", show_alert=True)
        if user_id != game["turn"]:
            return await query.answer("مو دورك، انتظر!", show_alert=True)
        if game["board"][pos] != "-":
            return await query.answer("المكان محجوز، اختر غيره.", show_alert=True)

        game["board"][pos] = "X" if user_id == game["p1"] else "O"
        win_result = check_xo_win(game["board"])

        if win_result:
            if win_result == "Draw": msg = "انتهت اللعبة بالتعادل!"
            else:
                winner_id = game["p1"] if win_result == "X" else game["p2"]
                winner_name = game["p1_name"] if win_result == "X" else game["p2_name"]
                prize = win_game(winner_id, 10000)
                msg = f"انتهت اللعبة بفوز {winner_name}!\nحصل على جائزة {prize} ريال."
            
            try: await query.message.edit_text(t(msg), reply_markup=generate_xo_board(game_id), parse_mode="HTML")
            except: await query.message.edit_text(t(msg), reply_markup=generate_xo_board(game_id))
            del xo_games[game_id]
            return

        game["turn"] = game["p2"] if user_id == game["p1"] else game["p1"]
        next_turn_name = game["p2_name"] if user_id == game["p1"] else game["p1_name"]
        msg = f"لعبة اكس او مستمرة\nالدور الان على: {next_turn_name}"
        try: await query.message.edit_text(t(msg), reply_markup=generate_xo_board(game_id), parse_mode="HTML")
        except: await query.message.edit_text(t(msg), reply_markup=generate_xo_board(game_id))
        return

    # --- قوائم الأوامر ---
    menus = {
        "cmd_main": "اهلا بك في قائمة اوامر ماريا\nاختر القسم اللي تبيه:",
        "cmd_games": "<b>اوامر الالعاب:</b>\n- سرعة\n- اكس او [بالرد]\n- كلمات\n- رياضيات\n- عواصم\n- كت / صراحة / عقاب\n- زواج [بالرد] / طلاق\n- زوجي\n- توب المتفاعلين",
        "cmd_bank": "<b>اوامر البنك:</b>\n- راتب\n- زرف [بالرد]\n- حظ / العجله\n- شراء / بيع\n- قرض\n- فلوسي\n- ممتلكاتي",
        "cmd_protect": "<b>اوامر الحماية:</b>\n- قفل الروابط / فتح الروابط\n- قفل الصور / قفل الملصقات\n- قفل التوجيه",
        "cmd_admin": "<b>الادارة:</b>\n- حظر / طرد / كتم / تقييد [بالرد]\n- رفع / تنزيل\n- تغيير كليشة الايدي\n- تغيير كليشة الاوامر\n- اضف رد / حذف رد",
        "cmd_general": "<b>العامة:</b>\n- ايدي\n- معلوماتي\n- رتبتي\n- الوقت / التاريخ\n- اهمس / ه [بالرد]\n- الرابط",
        "cmd_dev": "<b>المطور:</b>\n- اضف امر\n- تغير كلمه\n- تغيير كليشة الايدي عام\n- تغيير كليشة الاوامر عام\n- اضف رد عام / حذف رد عام\n- صنع زر"
    }

    if data in menus:
        if data == "cmd_dev" and user_id != str(DEVELOPER_ID):
            return await query.answer(t("معليش، هذا القسم خاص بالمطور فقط!"), show_alert=True)
        await query.answer()
        reply_m = generate_menu_keyboard() if data == "cmd_main" else InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="cmd_main")]])
        try: await query.message.edit_text(t(menus[data]), reply_markup=reply_m, parse_mode="HTML")
        except: await query.message.edit_text(t(menus[data]), reply_markup=reply_m)
        return

    # --- نظام الهمسات بالأزرار ---
    if data.startswith("sw_"):
        w_id = data[3:]
        if w_id in db.get("whispers", {}):
            whisper = db["whispers"][w_id]
            if user_id in [whisper["from_id"], whisper["to_id"]]:
                return await query.answer(text=whisper["text"], show_alert=True)
            return await query.answer(text=t("الهمسة مو لك، لا تتدخل"), show_alert=True)
        return await query.answer(text=t("الهمسة هذي محذوفة"), show_alert=True)

    if data.startswith("rw_"):
        parts = data.split("_", 2)
        if len(parts) >= 3:
            w_id = str(random.randint(100000, 999999))
            bot_info = await context.bot.get_me()
            db["whispers"][w_id] = {
                "from_id": user_id, "from_name": query.from_user.first_name,
                "to_id": parts[1], "to_name": parts[2],
                "chat_id": str(query.message.chat.id), "text": ""
            }
            save_data(db)
            btn_url = f"https://t.me/{bot_info.username}?start=w_{w_id}"
            await context.bot.send_message(
                chat_id=query.message.chat.id,
                text=t(f"تم تحديد الهمسه لـ {parts[2]}\nاضغط الزر لكتابة الهمسة"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t("اهمس هنا"), url=btn_url)]])
            )
            await query.answer()

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.from_user: return

    chat_id = str(update.message.chat_id)
    user = update.message.from_user
    user_id_int, user_id = user.id, str(user.id)

    issuer_role = get_user_role(chat_id, user_id_int)
    issuer_weight = ROLES[issuer_role]

    raw_text = update.message.text or update.message.caption
    if not raw_text: return
    text = raw_text.strip()
    html_text = update.message.text_html or update.message.caption_html or text

    # --- نظام الحماية ---
    if update.message.chat.type in ['group', 'supergroup'] and issuer_weight < ROLES["مميز"]:
        if chat_id not in db.get("chat_settings", {}):
            db.setdefault("chat_settings", {})[chat_id] = {"links": False, "photos": False, "stickers": False, "forwards": False}

        c_set = db["chat_settings"][chat_id]
        must_delete, reason = False, ""
        if c_set.get("photos") and update.message.photo: must_delete, reason = True, "الصور"
        elif c_set.get("stickers") and update.message.sticker: must_delete, reason = True, "الملصقات"
        elif c_set.get("forwards") and update.message.forward_date: must_delete, reason = True, "التوجيه"
        
        if c_set.get("links") and ("http://" in text or "https://" in text or "t.me/" in text):
            must_delete, reason = True, "الروابط"

        if must_delete:
            try:
                await update.message.delete()
                warning_msg = await safe_reply(update.message, t(f"عذرا {user.first_name}، يمنع ارسال {reason} هنا."))
                asyncio.create_task(delete_after(warning_msg, 5))
            except Exception: pass
            return

    # --- استقبال الهمسة في الخاص ---
    if update.message.chat.type == "private":
        if user_id_int in pending_whispers:
            w_id = pending_whispers[user_id_int]
            if w_id in db.get("whispers", {}):
                db["whispers"][w_id]["text"] = text
                save_data(db)
                whisper = db["whispers"][w_id]
                keyboard = [
                    [InlineKeyboardButton(t("رؤية الهمسة"), callback_data=f"sw_{w_id}")],
                    [InlineKeyboardButton(t(f"اهمس لـ {whisper['from_name']}"), callback_data=f"rw_{whisper['from_id']}_{whisper['from_name']}")]
                ]
                try:
                    await context.bot.send_message(chat_id=whisper["chat_id"], text=t(f"الهمسه لـ {whisper['to_name']}\nمن {whisper['from_name']}"), reply_markup=InlineKeyboardMarkup(keyboard))
                    await safe_reply(update.message, t("تم ارسال الهمسة بنجاح!"))
                except Exception:
                    await safe_reply(update.message, t("فشلت عملية ارسال الهمسة."))
                del pending_whispers[user_id_int]
                return

    # تحديث إحصائيات 
    db["user_names"][user_id] = user.first_name
    if update.message.chat.type in ['group', 'supergroup']:
        if chat_id not in db["group_msgs"]: db["group_msgs"][chat_id] = {}
        db["group_names"][chat_id] = update.message.chat.title
        db["group_msgs"][chat_id][user_id] = db["group_msgs"][chat_id].get(user_id, 0) + 1

    if user_id not in db["stats"]["users"]: db["stats"]["users"].append(user_id)
    if chat_id not in db["stats"]["groups"] and update.message.chat.type in ['group', 'supergroup']:
        db["stats"]["groups"].append(chat_id)

    db["msg_count"][user_id] = db["msg_count"].get(user_id, 0) + 1
    save_data(db)

    # فحص الكتم
    if chat_id in db["muted"] and user_id in db["muted"][chat_id]:
        try: await update.message.delete()
        except Exception: pass
        return

    # --- اختصارات الأوامر ---
    aliases = db.get("command_aliases", {})
    if text in aliases: text = aliases[text]
    else:
        for alias, orig in aliases.items():
            if text.startswith(alias + " "):
                text = orig + text[len(alias):]
                break
    text_normalized = text.replace("إلغاء", "الغاء").replace("فك ", "الغاء ")

    # ------------------ الأوامر العامة والرئيسية ------------------
    if text == "رتبتي":
        await safe_reply(update.message, t(f"رتبتك في هذه المجموعة هي: <b>{issuer_role}</b>"))
        return
        
    if text == "معلوماتي":
        msg = f"<b>معلوماتك الشخصية:</b>\nالاسم: {user.first_name}\nاليوزر: @{user.username if user.username else 'لا يوجد'}\nالايدي: <code>{user.id}</code>\nرتبتك بالقروب: {issuer_role}\nرسائلك: {db['msg_count'].get(str(user.id), 1)}\nرصيدك البنكي: {db['bank'].get(str(user.id), {}).get('balance', 0)} ريال"
        await safe_reply(update.message, t(msg))
        return

    if text.lower() in ["ايدي", "ا", "id"]:
        user_photos = await context.bot.get_user_profile_photos(user.id, limit=1)
        
        id_template = db.get("chat_templates", {}).get(chat_id, {}).get("id")
        if not id_template:
            id_template = db.get("global_templates", {}).get("id", "iD: <code>#الايدي</code>\nName: #الاسم\nUser Name: #يوزره\nRank: #الرتبة\nMsg: #الرسائل")
            
        caption = format_reply_text(id_template, user, chat_id)
        if user_photos.total_count > 0:
            await safe_reply_photo(update.message, user_photos.photos[0][-1].file_id, t(caption))
        else:
            await safe_reply(update.message, t(caption))
        return

    if text in ["الاوامر", "اوامري", "م", "أوامر"]:
        cmd_template = db.get("chat_templates", {}).get(chat_id, {}).get("commands")
        if not cmd_template:
            cmd_template = db.get("global_templates", {}).get("commands", "اهلا بك في قائمة اوامر ماريا\nاختر القسم اللي تبيه:")
            
        formatted_cmd = format_reply_text(cmd_template, user, chat_id)
        await safe_reply(update.message, t(formatted_cmd), reply_markup=generate_menu_keyboard())
        return

    # ------------------ نظام تغير كلمة واختصار الاوامر ------------------
    if user_id_int in adding_alias_state:
        state = adding_alias_state[user_id_int]
        if state.get("step") == "waiting_for_old_cmd":
            state["old_cmd"] = text
            state["step"] = "waiting_for_new_cmd"
            await safe_reply(update.message, t("ممتاز، الحين ارسل الاختصار اللي تبيه:"))
            return
        elif state.get("step") == "waiting_for_new_cmd":
            db["command_aliases"][text] = state["old_cmd"]
            save_data(db)
            del adding_alias_state[user_id_int]
            await safe_reply(update.message, t(f"تم بنجاح! تقدر تستخدم '{text}' بدال '{state['old_cmd']}'."))
            return

    if text == "اضف امر":
        if issuer_weight < ROLES["مالك"]: return await safe_reply(update.message, t("للمالك والمطور فقط"))
        adding_alias_state[user_id_int] = {"step": "waiting_for_old_cmd"}
        await safe_reply(update.message, t("ارسل الأمر الأساسي (مثلاً: حظر)"))
        return

    if user_id_int in changing_word_state:
        state = changing_word_state[user_id_int]
        if state.get("step") == "waiting_for_old_word":
            state["old_word"] = text
            state["step"] = "waiting_for_new_word"
            await safe_reply(update.message, t("اكتب الكلمة الجديدة اللي تبيها تطلع بدالها:"))
            return
        elif state.get("step") == "waiting_for_new_word":
            db["word_replacements"][state["old_word"]] = html_text
            save_data(db)
            del changing_word_state[user_id_int]
            await safe_reply(update.message, t("تم التغيير بنجاح! أي رسالة فيها كلمتك القديمة بتتغير للجديدة!"))
            return

    if text == "تغير كلمه":
        if issuer_weight < ROLES["مالك"]: return await safe_reply(update.message, t("للمالك فقط"))
        changing_word_state[user_id_int] = {"step": "waiting_for_old_word"}
        await safe_reply(update.message, t("اكتب الكلمة الأساسية بالبوت اللي تبي تغيرها:"))
        return

    # ------------------ نظام الكليشات المزدوج ------------------
    if user_id_int in changing_template_state:
        state = changing_template_state[user_id_int]
        target = state.get("target")
        
        if target == "id":
            if chat_id not in db["chat_templates"]: db["chat_templates"][chat_id] = {}
            db["chat_templates"][chat_id]["id"] = html_text 
            save_data(db)
            del changing_template_state[user_id_int]
            await safe_reply(update.message, t("تم حفظ كليشة الايدي الخاصة بالمجموعة بنجاح!"))
            return
        elif target == "cmd":
            if chat_id not in db["chat_templates"]: db["chat_templates"][chat_id] = {}
            db["chat_templates"][chat_id]["commands"] = html_text
            save_data(db)
            del changing_template_state[user_id_int]
            await safe_reply(update.message, t("تم حفظ كليشة الاوامر الخاصة بالمجموعة بنجاح!"))
            return
        elif target == "global_id":
            db["global_templates"]["id"] = html_text
            save_data(db)
            del changing_template_state[user_id_int]
            await safe_reply(update.message, t("تم حفظ كليشة الايدي العامة (لكل القروبات) بنجاح!"))
            return
        elif target == "global_cmd":
            db["global_templates"]["commands"] = html_text
            save_data(db)
            del changing_template_state[user_id_int]
            await safe_reply(update.message, t("تم حفظ كليشة الاوامر العامة (لكل القروبات) بنجاح!"))
            return

    if text == "تغيير كليشة الايدي":
        if issuer_weight < ROLES["مالك"]: return await safe_reply(update.message, t("للمالك فقط"))
        changing_template_state[user_id_int] = {"target": "id"}
        await safe_reply(update.message, t("ارسل الكليشة الخاصة بهذي المجموعة.\nمتغيرات: #الاسم, #الايدي, #يوزره, #الرتبة, #الرسائل, #النقاط"))
        return

    if text == "تغيير كليشة الاوامر":
        if issuer_weight < ROLES["مالك"]: return await safe_reply(update.message, t("للمالك فقط"))
        changing_template_state[user_id_int] = {"target": "cmd"}
        await safe_reply(update.message, t("ارسل كليشة الأوامر الخاصة بهذي المجموعة."))
        return

    if text == "تغيير كليشة الايدي عام":
        if user_id != str(DEVELOPER_ID): return await safe_reply(update.message, t("هذا الأمر للمطور فقط"))
        changing_template_state[user_id_int] = {"target": "global_id"}
        await safe_reply(update.message, t("ارسل الكليشة العامة للايدي (بتتطبق على كل القروبات اللي ماعندها كليشة خاصة)."))
        return

    if text == "تغيير كليشة الاوامر عام":
        if user_id != str(DEVELOPER_ID): return await safe_reply(update.message, t("هذا الأمر للمطور فقط"))
        changing_template_state[user_id_int] = {"target": "global_cmd"}
        await safe_reply(update.message, t("ارسل كليشة الأوامر العامة (بتتطبق على كل القروبات)."))
        return

    # ------------------ نظام الردود ------------------
    if user_id_int in adding_reply_state:
        state = adding_reply_state[user_id_int]
        step = state.get("step")
        target_type = state.get("type", "general") 

        if step == "waiting_for_keyword":
            state["keyword"] = text
            state["step"] = "waiting_for_reply_content"
            await safe_reply(update.message, t("حسنا يمكنك اضافة النص بحرية\nمتغيرات: #الاسم, #الايدي.. الخ"))
            return

        elif step == "waiting_for_reply_content":
            keyword = state.get("keyword")
            if keyword:
                reply_to_save = html_text 
                if target_type == "general":
                    if keyword not in db["custom_replies"]: db["custom_replies"][keyword] = []
                    db["custom_replies"][keyword].append(reply_to_save)
                else:
                    if chat_id not in db["group_replies"]: db["group_replies"][chat_id] = {}
                    if keyword not in db["group_replies"][chat_id]: db["group_replies"][chat_id][keyword] = []
                    db["group_replies"][chat_id][keyword].append(reply_to_save)
                save_data(db)
                await safe_reply(update.message, t("تم الحفظ! ارسل رد إضافي أو اكتب 'تم'"))
                state["step"] = "waiting_for_more_replies"
            return

        elif step == "waiting_for_more_replies":
            if text.lower() in ["تم", "خلاص"]:
                del adding_reply_state[user_id_int]
                await safe_reply(update.message, t("تم الانتهاء وحفظ جميع الردود"))
                return
            else:
                reply_to_save = html_text
                if target_type == "general": db["custom_replies"][state["keyword"]].append(reply_to_save)
                else: db["group_replies"][chat_id][state["keyword"]].append(reply_to_save)
                save_data(db)
                await safe_reply(update.message, t("تمت إضافة الرد الإضافي، ارسل غيره أو اكتب 'تم'"))
                return

    if text == "اضف رد عام":
        if user_id != str(DEVELOPER_ID): return await safe_reply(update.message, t("للمطور فقط"))
        adding_reply_state[user_id_int] = {"step": "waiting_for_keyword", "type": "general"}
        await safe_reply(update.message, t("ارسل كلمة الرد العام"))
        return

    if text == "اضف رد":
        if issuer_weight < ROLES["مالك"]: return await safe_reply(update.message, t("للمالك فقط"))
        adding_reply_state[user_id_int] = {"step": "waiting_for_keyword", "type": "group"}
        await safe_reply(update.message, t("ارسل كلمة الرد الخاص بمجموعتك"))
        return

    if text.startswith("حذف رد عام "):
        if user_id != str(DEVELOPER_ID): return
        keyword = text.replace("حذف رد عام ", "").strip()
        if keyword in db["custom_replies"]:
            del db["custom_replies"][keyword]
            save_data(db)
            await safe_reply(update.message, t(f"تم حذف الرد العام: {keyword}"))
        return

    if text.startswith("حذف رد "):
        if issuer_weight < ROLES["مالك"]: return
        keyword = text.replace("حذف رد ", "").strip()
        if chat_id in db.get("group_replies", {}) and keyword in db["group_replies"][chat_id]:
            del db["group_replies"][chat_id][keyword]
            save_data(db)
            await safe_reply(update.message, t(f"تم حذف رد القروب: {keyword}"))
        return

    # فحص الردود
    group_replies = db.get("group_replies", {}).get(chat_id, {})
    if text in group_replies:
        formatted_reply = format_reply_text(random.choice(group_replies[text]), user, chat_id)
        await safe_reply(update.message, t(formatted_reply))
        return
    elif text in db["custom_replies"]:
        formatted_reply = format_reply_text(random.choice(db["custom_replies"][text]), user, chat_id)
        await safe_reply(update.message, t(formatted_reply))
        return

    # ------------------ الألعاب المصغرة والمتعة ------------------
    if text in ["كت تويت", "كت"]: return await safe_reply(update.message, t(random.choice(CUT_TWEET)))
    if text in ["صراحة", "صراحه"]: return await safe_reply(update.message, t(random.choice(SARAHA)))
    if text == "لو خيروك": return await safe_reply(update.message, t(random.choice(KHYROK)))
    if text == "عقاب": return await safe_reply(update.message, t(random.choice(EQAB)))

    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        target_id = str(target_user.id)
        
        if text in ["اهمس", "ه"]:
            if target_user.is_bot: return await safe_reply(update.message, t("يا غبي مايمديك تهمس للبوت"))
            if target_id == user_id: return await safe_reply(update.message, t("يا حمار ماتقدر تهمس لنفسك"))
            w_id = str(random.randint(100000, 999999))
            db["whispers"][w_id] = {"from_id": user_id, "from_name": user.first_name, "to_id": target_id, "to_name": target_user.first_name, "chat_id": chat_id, "text": ""}
            save_data(db)
            await safe_reply(update.message, t(f"تم تحديد الهمسه لـ {target_user.first_name}"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t("اهمس هنا"), url=f"https://t.me/{(await context.bot.get_me()).username}?start=w_{w_id}")]]))
            return

        if text == "زواج":
            if target_id == user_id: return await safe_reply(update.message, t("تبي تتزوج نفسك؟ صاحي انت!"))
            db["marriages"][user_id] = target_id
            db["marriages"][target_id] = user_id
            save_data(db)
            return await safe_reply(update.message, t(f"مبروك! تم زواج {user.first_name} من {target_user.first_name} بالرفاه والبنين"))

        if text == "مسح":
            if issuer_weight < ROLES["ادمن"]: return await safe_reply(update.message, t("للمشرفين وأعلى"))
            try:
                await update.message.reply_to_message.delete()
                await update.message.delete()
            except: pass
            return
            
        if text.startswith("رفع "):
            if issuer_weight < ROLES["مالك"]: return await safe_reply(update.message, t("صلاحياتك ما تسمح"))
            new_role = text.replace("رفع ", "").strip()
            if new_role in ROLES and ROLES[new_role] < issuer_weight:
                if chat_id not in db["roles"]: db["roles"][chat_id] = {}
                db["roles"][chat_id][target_id] = new_role
                save_data(db)
                await safe_reply(update.message, t(f"ابشر، تم رفع {target_user.first_name} الى رتبة {new_role}"))
            return

    if text == "طلاق":
        if user_id in db.get("marriages", {}):
            p_id = db["marriages"][user_id]
            del db["marriages"][user_id]
            if p_id in db["marriages"]: del db["marriages"][p_id]
            save_data(db)
            return await safe_reply(update.message, t("ابغض الحلال.. تم الطلاق بنجاح وانفصلتوا"))
        return await safe_reply(update.message, t("انت مو متزوج اصلا عشان تطلق!"))

    if text == "راتب":
        u_bank = db["bank"].get(user_id)
        if u_bank:
            if time.time() - u_bank.get("last_salary", 0) < 3600: return await safe_reply(update.message, t("باقي وقت على راتبك"))
            amt = random.randint(10000, 50000) * get_multiplier(user_id)
            u_bank["balance"] += amt
            u_bank["last_salary"] = time.time()
            save_data(db)
            return await safe_reply(update.message, t(f"تم ايداع راتبك: {amt} ريال"))

    if text.startswith("ماريا "):
        prompt = text.replace("ماريا ", "").strip()
        status = await safe_reply(update.message, t("يتم التفكير"))
        ai_reply = await asyncio.to_thread(get_fast_ai_response, prompt)
        try: await status.edit_text(t(ai_reply), parse_mode="HTML")
        except: await status.edit_text(t(ai_reply))
        return

class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write("البوت شغال 100% بدون تعارضات".encode('utf-8'))

def run_server():
    server = HTTPServer(('0.0.0.0', int(os.environ.get("PORT", 10000))), DummyHandler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(ChatMemberHandler(track_bot_joins, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_text))
    print("البوت شغال بدون تعارضات وبدون ايموجيات عادية")
    
    # السر هنا: إغلاق أي نسخة قديمة وحل تعارض Telegram!
    app.run_polling(drop_pending_updates=True)

# تفعيل التوافق مع بيئة الاستضافات السحابية
nest_asyncio.apply()

# ================= الإعدادات الأساسية =================
TOKEN = "5845566822:AAGJGPGclHybO3r-0mL1I9kGDxduR7R6nr8"
DEVELOPER_ID = 5543325412
BOT_NAME = "ماريا"
DEV_NAME = "محمد الهاشمي"
DEV_BIO = "Software Developer"
# =======================================================

ai_client = Client()
DATA_FILE = 'data.json'

# قواميس حفظ حالات المستخدمين
adding_reply_state = {}
changing_word_state = {}
creating_button_state = {}
adding_alias_state = {}
changing_template_state = {}

active_word_game = {}
active_math_game = {}
active_tafkik_game = {}
active_tarkib_game = {}
active_capitals_game = {}
active_speed_game = {}
xo_games = {}
pending_whispers = {}

CAPITALS = {
    "السعودية": "الرياض", "مصر": "القاهرة", "الامارات": "ابوظبي", "الكويت": "الكويت",
    "قطر": "الدوحة", "البحرين": "المنامة", "عمان": "مسقط", "سوريا": "دمشق",
    "فلسطين": "القدس", "العراق": "بغداد", "اليمن": "صنعاء", "فرنسا": "باريس",
    "بريطانيا": "لندن", "ايطاليا": "روما", "اسبانيا": "مدريد", "المانيا": "برلين"
}

CUT_TWEET = ["وش طموحك بالحياة؟", "عمرك ندمت على معرفة شخص؟", "تفضل الشاي ولا القهوة؟", "أكثر تطبيق تستخدمه؟", "كلمة لشخص ببالك؟"]
SARAHA = ["متى آخر مرة بكيت؟", "أكبر كذبة كذبتها؟", "مين أقرب شخص لقلبك؟", "شيء تخاف منه؟"]
KHYROK = ["تخسر كل فلوسك أو تخسر أعز أصدقائك؟", "تطير ولا تختفي؟", "تاكل بيتزا طول عمرك ولا شاورما؟"]
EQAB = ["ارسل آخر صورة بجوالك", "اعترف بشيء غبي سويته بالقروب", "اكتب انا غبي 10 مرات", "أرسل نكتة سامجة"]

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # التأكد من وجود كل الأقسام
            for k in ["custom_replies", "group_replies", "msg_count", "bank", "group_games", "group_msgs", "group_names", "user_names", "link_disabled", "settings", "word_replacements", "whispers", "command_aliases", "chat_settings", "marriages", "chat_templates", "global_templates"]:
                if k not in data: data[k] = {}
            if "stats" not in data: data["stats"] = {"users": [], "groups": []}
            if "market" not in data: data["market"] = {"price": 100, "last_update": 0}
            if "game_words" not in data: data["game_words"] = ["مدرسة", "تليجرام", "سيارة", "مبرمج", "هاكر"]
            if "top_btn" not in data["settings"]: data["settings"]["top_btn"] = {"text": "اخفاء التوب", "emoji": ""}
            return data

    return {
        "roles": {}, "muted": {}, "custom_replies": {}, "group_replies": {}, "msg_count": {},
        "stats": {"users": [], "groups": []}, "bank": {}, "market": {"price": 100, "last_update": 0},
        "group_games": {}, "group_msgs": {}, "group_names": {}, "user_names": {},
        "link_disabled": {}, "game_words": ["مدرسة", "تليجرام", "سيارة", "برمجة", "حماية"],
        "settings": {"top_btn": {"text": "اخفاء التوب", "emoji": ""}}, "word_replacements": {},
        "whispers": {}, "command_aliases": {}, "chat_settings": {}, "marriages": {}, "chat_templates": {}, "global_templates": {}
    }

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = load_data()

# دالة ذكية لإرسال الرسائل تدعم الرموز المتحركة (HTML) بأمان
async def safe_reply(message_obj, text, **kwargs):
    try:
        return await message_obj.reply_text(text, parse_mode="HTML", **kwargs)
    except Exception:
        return await message_obj.reply_text(text, **kwargs)

async def safe_reply_photo(message_obj, photo, caption, **kwargs):
    try:
        return await message_obj.reply_photo(photo, caption=caption, parse_mode="HTML", **kwargs)
    except Exception:
        return await message_obj.reply_photo(photo, caption=caption, **kwargs)

def t(text):
    if not isinstance(text, str): return text
    for old_w, new_w in db.get("word_replacements", {}).items():
        text = text.replace(old_w, new_w)
    return text

ROLES = {"Dev": 6, "مالك اساسي": 5, "مالك": 4, "مدير": 3, "ادمن": 2, "مميز": 1, "عضو": 0}
ITEMS_PRICES = {"سيارة": 1000000, "ماسة": 5000000, "قصر": 15000000}
WHEEL_COST = 5000000

def get_user_role(chat_id, user_id):
    if str(user_id) == str(DEVELOPER_ID): return "Dev"
    chat_id, user_id = str(chat_id), str(user_id)
    if chat_id in db["roles"] and user_id in db["roles"][chat_id]:
        return db["roles"][chat_id][user_id]
    return "عضو"

def check_jail(user_id):
    u_bank = db["bank"].get(str(user_id))
    if not u_bank: return False
    if u_bank.get("is_jailed"): return True
    if u_bank.get("loan_due", 0) > 0 and time.time() > u_bank["loan_due"]:
        u_bank["is_jailed"] = True
        save_data(db)
        return True
    return False

def get_multiplier(user_id):
    u_bank = db["bank"].get(str(user_id))
    if u_bank and u_bank.get("x2_expiry", 0) > time.time(): return 2
    return 1

def win_game(uid, amount):
    if uid in db["bank"]:
        prize = amount * get_multiplier(uid)
        db["bank"][uid]["balance"] += prize
        save_data(db)
        return prize
    return 0

async def delete_after(message, seconds):
    await asyncio.sleep(seconds)
    try: await message.delete()
    except Exception: pass

def generate_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("الالعاب 🕹", callback_data="cmd_games"), InlineKeyboardButton("البنك 💰", callback_data="cmd_bank")],
        [InlineKeyboardButton("الحماية 🛡", callback_data="cmd_protect"), InlineKeyboardButton("الادارة ⚙️", callback_data="cmd_admin")],
        [InlineKeyboardButton("العامة 🌐", callback_data="cmd_general"), InlineKeyboardButton("المطور 👨‍💻", callback_data="cmd_dev")],
        [InlineKeyboardButton("إغلاق القائمة ❌", callback_data="hide_top")]
    ])

def generate_xo_board(game_id):
    board = xo_games[game_id]["board"]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(board[0], callback_data=f"xo_{game_id}_0"), InlineKeyboardButton(board[1], callback_data=f"xo_{game_id}_1"), InlineKeyboardButton(board[2], callback_data=f"xo_{game_id}_2")],
        [InlineKeyboardButton(board[3], callback_data=f"xo_{game_id}_3"), InlineKeyboardButton(board[4], callback_data=f"xo_{game_id}_4"), InlineKeyboardButton(board[5], callback_data=f"xo_{game_id}_5")],
        [InlineKeyboardButton(board[6], callback_data=f"xo_{game_id}_6"), InlineKeyboardButton(board[7], callback_data=f"xo_{game_id}_7"), InlineKeyboardButton(board[8], callback_data=f"xo_{game_id}_8")]
    ])

def check_xo_win(board):
    lines = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
    for a, b, c in lines:
        if board[a] == board[b] == board[c] and board[a] != "-": return board[a]
    if "-" not in board: return "Draw"
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if args and args[0].startswith("w_"):
        w_id = args[0][2:]
        if w_id in db["whispers"]:
            if db["whispers"][w_id]["from_id"] == str(update.message.from_user.id):
                pending_whispers[update.message.from_user.id] = w_id
                await safe_reply(update.message, t("اكتب همستك السرية الحين 🤫:"))
                return
    await safe_reply(update.message, t(f"هلا ومرحبا بك في بوت {BOT_NAME} 🌟"))

def get_fast_ai_response(prompt):
    try:
        response = ai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "أنت مساعد ذكي تسولف باللهجة السعودية البحتة والعامية وبأسلوب عفوي وسريع. ممنوع استخدام أي رموز تعبيرية."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.replace("*", "").replace("`", "").strip()
    except Exception:
        return "ابشر بس فيه ضغط بسيط جرب ثانية"

def format_reply_text(text, user, chat_id="المجموعة"):
    name = html.escape(user.first_name or "المستخدم")
    username = html.escape(f"@{user.username}" if user.username else "بدون يوزر")
    msg_cnt = db["msg_count"].get(str(user.id), 1)
    role = get_user_role(chat_id, user.id)
    pts = db['bank'].get(str(user.id), {}).get('balance', 0)
    return text.replace("#الاسم", name).replace("#يوزره", username).replace("#اليوزر", username).replace("#الايدي", str(user.id)).replace("#الرتبة", str(role)).replace("#الرسائل", str(msg_cnt)).replace("#النقاط", str(pts))

async def track_bot_joins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.my_chat_member
    if result.new_chat_member.status in ["member", "administrator"]:
        chat = result.chat
        if str(chat.id) not in db["stats"]["groups"]:
            db["stats"]["groups"].append(str(chat.id))
            save_data(db)
        link = "الرابط غير متوفر"
        if result.new_chat_member.status == "administrator":
            try: link = await context.bot.export_chat_invite_link(chat.id)
            except Exception: pass
        msg = f"تمت اضافة البوت لمجموعة جديدة 🎊\nاسم المجموعة: {chat.title}\nرابط المجموعة: {link}\n\nعدد المجموعات: {len(db['stats']['groups'])}"
        await context.bot.send_message(chat_id=DEVELOPER_ID, text=t(msg))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    data = query.data

    if data == "hide_top":
        try:
            await query.answer()
            await query.message.delete()
        except Exception: pass
        return

    # --- لعبة اكس او ---
    if data.startswith("xo_"):
        parts = data.split("_")
        game_id, pos = parts[1], int(parts[2])

        if game_id not in xo_games:
            return await query.answer("اللعبة هذي منتهية او محذوفة.", show_alert=True)
        game = xo_games[game_id]
        if user_id not in [game["p1"], game["p2"]]:
            return await query.answer("اللعبة مو لك، لا تتدخل!", show_alert=True)
        if user_id != game["turn"]:
            return await query.answer("مو دورك، انتظر!", show_alert=True)
        if game["board"][pos] != "-":
            return await query.answer("المكان محجوز، اختر غيره.", show_alert=True)

        game["board"][pos] = "X" if user_id == game["p1"] else "O"
        win_result = check_xo_win(game["board"])

        if win_result:
            if win_result == "Draw": msg = "انتهت اللعبة بالتعادل!"
            else:
                winner_id = game["p1"] if win_result == "X" else game["p2"]
                winner_name = game["p1_name"] if win_result == "X" else game["p2_name"]
                prize = win_game(winner_id, 10000)
                msg = f"انتهت اللعبة بفوز {winner_name} 👑!\nحصل على جائزة {prize} ريال."
            
            try: await query.message.edit_text(t(msg), reply_markup=generate_xo_board(game_id), parse_mode="HTML")
            except: await query.message.edit_text(t(msg), reply_markup=generate_xo_board(game_id))
            del xo_games[game_id]
            return

        game["turn"] = game["p2"] if user_id == game["p1"] else game["p1"]
        next_turn_name = game["p2_name"] if user_id == game["p1"] else game["p1_name"]
        msg = f"لعبة اكس او مستمرة 🎮\nالدور الان على: {next_turn_name}"
        try: await query.message.edit_text(t(msg), reply_markup=generate_xo_board(game_id), parse_mode="HTML")
        except: await query.message.edit_text(t(msg), reply_markup=generate_xo_board(game_id))
        return

    # --- قوائم الأوامر ---
    menus = {
        "cmd_main": "اهلا بك في قائمة اوامر ماريا\nاختر القسم اللي تبيه:",
        "cmd_games": "<b>اوامر الالعاب 🕹:</b>\n- سرعة\n- اكس او [بالرد]\n- كلمات\n- رياضيات\n- عواصم\n- كت / صراحة / عقاب\n- زواج [بالرد] / طلاق\n- زوجي\n- توب المتفاعلين",
        "cmd_bank": "<b>اوامر البنك 💰:</b>\n- راتب\n- زرف [بالرد]\n- حظ / العجله\n- شراء / بيع\n- قرض\n- فلوسي\n- ممتلكاتي",
        "cmd_protect": "<b>اوامر الحماية 🛡:</b>\n- قفل الروابط / فتح الروابط\n- قفل الصور / قفل الملصقات\n- قفل التوجيه",
        "cmd_admin": "<b>الادارة ⚙️:</b>\n- حظر / طرد / كتم / تقييد [بالرد]\n- رفع / تنزيل\n- تغيير كليشة الايدي\n- تغيير كليشة الاوامر\n- اضف رد / حذف رد",
        "cmd_general": "<b>العامة 🌐:</b>\n- ايدي\n- معلوماتي\n- رتبتي\n- الوقت / التاريخ\n- اهمس / ه [بالرد]\n- الرابط",
        "cmd_dev": "<b>المطور 👨‍💻:</b>\n- اضف امر\n- تغير كلمه\n- تغيير كليشة الايدي عام\n- تغيير كليشة الاوامر عام\n- اضف رد عام / حذف رد عام\n- صنع زر"
    }

    if data in menus:
        if data == "cmd_dev" and user_id != str(DEVELOPER_ID):
            return await query.answer(t("معليش، هذا القسم خاص بالمطور فقط! 🛑"), show_alert=True)
        await query.answer()
        reply_m = generate_menu_keyboard() if data == "cmd_main" else InlineKeyboardMarkup([[InlineKeyboardButton("رجوع 🔙", callback_data="cmd_main")]])
        try: await query.message.edit_text(t(menus[data]), reply_markup=reply_m, parse_mode="HTML")
        except: await query.message.edit_text(t(menus[data]), reply_markup=reply_m)
        return

    # --- نظام الهمسات بالأزرار ---
    if data.startswith("sw_"):
        w_id = data[3:]
        if w_id in db.get("whispers", {}):
            whisper = db["whispers"][w_id]
            if user_id in [whisper["from_id"], whisper["to_id"]]:
                return await query.answer(text=whisper["text"], show_alert=True)
            return await query.answer(text=t("الهمسة مو لك، لا تتدخل 🤫"), show_alert=True)
        return await query.answer(text=t("الهمسة هذي محذوفة ❌"), show_alert=True)

    if data.startswith("rw_"):
        parts = data.split("_", 2)
        if len(parts) >= 3:
            w_id = str(random.randint(100000, 999999))
            bot_info = await context.bot.get_me()
            db["whispers"][w_id] = {
                "from_id": user_id, "from_name": query.from_user.first_name,
                "to_id": parts[1], "to_name": parts[2],
                "chat_id": str(query.message.chat.id), "text": ""
            }
            save_data(db)
            btn_url = f"https://t.me/{bot_info.username}?start=w_{w_id}"
            await context.bot.send_message(
                chat_id=query.message.chat.id,
                text=t(f"تم تحديد الهمسه لـ {parts[2]} 🔒\nاضغط الزر لكتابة الهمسة"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t("اهمس هنا ✍️"), url=btn_url)]])
            )
            await query.answer()

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.from_user: return

    chat_id = str(update.message.chat_id)
    user = update.message.from_user
    user_id_int, user_id = user.id, str(user.id)

    issuer_role = get_user_role(chat_id, user_id_int)
    issuer_weight = ROLES[issuer_role]

    # سحب الرسالة بصيغة HTML لحفظ رموز البريميوم المتحركة!
    raw_text = update.message.text or update.message.caption
    if not raw_text: return
    text = raw_text.strip()
    html_text = update.message.text_html or update.message.caption_html or text

    # --- نظام الحماية (رتبة مميز مستثنيين) ---
    if update.message.chat.type in ['group', 'supergroup'] and issuer_weight < ROLES["مميز"]:
        if chat_id not in db.get("chat_settings", {}):
            db.setdefault("chat_settings", {})[chat_id] = {"links": False, "photos": False, "stickers": False, "forwards": False}

        c_set = db["chat_settings"][chat_id]
        must_delete, reason = False, ""
        if c_set.get("photos") and update.message.photo: must_delete, reason = True, "الصور"
        elif c_set.get("stickers") and update.message.sticker: must_delete, reason = True, "الملصقات"
        elif c_set.get("forwards") and update.message.forward_date: must_delete, reason = True, "التوجيه"
        
        if c_set.get("links") and ("http://" in text or "https://" in text or "t.me/" in text):
            must_delete, reason = True, "الروابط"

        if must_delete:
            try:
                await update.message.delete()
                warning_msg = await safe_reply(update.message, t(f"عذرا {user.first_name}، يمنع ارسال {reason} هنا 🚫."))
                asyncio.create_task(delete_after(warning_msg, 5))
            except Exception: pass
            return

    # --- استقبال الهمسة في الخاص ---
    if update.message.chat.type == "private":
        if user_id_int in pending_whispers:
            w_id = pending_whispers[user_id_int]
            if w_id in db.get("whispers", {}):
                db["whispers"][w_id]["text"] = text
                save_data(db)
                whisper = db["whispers"][w_id]
                keyboard = [
                    [InlineKeyboardButton(t("رؤية الهمسة 👁‍🗨"), callback_data=f"sw_{w_id}")],
                    [InlineKeyboardButton(t(f"اهمس لـ {whisper['from_name']} ✍️"), callback_data=f"rw_{whisper['from_id']}_{whisper['from_name']}")]
                ]
                try:
                    await context.bot.send_message(chat_id=whisper["chat_id"], text=t(f"الهمسه لـ {whisper['to_name']} 🔒\nمن {whisper['from_name']}"), reply_markup=InlineKeyboardMarkup(keyboard))
                    await safe_reply(update.message, t("تم ارسال الهمسة بنجاح! ✅"))
                except Exception:
                    await safe_reply(update.message, t("فشلت عملية ارسال الهمسة ❌."))
                del pending_whispers[user_id_int]
                return

    # تحديث إحصائيات 
    db["user_names"][user_id] = user.first_name
    if update.message.chat.type in ['group', 'supergroup']:
        if chat_id not in db["group_msgs"]: db["group_msgs"][chat_id] = {}
        db["group_names"][chat_id] = update.message.chat.title
        db["group_msgs"][chat_id][user_id] = db["group_msgs"][chat_id].get(user_id, 0) + 1

    if user_id not in db["stats"]["users"]: db["stats"]["users"].append(user_id)
    if chat_id not in db["stats"]["groups"] and update.message.chat.type in ['group', 'supergroup']:
        db["stats"]["groups"].append(chat_id)

    db["msg_count"][user_id] = db["msg_count"].get(user_id, 0) + 1
    save_data(db)

    # فحص الكتم
    if chat_id in db["muted"] and user_id in db["muted"][chat_id]:
        try: await update.message.delete()
        except Exception: pass
        return

    # --- اختصارات الأوامر ---
    aliases = db.get("command_aliases", {})
    if text in aliases: text = aliases[text]
    else:
        for alias, orig in aliases.items():
            if text.startswith(alias + " "):
                text = orig + text[len(alias):]
                break
    text_normalized = text.replace("إلغاء", "الغاء").replace("فك ", "الغاء ")

    # ------------------ الأوامر العامة والرئيسية ------------------
    if text == "رتبتي":
        await safe_reply(update.message, t(f"رتبتك في هذه المجموعة هي: <b>{issuer_role}</b> 🌟"))
        return
        
    if text == "معلوماتي":
        msg = f"<b>معلوماتك الشخصية:</b>\nالاسم: {user.first_name}\nاليوزر: @{user.username if user.username else 'لا يوجد'}\nالايدي: <code>{user.id}</code>\nرتبتك بالقروب: {issuer_role}\nرسائلك: {db['msg_count'].get(str(user.id), 1)}\nرصيدك البنكي: {db['bank'].get(str(user.id), {}).get('balance', 0)} ريال 💰"
        await safe_reply(update.message, t(msg))
        return

    if text.lower() in ["ايدي", "ا", "id"]:
        user_photos = await context.bot.get_user_profile_photos(user.id, limit=1)
        
        # الذكاء في الكليشات: يفضل كليشة القروب، إذا مو موجودة يأخذ الكليشة العامة، إذا مو موجودة يأخذ الافتراضية
        id_template = db.get("chat_templates", {}).get(chat_id, {}).get("id")
        if not id_template:
            id_template = db.get("global_templates", {}).get("id", "iD: <code>#الايدي</code>\nName: #الاسم\nUser Name: #يوزره\nRank: #الرتبة\nMsg: #الرسائل")
            
        caption = format_reply_text(id_template, user, chat_id)
        if user_photos.total_count > 0:
            await safe_reply_photo(update.message, user_photos.photos[0][-1].file_id, t(caption))
        else:
            await safe_reply(update.message, t(caption))
        return

    if text in ["الاوامر", "اوامري", "م", "أوامر"]:
        # الذكاء في كليشة الأوامر: قروب -> عام -> افتراضي
        cmd_template = db.get("chat_templates", {}).get(chat_id, {}).get("commands")
        if not cmd_template:
            cmd_template = db.get("global_templates", {}).get("commands", "اهلا بك في قائمة اوامر ماريا\nاختر القسم اللي تبيه:")
            
        formatted_cmd = format_reply_text(cmd_template, user, chat_id)
        await safe_reply(update.message, t(formatted_cmd), reply_markup=generate_menu_keyboard())
        return

    # ------------------ نظام تغير كلمة واختصار الاوامر ------------------
    if user_id_int in adding_alias_state:
        state = adding_alias_state[user_id_int]
        if state.get("step") == "waiting_for_old_cmd":
            state["old_cmd"] = text
            state["step"] = "waiting_for_new_cmd"
            await safe_reply(update.message, t("ممتاز، الحين ارسل الاختصار اللي تبيه:"))
            return
        elif state.get("step") == "waiting_for_new_cmd":
            db["command_aliases"][text] = state["old_cmd"]
            save_data(db)
            del adding_alias_state[user_id_int]
            await safe_reply(update.message, t(f"تم بنجاح! تقدر تستخدم '{text}' بدال '{state['old_cmd']}'."))
            return

    if text == "اضف امر":
        if issuer_weight < ROLES["مالك"]: return await safe_reply(update.message, t("للمالك والمطور فقط 🛑"))
        adding_alias_state[user_id_int] = {"step": "waiting_for_old_cmd"}
        await safe_reply(update.message, t("ارسل الأمر الأساسي (مثلاً: حظر)"))
        return

    if user_id_int in changing_word_state:
        state = changing_word_state[user_id_int]
        if state.get("step") == "waiting_for_old_word":
            state["old_word"] = text
            state["step"] = "waiting_for_new_word"
            await safe_reply(update.message, t("اكتب الكلمة الجديدة اللي تبيها تطلع بدالها:"))
            return
        elif state.get("step") == "waiting_for_new_word":
            db["word_replacements"][state["old_word"]] = html_text
            save_data(db)
            del changing_word_state[user_id_int]
            await safe_reply(update.message, t("تم التغيير بنجاح! أي رسالة فيها كلمتك القديمة بتتغير للجديدة برموزها! ✅"))
            return

    if text == "تغير كلمه":
        if issuer_weight < ROLES["مالك"]: return await safe_reply(update.message, t("للمالك فقط 🛑"))
        changing_word_state[user_id_int] = {"step": "waiting_for_old_word"}
        await safe_reply(update.message, t("اكتب الكلمة الأساسية بالبوت اللي تبي تغيرها:"))
        return

    # ------------------ نظام الكليشات المزدوج (عام / خاص بالقروب) ------------------
    if user_id_int in changing_template_state:
        state = changing_template_state[user_id_int]
        target = state.get("target")
        
        if target == "id":
            if chat_id not in db["chat_templates"]: db["chat_templates"][chat_id] = {}
            db["chat_templates"][chat_id]["id"] = html_text 
            save_data(db)
            del changing_template_state[user_id_int]
            await safe_reply(update.message, t("تم حفظ كليشة الايدي الخاصة بالمجموعة بنجاح! ✅"))
            return
        elif target == "cmd":
            if chat_id not in db["chat_templates"]: db["chat_templates"][chat_id] = {}
            db["chat_templates"][chat_id]["commands"] = html_text
            save_data(db)
            del changing_template_state[user_id_int]
            await safe_reply(update.message, t("تم حفظ كليشة الاوامر الخاصة بالمجموعة بنجاح! ✅"))
            return
        elif target == "global_id":
            db["global_templates"]["id"] = html_text
            save_data(db)
            del changing_template_state[user_id_int]
            await safe_reply(update.message, t("تم حفظ كليشة الايدي العامة (لكل القروبات) بنجاح! 🌍✅"))
            return
        elif target == "global_cmd":
            db["global_templates"]["commands"] = html_text
            save_data(db)
            del changing_template_state[user_id_int]
            await safe_reply(update.message, t("تم حفظ كليشة الاوامر العامة (لكل القروبات) بنجاح! 🌍✅"))
            return

    if text == "تغيير كليشة الايدي":
        if issuer_weight < ROLES["مالك"]: return await safe_reply(update.message, t("للمالك فقط 🛑"))
        changing_template_state[user_id_int] = {"target": "id"}
        await safe_reply(update.message, t("ارسل الكليشة الخاصة بهذي المجموعة مع رموز البريميوم.\nمتغيرات: #الاسم, #الايدي, #يوزره, #الرتبة, #الرسائل, #النقاط"))
        return

    if text == "تغيير كليشة الاوامر":
        if issuer_weight < ROLES["مالك"]: return await safe_reply(update.message, t("للمالك فقط 🛑"))
        changing_template_state[user_id_int] = {"target": "cmd"}
        await safe_reply(update.message, t("ارسل كليشة الأوامر الخاصة بهذي المجموعة."))
        return

    if text == "تغيير كليشة الايدي عام":
        if user_id != str(DEVELOPER_ID): return await safe_reply(update.message, t("هذا الأمر للمطور فقط 🛑"))
        changing_template_state[user_id_int] = {"target": "global_id"}
        await safe_reply(update.message, t("ارسل الكليشة العامة للايدي (بتتطبق على كل القروبات اللي ماعندها كليشة خاصة)."))
        return

    if text == "تغيير كليشة الاوامر عام":
        if user_id != str(DEVELOPER_ID): return await safe_reply(update.message, t("هذا الأمر للمطور فقط 🛑"))
        changing_template_state[user_id_int] = {"target": "global_cmd"}
        await safe_reply(update.message, t("ارسل كليشة الأوامر العامة (بتتطبق على كل القروبات)."))
        return

    # ------------------ نظام الردود ------------------
    if user_id_int in adding_reply_state:
        state = adding_reply_state[user_id_int]
        step = state.get("step")
        target_type = state.get("type", "general") 

        if step == "waiting_for_keyword":
            state["keyword"] = text
            state["step"] = "waiting_for_reply_content"
            await safe_reply(update.message, t("حسنا يمكنك اضافة النص مع رموز البريميوم بحرية\nمتغيرات: #الاسم, #الايدي.. الخ"))
            return

        elif step == "waiting_for_reply_content":
            keyword = state.get("keyword")
            if keyword:
                reply_to_save = html_text # حفظ رموز البريميوم
                if target_type == "general":
                    if keyword not in db["custom_replies"]: db["custom_replies"][keyword] = []
                    db["custom_replies"][keyword].append(reply_to_save)
                else:
                    if chat_id not in db["group_replies"]: db["group_replies"][chat_id] = {}
                    if keyword not in db["group_replies"][chat_id]: db["group_replies"][chat_id][keyword] = []
                    db["group_replies"][chat_id][keyword].append(reply_to_save)
                save_data(db)
                await safe_reply(update.message, t("تم الحفظ برموزه! ارسل رد إضافي أو اكتب 'تم' ✅"))
                state["step"] = "waiting_for_more_replies"
            return

        elif step == "waiting_for_more_replies":
            if text.lower() in ["تم", "خلاص"]:
                del adding_reply_state[user_id_int]
                await safe_reply(update.message, t("تم الانتهاء وحفظ جميع الردود ✅"))
                return
            else:
                reply_to_save = html_text
                if target_type == "general": db["custom_replies"][state["keyword"]].append(reply_to_save)
                else: db["group_replies"][chat_id][state["keyword"]].append(reply_to_save)
                save_data(db)
                await safe_reply(update.message, t("تمت إضافة الرد الإضافي، ارسل غيره أو اكتب 'تم'"))
                return

    if text == "اضف رد عام":
        if user_id != str(DEVELOPER_ID): return await safe_reply(update.message, t("للمطور فقط 🛑"))
        adding_reply_state[user_id_int] = {"step": "waiting_for_keyword", "type": "general"}
        await safe_reply(update.message, t("ارسل كلمة الرد العام"))
        return

    if text == "اضف رد":
        if issuer_weight < ROLES["مالك"]: return await safe_reply(update.message, t("للمالك فقط 🛑"))
        adding_reply_state[user_id_int] = {"step": "waiting_for_keyword", "type": "group"}
        await safe_reply(update.message, t("ارسل كلمة الرد الخاص بمجموعتك"))
        return

    if text.startswith("حذف رد عام "):
        if user_id != str(DEVELOPER_ID): return
        keyword = text.replace("حذف رد عام ", "").strip()
        if keyword in db["custom_replies"]:
            del db["custom_replies"][keyword]
            save_data(db)
            await safe_reply(update.message, t(f"تم حذف الرد العام: {keyword} ✅"))
        return

    if text.startswith("حذف رد "):
        if issuer_weight < ROLES["مالك"]: return
        keyword = text.replace("حذف رد ", "").strip()
        if chat_id in db.get("group_replies", {}) and keyword in db["group_replies"][chat_id]:
            del db["group_replies"][chat_id][keyword]
            save_data(db)
            await safe_reply(update.message, t(f"تم حذف رد القروب: {keyword} ✅"))
        return

    # فحص الردود
    group_replies = db.get("group_replies", {}).get(chat_id, {})
    if text in group_replies:
        formatted_reply = format_reply_text(random.choice(group_replies[text]), user, chat_id)
        await safe_reply(update.message, t(formatted_reply))
        return
    elif text in db["custom_replies"]:
        formatted_reply = format_reply_text(random.choice(db["custom_replies"][text]), user, chat_id)
        await safe_reply(update.message, t(formatted_reply))
        return

    # ------------------ الألعاب المصغرة والمتعة ------------------
    if text in ["كت تويت", "كت"]: return await safe_reply(update.message, t(random.choice(CUT_TWEET)))
    if text in ["صراحة", "صراحه"]: return await safe_reply(update.message, t(random.choice(SARAHA)))
    if text == "لو خيروك": return await safe_reply(update.message, t(random.choice(KHYROK)))
    if text == "عقاب": return await safe_reply(update.message, t(random.choice(EQAB)))

    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        target_id = str(target_user.id)
        
        if text in ["اهمس", "ه"]:
            if target_user.is_bot: return await safe_reply(update.message, t("يا غبي ما يمديك تهمس للبوت 🤖❌"))
            if target_id == user_id: return await safe_reply(update.message, t("يا حمار ما تقدر تهمس لنفسك 🐴❌"))
            w_id = str(random.randint(100000, 999999))
            db["whispers"][w_id] = {"from_id": user_id, "from_name": user.first_name, "to_id": target_id, "to_name": target_user.first_name, "chat_id": chat_id, "text": ""}
            save_data(db)
            await safe_reply(update.message, t(f"تم التحديد لـ {target_user.first_name} 🔒"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t("اهمس هنا ✍️"), url=f"https://t.me/{(await context.bot.get_me()).username}?start=w_{w_id}")]]))
            return

        if text == "زواج":
            if target_id == user_id: return await safe_reply(update.message, t("تبي تتزوج نفسك؟ صاحي! 🤦‍♂️"))
            db["marriages"][user_id] = target_id
            db["marriages"][target_id] = user_id
            save_data(db)
            return await safe_reply(update.message, t(f"مبروك! تم زواج {user.first_name} من {target_user.first_name} 💍🎊"))

        if text == "مسح":
            if issuer_weight < ROLES["ادمن"]: return await safe_reply(update.message, t("للمشرفين وأعلى 🛑"))
            try:
                await update.message.reply_to_message.delete()
                await update.message.delete()
            except: pass
            return
            
        if text.startswith("رفع "):
            if issuer_weight < ROLES["مالك"]: return await safe_reply(update.message, t("صلاحياتك ما تسمح 🛑"))
            new_role = text.replace("رفع ", "").strip()
            if new_role in ROLES and ROLES[new_role] < issuer_weight:
                if chat_id not in db["roles"]: db["roles"][chat_id] = {}
                db["roles"][chat_id][target_id] = new_role
                save_data(db)
                await safe_reply(update.message, t(f"ابشر، تم رفع {target_user.first_name} الى رتبة {new_role} 👑"))
            return

    if text == "طلاق":
        if user_id in db.get("marriages", {}):
            p_id = db["marriages"][user_id]
            del db["marriages"][user_id]
            if p_id in db["marriages"]: del db["marriages"][p_id]
            save_data(db)
            return await safe_reply(update.message, t("تم الطلاق بنجاح 💔"))
        return await safe_reply(update.message, t("انت مو متزوج اصلا! 😂"))

    if text == "راتب":
        u_bank = db["bank"].get(user_id)
        if u_bank:
            if time.time() - u_bank.get("last_salary", 0) < 3600: return await safe_reply(update.message, t("باقي وقت على راتبك ⏳"))
            amt = random.randint(10000, 50000) * get_multiplier(user_id)
            u_bank["balance"] += amt
            u_bank["last_salary"] = time.time()
            save_data(db)
            return await safe_reply(update.message, t(f"تم ايداع راتبك: {amt} ريال 💸"))

    if text.startswith("ماريا "):
        prompt = text.replace("ماريا ", "").strip()
        status = await safe_reply(update.message, t("يتم التفكير... 🤔"))
        ai_reply = await asyncio.to_thread(get_fast_ai_response, prompt)
        try: await status.edit_text(t(ai_reply), parse_mode="HTML")
        except: await status.edit_text(t(ai_reply))
        return

class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write("البوت شغال 100% مع الرموز المتحركة والكليشات المتطورة".encode('utf-8'))

def run_server():
    server = HTTPServer(('0.0.0.0', int(os.environ.get("PORT", 10000))), DummyHandler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(ChatMemberHandler(track_bot_joins, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_text))
    print("البوت شغال بأقوى التحديثات ويدعم الكليشات المزدوجة ورموز البريميوم في كل مكان!")
    app.run_polling()
