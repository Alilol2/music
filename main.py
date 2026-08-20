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
    "بريطانيا": "لندن", "ايطاليا": "روما", "اسبانيا": "مدريد", "المانيا": "برلين",
    "امريكا": "واشنطن", "روسيا": "موسكو", "اليابان": "طوكيو", "الصين": "بكين"
}

CUT_TWEET = [
    "وش طموحك بالحياة؟", "عمرك ندمت على معرفة شخص؟", "تفضل الشاي ولا القهوة؟",
    "أكثر تطبيق تستخدمه؟", "شيء مستحيل تسامح عليه؟", "كلمة لشخص ببالك؟",
    "لو رجع فيك الزمن وش بتغير؟", "أفضل سنة بحياتك؟", "وش قاعد تفكر فيه الحين؟", "تسامح بسهولة؟"
]

SARAHA = [
    "متى آخر مرة بكيت؟", "أكبر كذبة كذبتها؟", "مين أقرب شخص لقلبك؟",
    "شيء تخاف منه؟", "موقف محرج صار لك وما تنساه؟", "هل سبق وانطردت من حصة؟",
    "شخص تتمنى قربه؟", "هل تخفي سر كبير عن أهلك؟", "كم مرة حبيت؟", "أكثر صفة تكرهها بنفسك؟"
]

KHYROK = [
    "تخسر كل فلوسك أو تخسر أعز أصدقائك؟", "تعيش في الماضي ولا المستقبل؟",
    "تطير ولا تختفي؟", "تاكل بيتزا طول عمرك ولا شاورما؟",
    "تعرف متى بتموت ولا كيف بتموت؟", "تصير غني بس وحيد ولا فقير ومعاك أهلك؟",
    "تنسى كيف تتكلم ولا تنسى كيف تقرأ؟"
]

EQAB = [
    "ارسل آخر صورة بجوالك", "اعترف بشيء غبي سويته بالقروب",
    "حط صورة حمار افتار لك لمدة يوم", "ارسل رسالة اعتذار لأول شخص بالواتس وصور الشاشة",
    "اكتب انا غبي 10 مرات", "أرسل نكتة سامجة وإذا ما ضحكوا تنطرد دقيقة"
]

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for k in ["custom_replies", "group_replies", "msg_count", "bank", "group_games", "group_msgs", "group_names", "user_names", "link_disabled", "settings", "word_replacements", "whispers", "command_aliases", "chat_settings", "marriages", "chat_templates"]:
                if k not in data:
                    data[k] = {}
            if "stats" not in data:
                data["stats"] = {"users": [], "groups": []}
            if "market" not in data:
                data["market"] = {"price": 100, "last_update": 0}
            if "game_words" not in data:
                data["game_words"] = ["مدرسة", "تليجرام", "سيارة", "كمبيوتر", "السعودية", "برمجة"]
            if "top_btn" not in data["settings"]:
                data["settings"]["top_btn"] = {"text": "اخفاء التوب", "emoji": ""}
            return data

    return {
        "roles": {}, "muted": {}, "custom_replies": {}, "group_replies": {}, "msg_count": {},
        "stats": {"users": [], "groups": []}, "bank": {}, "market": {"price": 100, "last_update": 0},
        "group_games": {}, "group_msgs": {}, "group_names": {}, "user_names": {},
        "link_disabled": {}, "game_words": ["مدرسة", "تليجرام", "سيارة", "كمبيوتر", "السعودية", "برمجة"],
        "settings": {"top_btn": {"text": "اخفاء التوب", "emoji": ""}}, "word_replacements": {},
        "whispers": {}, "command_aliases": {}, "chat_settings": {}, "marriages": {}, "chat_templates": {}
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
    if not isinstance(text, str):
        return text
    for old_w, new_w in db.get("word_replacements", {}).items():
        text = text.replace(old_w, new_w)
    return text

ROLES = {"Dev": 6, "مالك اساسي": 5, "مالك": 4, "مدير": 3, "ادمن": 2, "مميز": 1, "عضو": 0}
ITEMS_PRICES = {"سيارة": 1000000, "ماسة": 5000000, "قصر": 15000000}
WHEEL_COST = 5000000

def get_user_role(chat_id, user_id):
    if str(user_id) == str(DEVELOPER_ID):
        return "Dev"
    chat_id = str(chat_id)
    user_id = str(user_id)
    if chat_id in db["roles"] and user_id in db["roles"][chat_id]:
        return db["roles"][chat_id][user_id]
    return "عضو"

def check_jail(user_id):
    u_bank = db["bank"].get(str(user_id))
    if not u_bank:
        return False
    if u_bank.get("is_jailed"):
        return True
    if u_bank.get("loan_due", 0) > 0 and time.time() > u_bank["loan_due"]:
        u_bank["is_jailed"] = True
        save_data(db)
        return True
    return False

def get_multiplier(user_id):
    u_bank = db["bank"].get(str(user_id))
    if u_bank and u_bank.get("x2_expiry", 0) > time.time():
        return 2
    return 1

def win_game(uid, amount):
    if uid in db["bank"]:
        mult = get_multiplier(uid)
        prize = amount * mult
        db["bank"][uid]["balance"] += prize
        save_data(db)
        return prize
    return 0

async def delete_after(message, seconds):
    await asyncio.sleep(seconds)
    try:
        await message.delete()
    except Exception:
        pass

def generate_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("الالعاب", callback_data="cmd_games"), InlineKeyboardButton("البنك", callback_data="cmd_bank")],
        [InlineKeyboardButton("الحماية", callback_data="cmd_protect"), InlineKeyboardButton("الادارة", callback_data="cmd_admin")],
        [InlineKeyboardButton("العامة", callback_data="cmd_general"), InlineKeyboardButton("المطور", callback_data="cmd_dev")],
        [InlineKeyboardButton("اغلاق القائمة", callback_data="hide_top")]
    ])

def generate_xo_board(game_id):
    game = xo_games[game_id]
    board = game["board"]
    keyboard = [
        [InlineKeyboardButton(board[0], callback_data=f"xo_{game_id}_0"), InlineKeyboardButton(board[1], callback_data=f"xo_{game_id}_1"), InlineKeyboardButton(board[2], callback_data=f"xo_{game_id}_2")],
        [InlineKeyboardButton(board[3], callback_data=f"xo_{game_id}_3"), InlineKeyboardButton(board[4], callback_data=f"xo_{game_id}_4"), InlineKeyboardButton(board[5], callback_data=f"xo_{game_id}_5")],
        [InlineKeyboardButton(board[6], callback_data=f"xo_{game_id}_6"), InlineKeyboardButton(board[7], callback_data=f"xo_{game_id}_7"), InlineKeyboardButton(board[8], callback_data=f"xo_{game_id}_8")]
    ]
    return InlineKeyboardMarkup(keyboard)

def check_xo_win(board):
    lines = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
    for a, b, c in lines:
        if board[a] == board[b] == board[c] and board[a] != "-":
            return board[a]
    if "-" not in board:
        return "Draw"
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if args and args[0].startswith("w_"):
        w_id = args[0][2:]
        if w_id in db["whispers"]:
            whisper = db["whispers"][w_id]
            if whisper["from_id"] == str(update.message.from_user.id):
                pending_whispers[update.message.from_user.id] = w_id
                await safe_reply(update.message, t("اكتب همستك الحين:"))
                return
    await safe_reply(update.message, t("هلا ومرحبا"))

def get_fast_ai_response(prompt):
    try:
        response = ai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "أنت مساعد ذكي تسولف باللهجة السعودية البحتة والعامية وبأسلوب عفوي وسريع جداً. ممنوع استخدام أي إيموجات أو رموز تعبيرية أو نجوم أو هاشتاقات أو علامات تنسيق نهائياً."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.replace("*", "").replace("#", "").replace("`", "").replace("_", "").replace("-", "").strip()
    except Exception:
        return "ابشر بس فيه ضغط بسيط جرب ثانية"

def format_reply_text(text, user, chat_id="المجموعة"):
    name = html.escape(user.first_name or "المستخدم")
    username = html.escape(f"@{user.username}" if user.username else "بدون يوزر")
    msg_cnt = db["msg_count"].get(str(user.id), 1)
    role = get_user_role(chat_id, user.id)
    pts = db['bank'].get(str(user.id), {}).get('balance', 0)
    
    return text.replace("#الاسم", name).replace("#يوزره", username).replace("#اليوزر", username).replace("#الايدي", str(user.id)).replace("#الرتبة", role).replace("#الرسائل", str(msg_cnt)).replace("#النقاط", str(pts))

async def track_bot_joins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.my_chat_member
    if result.new_chat_member.status in ["member", "administrator"]:
        chat = result.chat
        if str(chat.id) not in db["stats"]["groups"]:
            db["stats"]["groups"].append(str(chat.id))
            save_data(db)

        link = "الرابط غير متوفر"
        if result.new_chat_member.status == "administrator":
            try:
                link = await context.bot.export_chat_invite_link(chat.id)
            except Exception:
                pass

        msg = f"تمت اضافة البوت لمجموعة جديدة\nاسم المجموعة: {chat.title}\nرابط المجموعة: {link}\n\nاحصائيات البوت الحالية:\nعدد المجموعات: {len(db['stats']['groups'])}\nعدد المستخدمين: {len(db['stats']['users'])}"
        await context.bot.send_message(chat_id=DEVELOPER_ID, text=t(msg))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    data = query.data

    if data == "hide_top":
        try:
            await query.answer()
            await query.message.delete()
        except Exception:
            pass
        return

    # --- لعبة اكس او ---
    if data.startswith("xo_"):
        parts = data.split("_")
        game_id = parts[1]
        pos = int(parts[2])

        if game_id not in xo_games:
            await query.answer("اللعبة هذي منتهية او محذوفة.", show_alert=True)
            return

        game = xo_games[game_id]

        if user_id not in [game["p1"], game["p2"]]:
            await query.answer("اللعبة مو لك، لا تتدخل!", show_alert=True)
            return

        if user_id != game["turn"]:
            await query.answer("مو دورك، انتظر!", show_alert=True)
            return

        if game["board"][pos] != "-":
            await query.answer("المكان هذا محجوز، اختر غيره.", show_alert=True)
            return

        mark = "X" if user_id == game["p1"] else "O"
        game["board"][pos] = mark

        win_result = check_xo_win(game["board"])

        if win_result:
            if win_result == "Draw":
                msg = "انتهت اللعبة بالتعادل بين الطرفين!"
            else:
                winner_id = game["p1"] if win_result == "X" else game["p2"]
                winner_name = game["p1_name"] if win_result == "X" else game["p2_name"]
                prize = win_game(winner_id, 10000)
                msg = f"انتهت اللعبة بفوز {winner_name}!\nوحصل على جائزة {prize} ريال."

            try:
                await query.message.edit_text(t(msg), reply_markup=generate_xo_board(game_id), parse_mode="HTML")
            except Exception:
                await query.message.edit_text(t(msg), reply_markup=generate_xo_board(game_id))
            del xo_games[game_id]
            return

        game["turn"] = game["p2"] if user_id == game["p1"] else game["p1"]
        next_turn_name = game["p2_name"] if user_id == game["p1"] else game["p1_name"]

        try:
            await query.message.edit_text(t(f"لعبة اكس او مستمرة\nالدور الان على: {next_turn_name}"), reply_markup=generate_xo_board(game_id), parse_mode="HTML")
        except Exception:
            await query.message.edit_text(t(f"لعبة اكس او مستمرة\nالدور الان على: {next_turn_name}"), reply_markup=generate_xo_board(game_id))
        return

    # --- قوائم الأوامر ---
    menus = {
        "cmd_main": "اهلا بك في قائمة اوامر ماريا\nاختر القسم اللي تبيه من الازرار تحت:",
        "cmd_games": "اوامر الالعاب:\n\n- سرعة / لعبة سرعة\n- اكس او [بالرد]\n- لعبة كلمات\n- لعبة رياضيات\n- لعبة عواصم\n- لعبة تفكيك\n- لعبة تركيب\n- كت تويت / كت\n- صراحة / صراحه\n- لو خيروك\n- عقاب\n- زواج [بالرد] / طلاق\n- زوجي / زوجتي\n- توب القروبات\n- توب المتفاعلين",
        "cmd_bank": "اوامر البنك والاقتصاد:\n\n- انشاء حساب بنكي\n- فلوسي\n- راتب\n- بخشيش\n- زرف [بالرد]\n- استثمار / مضاربه [المبلغ]\n- حظ\n- العجله\n- ممتلكاتي\n- شراء / بيع / اهداء [العدد] [الشيء]\n- سعر الاسهم / شراء اسهم / بيع اسهم\n- قرض / ديوني / سداد ديوني\n- ديونه / سداد ديونه [بالرد]\n- سجني",
        "cmd_protect": "اوامر الحماية (للمشرفين فقط):\n(تطبق على الأعضاء اللي رتبتهم اقل من مميز)\n\n- قفل الروابط / فتح الروابط\n- قفل الصور / فتح الصور\n- قفل الملصقات / فتح الملصقات\n- قفل التوجيه / فتح التوجيه",
        "cmd_admin": "اوامر الادارة والمشرفين:\n\n- حظر / طرد / كتم / تقييد [بالرد]\n- الغاء حظر / الغاء كتم / الغاء تقييد [بالرد]\n- مسح [بالرد]\n- تثبيت / الغاء التثبيت [بالرد]\n- رفع / تنزيل [بالرد]\n- ضع اسم / ضع وصف\n- تفعيل الرابط / تعطيل الرابط\n- اضف كلمة\n- اضف رد / حذف رد (للمالك - خاصة بالقروب)\n- تغيير كليشة الايدي / تغيير كليشة الاوامر (للمالك)",
        "cmd_general": "الاوامر العامة:\n\n- ايدي / ا / id\n- معلوماتي\n- القروب\n- الوقت / التاريخ\n- احسب [مسألة]\n- زخرفة [نص]\n- قول [نص]\n- رتبتي\n- رتبته [بالرد]\n- الرابط\n- الردود العامه\n- تيست [سؤالك]\n- اهمس / ه [بالرد]\n- المطور / نادي المطور\n- الاوامر / م",
        "cmd_dev": "اوامر المطور (Dev):\n\n- اضف امر (لصنع اختصار لأي امر)\n- صنع زر (لارسال رسالة بزر شفاف ورابط)\n- تغير كلمه (لاستبدال الكلمات بالنظام الذكي)\n- تعديل زر (زر اخفاء التوب)\n- اضف رد عام / حذف رد عام"
    }

    if data in menus:
        if data == "cmd_dev" and user_id != str(DEVELOPER_ID):
            await query.answer(t("معليش، هذا القسم خاص بالمطور فقط! يمنع الدخول."), show_alert=True)
            return
        await query.answer()
        reply_m = generate_menu_keyboard() if data == "cmd_main" else InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="cmd_main")]])
        try:
            await query.message.edit_text(t(menus[data]), reply_markup=reply_m, parse_mode="HTML")
        except:
            await query.message.edit_text(t(menus[data]), reply_markup=reply_m)
        return

    # --- نظام الهمسات بالأزرار ---
    if data.startswith("sw_"):
        w_id = data[3:]
        if w_id in db.get("whispers", {}):
            whisper = db["whispers"][w_id]
            if user_id in [whisper["from_id"], whisper["to_id"]]:
                await query.answer(text=whisper["text"], show_alert=True)
                return
            else:
                await query.answer(text=t("الهمسة مو لك، لا تتدخل"), show_alert=True)
                return
        await query.answer(text=t("الهمسة هذي قديمة ومحذوفة"), show_alert=True)
        return

    if data.startswith("rw_"):
        parts = data.split("_", 2)
        if len(parts) >= 3:
            target_id = parts[1]
            target_name = parts[2]

            w_id = str(random.randint(100000, 999999))
            bot_info = await context.bot.get_me()

            db["whispers"][w_id] = {
                "from_id": user_id,
                "from_name": query.from_user.first_name,
                "to_id": target_id,
                "to_name": target_name,
                "chat_id": str(query.message.chat.id),
                "text": ""
            }
            save_data(db)

            btn_url = f"https://t.me/{bot_info.username}?start=w_{w_id}"
            keyboard = [[InlineKeyboardButton(t("اهمس هنا"), url=btn_url)]]

            await context.bot.send_message(
                chat_id=query.message.chat.id,
                text=t(f"تم تحديد الهمسه لـ {target_name}\nاضغط الزر لكتابة الهمسة"),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            await query.answer()
        return

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.from_user:
        return

    chat_id = str(update.message.chat_id)
    user = update.message.from_user
    user_id_int = user.id
    user_id = str(user.id)

    issuer_role = get_user_role(chat_id, int(user_id))
    issuer_weight = ROLES[issuer_role]

    # سحب الرسالة بصيغة HTML لحفظ الرموز المتحركة
    raw_text = update.message.text or update.message.caption
    if not raw_text:
        return
    text = raw_text.strip()
    html_text = update.message.text_html or update.message.caption_html or text

    # --- نظام الحماية المتطور ---
    if update.message.chat.type in ['group', 'supergroup'] and issuer_weight < ROLES["مميز"]:
        if chat_id not in db.get("chat_settings", {}):
            db.setdefault("chat_settings", {})[chat_id] = {"links": False, "photos": False, "stickers": False, "forwards": False}

        c_set = db["chat_settings"][chat_id]
        must_delete = False
        reason = ""

        if c_set.get("photos") and update.message.photo:
            must_delete = True
            reason = "الصور"
        elif c_set.get("stickers") and update.message.sticker:
            must_delete = True
            reason = "الملصقات"
        elif c_set.get("forwards") and update.message.forward_date:
            must_delete = True
            reason = "التوجيه"

        text_to_check = update.message.text or update.message.caption or ""
        if c_set.get("links") and ("http://" in text_to_check or "https://" in text_to_check or "t.me/" in text_to_check):
            must_delete = True
            reason = "الروابط"

        if must_delete:
            try:
                await update.message.delete()
                warning_msg = await safe_reply(update.message, t(f"عذرا عزيزي {user.first_name}، يمنع ارسال {reason} في هذه المجموعة."))
                asyncio.create_task(delete_after(warning_msg, 5))
            except Exception:
                pass
            return

    # --- استقبال نص الهمسة في الخاص ---
    if update.message.chat.type == "private":
        if user_id_int in pending_whispers:
            w_id = pending_whispers[user_id_int]
            if w_id in db.get("whispers", {}):
                db["whispers"][w_id]["text"] = text
                save_data(db)

                whisper = db["whispers"][w_id]
                chat_id_group = whisper["chat_id"]

                keyboard = [
                    [InlineKeyboardButton(t("رؤية الهمسة"), callback_data=f"sw_{w_id}")],
                    [InlineKeyboardButton(t(f"اهمس لـ {whisper['from_name']}"), callback_data=f"rw_{whisper['from_id']}_{whisper['from_name']}")]
                ]

                msg = f"الهمسه لـ {whisper['to_name']}\nمن {whisper['from_name']}"
                try:
                    await context.bot.send_message(
                        chat_id=chat_id_group,
                        text=t(msg),
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    await safe_reply(update.message, t("تم ارسال الهمسة للقروب بنجاح!"))
                except Exception:
                    await safe_reply(update.message, t("فشلت عملية ارسال الهمسة، يمكن البوت انطرد من القروب."))

                del pending_whispers[user_id_int]
                return

    # تحديث إحصائيات المستخدمين والقروبات
    db["user_names"][user_id] = user.first_name
    if update.message.chat.type in ['group', 'supergroup']:
        if chat_id not in db["group_msgs"]:
            db["group_msgs"][chat_id] = {}
        db["group_names"][chat_id] = update.message.chat.title
        db["group_msgs"][chat_id][user_id] = db["group_msgs"][chat_id].get(user_id, 0) + 1

    if user_id not in db["stats"]["users"]:
        db["stats"]["users"].append(user_id)
    if chat_id not in db["stats"]["groups"] and update.message.chat.type in ['group', 'supergroup']:
        db["stats"]["groups"].append(chat_id)

    db["msg_count"][user_id] = db["msg_count"].get(user_id, 0) + 1
    save_data(db)

    # فحص الكتم
    if chat_id in db["muted"] and user_id in db["muted"][chat_id]:
        try:
            await update.message.delete()
        except Exception:
            pass
        return

    # --- نظام اختصارات الأوامر الذكي ---
    aliases = db.get("command_aliases", {})
    if text in aliases:
        text = aliases[text]
    else:
        for alias, orig in aliases.items():
            if text.startswith(alias + " "):
                text = orig + text[len(alias):]
                break

    text_normalized = text.replace("إلغاء", "الغاء").replace("فك ", "الغاء ")

    # --- أوامر القائمة الرئيسية التفاعلية ---
    if text in ["الاوامر", "اوامري", "م", "أوامر", "الاوامر"]:
        cmd_template = db.get("chat_templates", {}).get(chat_id, {}).get("commands", "اهلا بك في قائمة اوامر ماريا\nاختر القسم اللي تبيه من الازرار تحت:")
        formatted_cmd = format_reply_text(cmd_template, user, chat_id)
        await safe_reply(update.message, t(formatted_cmd), reply_markup=generate_menu_keyboard())
        return

    # ------------------ نظام اختصار الأوامر ------------------
    if user_id_int in adding_alias_state:
        state = adding_alias_state[user_id_int]
        step = state.get("step")

        if step == "waiting_for_old_cmd":
            state["old_cmd"] = text
            state["step"] = "waiting_for_new_cmd"
            await safe_reply(update.message, t("ممتاز، الحين ارسل الاختصار أو الأمر الجديد اللي تبيه (مثلاً: ظ):"))
            return

        elif step == "waiting_for_new_cmd":
            old_cmd = state["old_cmd"]
            db["command_aliases"][text] = old_cmd
            save_data(db)
            del adding_alias_state[user_id_int]
            await safe_reply(update.message, t(f"تم بنجاح! الحين تقدر تستخدم '{text}' بدال '{old_cmd}'."))
            return

    if text == "اضف امر":
        if issuer_weight < ROLES["مالك"]:
            await safe_reply(update.message, t("معليش هذا الامر للمالك والـ Dev فقط"))
            return
        adding_alias_state[user_id_int] = {"step": "waiting_for_old_cmd"}
        await safe_reply(update.message, t("ارسل الأمر الأساسي اللي تبي تسوي له اختصار (مثلاً: حظر)"))
        return

    # ------------------ نظام تغيير الكلمات (الذكي بالرموز) ------------------
    if user_id_int in changing_word_state:
        state = changing_word_state[user_id_int]
        step = state.get("step")

        if step == "waiting_for_old_word":
            state["old_word"] = text
            state["step"] = "waiting_for_new_word"
            await safe_reply(update.message, t("ممتاز، الحين اكتب الكلمة أو الجملة الجديدة اللي تبيها تطلع بدالها:"))
            return

        elif step == "waiting_for_new_word":
            old_word = state["old_word"]
            db["word_replacements"][old_word] = html_text
            save_data(db)
            del changing_word_state[user_id_int]
            await safe_reply(update.message, t(f"تم التغيير بنجاح! من اليوم أي رسالة فيها '{old_word}' بتتغير إلى الجديدة"))
            return

    if text == "تغير كلمه":
        if issuer_weight < ROLES["مالك"]:
            await safe_reply(update.message, t("معليش هذا الامر للمالك والـ Dev فقط"))
            return
        changing_word_state[user_id_int] = {"step": "waiting_for_old_word"}
        await safe_reply(update.message, t("اكتب الكلمة الأساسية اللي تبي تغيرها (نفس ما تطلع بالبوت بالضبط):"))
        return

    # ------------------ نظام تغيير الكليشات (الايدي والاوامر) ------------------
    if user_id_int in changing_template_state:
        state = changing_template_state[user_id_int]
        target = state.get("target")

        if target == "id":
            if chat_id not in db["chat_templates"]: db["chat_templates"][chat_id] = {}
            db["chat_templates"][chat_id]["id"] = html_text
            save_data(db)
            del changing_template_state[user_id_int]
            await safe_reply(update.message, t("تم حفظ كليشة الايدي الجديدة بنجاح للمجموعة!"))
            return
            
        elif target == "cmd":
            if chat_id not in db["chat_templates"]: db["chat_templates"][chat_id] = {}
            db["chat_templates"][chat_id]["commands"] = html_text
            save_data(db)
            del changing_template_state[user_id_int]
            await safe_reply(update.message, t("تم حفظ كليشة الاوامر الجديدة بنجاح للمجموعة!"))
            return

    if text == "تغيير كليشة الايدي":
        if issuer_weight < ROLES["مالك"]:
            await safe_reply(update.message, t("معليش هذا الامر للمالك والـ Dev فقط"))
            return
        changing_template_state[user_id_int] = {"target": "id"}
        await safe_reply(update.message, t("ارسل الكليشة اللي تبيها للايدي الحين.\nتقدر تستخدم:\n#الاسم\n#الايدي\n#يوزره\n#الرتبة\n#الرسائل\n#النقاط"))
        return

    if text == "تغيير كليشة الاوامر":
        if issuer_weight < ROLES["مالك"]:
            await safe_reply(update.message, t("معليش هذا الامر للمالك والـ Dev فقط"))
            return
        changing_template_state[user_id_int] = {"target": "cmd"}
        await safe_reply(update.message, t("ارسل الكليشة اللي تبيها تظهر فوق أزرار الأوامر.\nتقدر تستخدم المتغيرات مثل #الاسم وغيرها."))
        return

    # ------------------ الأوامر والمعلومات العامة ------------------
    if text == "الوقت":
        ksa_time = datetime.utcnow() + timedelta(hours=3)
        await safe_reply(update.message, t(f"الوقت الان في السعودية: {ksa_time.strftime('%I:%M %p')}"))
        return

    if text == "التاريخ":
        ksa_time = datetime.utcnow() + timedelta(hours=3)
        await safe_reply(update.message, t(f"التاريخ اليوم: {ksa_time.strftime('%Y-%m-%d')}"))
        return

    if text == "معلوماتي":
        msg = f"معلوماتك الشخصية:\nالاسم: {user.first_name}\nاليوزر: @{user.username if user.username else 'لا يوجد'}\nالايدي: {user.id}\nرتبتك بالقروب: {issuer_role}\nرسائلك: {db['msg_count'].get(str(user.id), 1)}\nرصيدك البنكي: {db['bank'].get(str(user.id), {}).get('balance', 0)} ريال"
        await safe_reply(update.message, t(msg))
        return

    if text == "القروب":
        if update.message.chat.type == "private":
            await safe_reply(update.message, t("هذا الامر للمجموعات فقط"))
            return
        msg = f"معلومات المجموعة:\nالاسم: {update.message.chat.title}\nالايدي: {update.message.chat.id}\nعدد الرسائل المسجلة: {sum(db['group_msgs'].get(chat_id, {}).values())}"
        await safe_reply(update.message, t(msg))
        return

    if text.startswith("احسب "):
        calc = text.replace("احسب ", "").strip()
        try:
            allowed = "0123456789+-*/(). "
            if all(c in allowed for c in calc):
                res = eval(calc)
                await safe_reply(update.message, t(f"الناتج: {res}"))
            else:
                await safe_reply(update.message, t("ارقام وعمليات حسابية فقط يا ذكي"))
        except Exception:
            await safe_reply(update.message, t("مسألة خاطئة، تأكد من الارقام"))
        return

    if text.startswith("زخرفة "):
        word = text.replace("زخرفة ", "").strip()
        zakhrafa = " ".join([c + "ـ" for c in word])
        await safe_reply(update.message, t(f"الكلمة المزخرفة:\n{zakhrafa}"))
        return

    if text.startswith("قول "):
        word = text.replace("قول ", "").strip()
        try:
            await update.message.delete()
        except Exception:
            pass
        await safe_reply(update.message, t(word))
        return

    # ------------------ ألعاب التليجرام ------------------
    if text in ["كت تويت", "كت"]:
        await safe_reply(update.message, t(random.choice(CUT_TWEET)))
        return

    if text in ["صراحة", "صراحه"]:
        await safe_reply(update.message, t(random.choice(SARAHA)))
        return

    if text in ["لو خيروك"]:
        await safe_reply(update.message, t(random.choice(KHYROK)))
        return

    if text in ["عقاب"]:
        await safe_reply(update.message, t(random.choice(EQAB)))
        return

    # ------------------ نظام الزواج واكس او بالرد ------------------
    if update.message.reply_to_message:
        target_id = str(update.message.reply_to_message.from_user.id)

        if text == "زواج":
            if target_id == user_id:
                await safe_reply(update.message, t("تبي تتزوج نفسك؟ صاحي انت!"))
                return
            if update.message.reply_to_message.from_user.is_bot:
                await safe_reply(update.message, t("البوتات للبرمجة مو للزواج"))
                return
            if user_id in db.get("marriages", {}):
                await safe_reply(update.message, t("انت متزوج من قبل، طلق اول!"))
                return
            if target_id in db.get("marriages", {}):
                await safe_reply(update.message, t("هذا الشخص متزوج، ابعد عن المشاكل!"))
                return

            db["marriages"][user_id] = target_id
            db["marriages"][target_id] = user_id
            save_data(db)
            msg = f"مبروووك! تم زواج {user.first_name} من {update.message.reply_to_message.from_user.first_name} بالرفاه والبنين"
            await safe_reply(update.message, t(msg))
            return

        if text in ["اكس او", "لعبة اكس او"]:
            if target_id == user_id:
                await safe_reply(update.message, t("تبي تلعب مع نفسك؟"))
                return
            if update.message.reply_to_message.from_user.is_bot:
                await safe_reply(update.message, t("ما تقدر تتحدى البوت بالاكس او"))
                return

            game_id = str(update.message.message_id)
            xo_games[game_id] = {
                "p1": user_id,
                "p1_name": user.first_name,
                "p2": target_id,
                "p2_name": update.message.reply_to_message.from_user.first_name,
                "board": ["-"] * 9,
                "turn": user_id
            }
            msg = f"لعبة اكس او بين {user.first_name} (X) و {update.message.reply_to_message.from_user.first_name} (O)\nالدور الان على: {user.first_name}"
            await safe_reply(update.message, t(msg), reply_markup=generate_xo_board(game_id))
            return

    if text == "طلاق":
        if user_id in db.get("marriages", {}):
            partner_id = db["marriages"][user_id]
            del db["marriages"][user_id]
            if partner_id in db["marriages"]:
                del db["marriages"][partner_id]
            save_data(db)
            await safe_reply(update.message, t("ابغض الحلال.. تم الطلاق بنجاح وانفصلتوا"))
            return
        await safe_reply(update.message, t("انت مو متزوج اصلا عشان تطلق!"))
        return

    if text in ["زوجي", "زوجتي"]:
        if user_id in db.get("marriages", {}):
            partner_id = db["marriages"][user_id]
            partner_name = db["user_names"].get(partner_id, "عضو مجهول")
            await safe_reply(update.message, t(f"شريك حياتك هو: {partner_name}"))
            return
        await safe_reply(update.message, t("انت سنجل بائس مو متزوج"))
        return

    # ------------------ نظام الألعاب المصغرة مع التوقيت ------------------
    if chat_id in active_math_game and text == active_math_game[chat_id]["answer"]:
        game_data = active_math_game.pop(chat_id)
        elapsed = time.time() - game_data["start"]
        prize = win_game(user_id, 3000)
        msg = f"كفو يا {user.first_name} جوابك صح!\nاستغرقت {elapsed:.2f} ثانية"
        if prize:
            msg += f"\nربحت {prize} ريال بالبنك"
        await safe_reply(update.message, t(msg))
        return

    if chat_id in active_capitals_game and text == active_capitals_game[chat_id]["answer"]:
        game_data = active_capitals_game.pop(chat_id)
        elapsed = time.time() - game_data["start"]
        prize = win_game(user_id, 4000)
        msg = f"وحش يا {user.first_name} الجواب هو {text}!\nاستغرقت {elapsed:.2f} ثانية"
        if prize:
            msg += f"\nربحت {prize} ريال بالبنك"
        await safe_reply(update.message, t(msg))
        return

    if chat_id in active_tafkik_game and text == active_tafkik_game[chat_id]["answer"]:
        game_data = active_tafkik_game.pop(chat_id)
        elapsed = time.time() - game_data["start"]
        prize = win_game(user_id, 3000)
        msg = f"بطل يا {user.first_name} فككت الكلمة صح!\nاستغرقت {elapsed:.2f} ثانية"
        if prize:
            msg += f"\nربحت {prize} ريال بالبنك"
        await safe_reply(update.message, t(msg))
        return

    if chat_id in active_tarkib_game and text == active_tarkib_game[chat_id]["answer"]:
        game_data = active_tarkib_game.pop(chat_id)
        elapsed = time.time() - game_data["start"]
        prize = win_game(user_id, 3000)
        msg = f"ذيبان يا {user.first_name} ركبت الكلمة صح!\nاستغرقت {elapsed:.2f} ثانية"
        if prize:
            msg += f"\nربحت {prize} ريال بالبنك"
        await safe_reply(update.message, t(msg))
        return

    if chat_id in active_speed_game and text == active_speed_game[chat_id]["word"]:
        game = active_speed_game[chat_id]
        if user_id not in [w["id"] for w in game["winners"]]:
            elapsed = time.time() - game["start"]
            prize = 5000 if len(game["winners"]) == 0 else (3000 if len(game["winners"]) == 1 else 1000)
            game["winners"].append({"id": user_id, "name": user.first_name, "time": elapsed, "prize": prize})
            win_game(user_id, prize)

            if len(game["winners"]) == 3:
                msg = "انتهت لعبة السرعة!\nالفائزين:\n"
                for i, w in enumerate(game["winners"]):
                    msg += f"{i+1}- {w['name']} (استغرق {w['time']:.2f} ث) ربح {w['prize']}\n"
                del active_speed_game[chat_id]
                await safe_reply(update.message, t(msg))
                return
            else:
                await safe_reply(update.message, t(f"المركز {len(game['winners'])} لـ {user.first_name} في {elapsed:.2f} ثانية! باقي {3 - len(game['winners'])} مراكز"))
                return

    if text in ["رياضيات", "لعبة رياضيات"]:
        a = random.randint(1, 100)
        b = random.randint(1, 100)
        op = random.choice(["+", "-", "*"])
        active_math_game[chat_id] = {"answer": str(eval(f"{a}{op}{b}")), "start": time.time()}
        await safe_reply(update.message, t(f"أول شخص يحل هالمسألة يفوز:\n{a} {op} {b} = ؟"))
        return

    if text in ["عواصم", "لعبة عواصم"]:
        country, capital = random.choice(list(CAPITALS.items()))
        active_capitals_game[chat_id] = {"answer": capital, "start": time.time()}
        await safe_reply(update.message, t(f"أول شخص يكتب عاصمة ( {country} ) يفوز:"))
        return

    if text in ["تفكيك", "لعبة تفكيك"]:
        word = random.choice(db["game_words"])
        active_tafkik_game[chat_id] = {"answer": " ".join(list(word)), "start": time.time()}
        await safe_reply(update.message, t(f"أول شخص يفكك هالكلمة يفوز:\n{word}"))
        return

    if text in ["تركيب", "لعبة تركيب"]:
        word = random.choice(db["game_words"])
        active_tarkib_game[chat_id] = {"answer": word, "start": time.time()}
        await safe_reply(update.message, t(f"أول شخص يركب هالحروف يفوز:\n{' '.join(list(word))}"))
        return

    if text in ["سرعة", "سرعه", "لعبة سرعة", "لعبة سرعه"]:
        word = random.choice(db["game_words"])
        active_speed_game[chat_id] = {"word": word, "start": time.time(), "winners": []}
        await safe_reply(update.message, t(f"اسرع 3 يكتبون هالكلمة يفوزون:\n\n{word}"))
        return

    # ------------------ نظام الأقفال والإدارة المتطورة ------------------
    if text.startswith("قفل ") or text.startswith("فتح "):
        if issuer_weight < ROLES["ادمن"]:
            await safe_reply(update.message, t("هذا الأمر للمشرفين وأعلى"))
            return

        if chat_id not in db.get("chat_settings", {}):
            db.setdefault("chat_settings", {})[chat_id] = {"links": False, "photos": False, "stickers": False, "forwards": False}

        c_set = db["chat_settings"][chat_id]
        parts = text.split()
        if len(parts) < 2:
            return

        action = parts[0]
        target = parts[1]
        state = True if action == "قفل" else False

        if target in ["الروابط", "روابط"]:
            c_set["links"] = state
        elif target in ["الصور", "صور"]:
            c_set["photos"] = state
        elif target in ["الملصقات", "ملصقات"]:
            c_set["stickers"] = state
        elif target in ["التوجيه", "توجيه"]:
            c_set["forwards"] = state
        else:
            return

        save_data(db)
        await safe_reply(update.message, t(f"تم {action} {target} بنجاح"))
        return

    if text.startswith("ضع اسم "):
        if issuer_weight < ROLES["ادمن"]:
            return
        new_name = text.replace("ضع اسم ", "").strip()
        try:
            await context.bot.set_chat_title(chat_id, new_name)
            await safe_reply(update.message, t("تم تغيير اسم المجموعة بنجاح"))
        except Exception:
            await safe_reply(update.message, t("البوت ماله صلاحية يغير الاسم"))
        return

    if text.startswith("ضع وصف "):
        if issuer_weight < ROLES["ادمن"]:
            return
        new_desc = text.replace("ضع وصف ", "").strip()
        try:
            await context.bot.set_chat_description(chat_id, new_desc)
            await safe_reply(update.message, t("تم تغيير وصف المجموعة بنجاح"))
        except Exception:
            await safe_reply(update.message, t("البوت ماله صلاحية يغير الوصف"))
        return

    if update.message.reply_to_message:
        if text == "تثبيت":
            if issuer_weight < ROLES["ادمن"]:
                return
            try:
                await update.message.reply_to_message.pin()
                await safe_reply(update.message, t("تم تثبيت الرسالة"))
            except Exception:
                await safe_reply(update.message, t("ما عندي صلاحية تثبيت"))
            return

        if text == "الغاء التثبيت" or text == "الغاء تثبيت":
            if issuer_weight < ROLES["ادمن"]:
                return
            try:
                await update.message.reply_to_message.unpin()
                await safe_reply(update.message, t("تم الغاء تثبيت الرسالة"))
            except Exception:
                await safe_reply(update.message, t("ما عندي صلاحية"))
            return

    # ------------------ نظام صنع الأزرار الحرة بالروابط ------------------
    if user_id_int in creating_button_state:
        state = creating_button_state[user_id_int]
        step = state.get("step")

        if step == "waiting_for_msg_text":
            state["msg_text"] = text
            state["step"] = "waiting_for_btn_text"
            await safe_reply(update.message, t("ممتاز، الحين ارسل النص اللي تبيه يطلع داخل الزر (تقدر تحط ايموجي كيبورد عادي معه):"))
            return

        elif step == "waiting_for_btn_text":
            state["btn_text"] = text
            state["step"] = "waiting_for_btn_url"
            await safe_reply(update.message, t("بطل، اخر خطوة: ارسل الرابط اللي يوديه الزر (لازم يبدأ بـ http أو https):"))
            return

        elif step == "waiting_for_btn_url":
            if not text.startswith("http"):
                await safe_reply(update.message, t("الرابط لازم يبدأ بـ http أو https، حاول مره ثانية:"))
                return

            msg_text = state["msg_text"]
            btn_text = state["btn_text"]
            btn_url = text

            keyboard = [[InlineKeyboardButton(btn_text, url=btn_url)]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            del creating_button_state[user_id_int]
            await safe_reply(update.message, msg_text, reply_markup=reply_markup)
            await safe_reply(update.message, t("تم انشاء الزر وارسال الرسالة بنجاح!"))
            return

    if text == "صنع زر":
        if issuer_weight < ROLES["ادمن"]:
            await safe_reply(update.message, t("معليش هذا الامر للادارة فقط"))
            return
        creating_button_state[user_id_int] = {"step": "waiting_for_msg_text"}
        await safe_reply(update.message, t("حلو، وش تبي يكون النص الأساسي للرسالة؟ (الكلام اللي فوق الزر)"))
        return

    # ------------------ نظام إضافة الردود والزر ------------------
    if user_id_int in adding_reply_state:
        state = adding_reply_state[user_id_int]
        step = state.get("step")
        target_type = state.get("type", "general") 

        if step == "waiting_for_keyword":
            state["keyword"] = text
            state["step"] = "waiting_for_reply_content"
            help_message = (
                "حسنا يمكنك اضافة النص مع رموز البريميوم بحرية\n"
                "ويمكنك تخصيص الرد بتلك الطريقة :\n"
                "#الاسم - اسم العضو\n"
                "#يوزره - يوزر المستخدم\n"
                "#الايدي - ايدي المستخدم\n"
                "#الرتبة - رتبة المستخدم\n"
                "#الرسائل - عدد الرسائل\n"
                "#النقاط - نقاط المستخدم"
            )
            await safe_reply(update.message, t(help_message))
            return

        elif step == "waiting_for_reply_content":
            keyword = state.get("keyword")
            if keyword:
                reply_to_save = html_text
                if target_type == "general":
                    if keyword not in db["custom_replies"]:
                        db["custom_replies"][keyword] = []
                    db["custom_replies"][keyword].append(reply_to_save)
                else:
                    if chat_id not in db["group_replies"]:
                        db["group_replies"][chat_id] = {}
                    if keyword not in db["group_replies"][chat_id]:
                        db["group_replies"][chat_id][keyword] = []
                    db["group_replies"][chat_id][keyword].append(reply_to_save)
                
                save_data(db)
                reply_msg = "تم اضافة الرد لكل المجموعات برموزه" if target_type == "general" else "تم اضافة الرد لهذه المجموعة برموزها"
                await safe_reply(update.message, t(reply_msg))
                state["step"] = "waiting_for_more_replies"
            return

        elif step == "waiting_for_more_replies":
            keyword = state.get("keyword")
            if text.lower() in ["تم", "خلاص"]:
                del adding_reply_state[user_id_int]
                await safe_reply(update.message, t("تم الانتهاء وحفظ جميع الردود بنجاح"))
                return
            else:
                if keyword:
                    reply_to_save = html_text
                    if target_type == "general":
                        db["custom_replies"][keyword].append(reply_to_save)
                        count = len(db["custom_replies"][keyword])
                    else:
                        db["group_replies"][chat_id][keyword].append(reply_to_save)
                        count = len(db["group_replies"][chat_id][keyword])
                    save_data(db)
                    await safe_reply(update.message, t(f"تم اضافة الرد باقى {count}\nتم اضافة الرد ارسل رد اخر او ارسل تم"))
                return

    if text in ["اضف رد عام"]:
        if user_id != str(DEVELOPER_ID):
            await safe_reply(update.message, t("معليش هذا الامر للمطور فقط"))
            return
        adding_reply_state[user_id_int] = {"step": "waiting_for_keyword", "type": "general"}
        await safe_reply(update.message, t("حسنا الان ارسل كلمة الرد العام"))
        return

    if text in ["اضف رد"]:
        if issuer_weight < ROLES["مالك"]:
            await safe_reply(update.message, t("معليش هذا الامر للمالك والـ Dev فقط"))
            return
        adding_reply_state[user_id_int] = {"step": "waiting_for_keyword", "type": "group"}
        await safe_reply(update.message, t("حسنا الان ارسل كلمة الرد الخاص بمجموعتك"))
        return

    if text.startswith("حذف رد عام "):
        if user_id != str(DEVELOPER_ID):
            await safe_reply(update.message, t("هذا الامر للمطور فقط"))
            return
        keyword = text.replace("حذف رد عام ", "").strip()
        if keyword in db["custom_replies"]:
            del db["custom_replies"][keyword]
            save_data(db)
            await safe_reply(update.message, t(f"تم حذف الرد العام الخاص بـ: {keyword}"))
        else:
            await safe_reply(update.message, t("الكلمة مو موجودة بقائمة الردود العامة"))
        return

    if text.startswith("حذف رد "):
        if issuer_weight < ROLES["مالك"]:
            await safe_reply(update.message, t("معليش هذا الامر للمالك والـ Dev فقط"))
            return
        keyword = text.replace("حذف رد ", "").strip()
        if chat_id in db.get("group_replies", {}) and keyword in db["group_replies"][chat_id]:
            del db["group_replies"][chat_id][keyword]
            save_data(db)
            await safe_reply(update.message, t(f"تم حذف رد القروب الخاص بـ: {keyword}"))
        else:
            await safe_reply(update.message, t("الكلمة مو موجودة بقائمة ردود القروب"))
        return

    group_replies = db.get("group_replies", {}).get(chat_id, {})
    if text in group_replies:
        possible_replies = group_replies[text]
        chosen_reply = random.choice(possible_replies)
        formatted_reply = format_reply_text(chosen_reply, user, chat_id)
        await safe_reply(update.message, t(formatted_reply))
        return
    elif text in db["custom_replies"]:
        possible_replies = db["custom_replies"][text]
        chosen_reply = random.choice(possible_replies)
        formatted_reply = format_reply_text(chosen_reply, user, chat_id)
        await safe_reply(update.message, t(formatted_reply))
        return

    # ------------------ نظام لعبة الكلمات القديمة ------------------
    if chat_id in active_word_game:
        if text == active_word_game[chat_id]["answer"]:
            game_data = active_word_game.pop(chat_id)
            elapsed = time.time() - game_data["start"]
            prize = win_game(user_id, 5000)
            msg = f"كفو يا {user.first_name} جبتها صح والكلمة هي: {text}\nاستغرقت {elapsed:.2f} ثانية"
            if prize:
                msg += f"\nتم اضافة {prize} ريال لحسابك البنكي"
            await safe_reply(update.message, t(msg))
            return

    if text.startswith("اضف كلمة "):
        if issuer_weight < ROLES["ادمن"]:
            await safe_reply(update.message, t("هذا الامر للادمن واعلى"))
            return
        new_word = text.replace("اضف كلمة ", "").strip()
        if new_word and new_word not in db["game_words"]:
            db["game_words"].append(new_word)
            save_data(db)
            await safe_reply(update.message, t(f"تم اضافة الكلمة الى قائمة الالعاب بنجاح"))
        else:
            await safe_reply(update.message, t("الكلمة موجودة من قبل"))
        return

    if text in ["لعبة كلمات", "لعبة الكلمات"]:
        if not db["game_words"]:
            await safe_reply(update.message, t("مافي كلمات مضافة، ضيفوا كلمات اول بامر: اضف كلمة"))
            return
        word = random.choice(db["game_words"])
        letters = list(word)
        random.shuffle(letters)
        shuffled = "".join(letters)
        if shuffled == word and len(word) > 1:
            random.shuffle(letters)
            shuffled = "".join(letters)
        active_word_game[chat_id] = {"answer": word, "start": time.time()}
        await safe_reply(update.message, t(f"اسرع واحد يرتب هالكلمة يفوز:\n\n{shuffled}"))
        return

    # ------------------ نظام الرابط ------------------
    if text == "تعطيل الرابط":
        if issuer_weight < ROLES["ادمن"]:
            await safe_reply(update.message, t("هذا الامر للادمن واعلى"))
            return
        db["link_disabled"][chat_id] = True
        save_data(db)
        await safe_reply(update.message, t("تم تعطيل الرابط بنجاح"))
        return

    if text == "تفعيل الرابط":
        if issuer_weight < ROLES["ادمن"]:
            await safe_reply(update.message, t("هذا الامر للادمن واعلى"))
            return
        db["link_disabled"][chat_id] = False
        save_data(db)
        await safe_reply(update.message, t("تم تفعيل الرابط بنجاح"))
        return

    if text == "الرابط":
        if db["link_disabled"].get(chat_id, False):
            await safe_reply(update.message, t("المشرفين عطلوا الرابط"))
            return
        try:
            link = await context.bot.export_chat_invite_link(chat_id)
            await safe_reply(update.message, t(f"رابط المجموعة:\n{link}"))
        except Exception:
            await safe_reply(update.message, t("البوت مو مشرف او ماعنده صلاحية دعوة المستخدمين"))
        return

    if text == "الردود العامه":
        replies = db.get("custom_replies", {})
        if not replies:
            await safe_reply(update.message, t("مافي ردود عامة مضافة حاليا"))
            return
        msg = "قائمة الردود العامة المضافة:\n\n"
        for i, key in enumerate(replies.keys(), 1):
            msg += f"{i} - {key}\n"
        await safe_reply(update.message, t(msg))
        return

    # ------------------ نظام البنك والاقتصاد المتكامل ------------------
    game_commands = ["انشاء حساب بنكي", "راتب", "بخشيش", "زرف", "استثمار", "مضاربه", "حظ", "العجله", "ممتلكاتي", "سعر الاسهم", "قرض", "سجني", "ديوني", "سداد ديوني", "فلوسي"]
    is_game_cmd = any(text.startswith(cmd) for cmd in game_commands + ["شراء ", "بيع ", "اهداء ", "شراء اسهم ", "بيع اسهم ", "ديونه ", "سداد ديونه "])

    if is_game_cmd:
        if update.message.chat.type in ['group', 'supergroup']:
            db["group_games"][chat_id] = db["group_games"].get(chat_id, 0) + 1
            save_data(db)

        if text == "انشاء حساب بنكي":
            if user_id in db["bank"]:
                await safe_reply(update.message, t("عندك حساب بنكي من قبل"))
            else:
                db["bank"][user_id] = {
                    "balance": 50000, "inventory": {}, "loan": 0, "loan_due": 0,
                    "is_jailed": False, "x2_expiry": 0, "stocks": 0, "last_salary": 0
                }
                save_data(db)
                await safe_reply(update.message, t("تم انشاء حسابك البنكي بنجاح وتم ايداع 50 الف ريال هدية ترحيبية"))
            return

        if user_id not in db["bank"]:
            await safe_reply(update.message, t("لازم تسوي حساب بنكي اول، اكتب: انشاء حساب بنكي"))
            return

        if check_jail(user_id) and text not in ["ديوني", "سداد ديوني", "سجني"]:
            await safe_reply(update.message, t("انت مسجون حاليا بسبب الديون وماتقدر تلعب حتى تسدد، اكتب: ديوني"))
            return

        mult = get_multiplier(user_id)
        u_bank = db["bank"][user_id]

        if text == "فلوسي":
            await safe_reply(update.message, t(f"فلوسك بالبنك: {u_bank['balance']} ريال"))
            return

        if text == "راتب":
            if time.time() - u_bank.get("last_salary", 0) < 3600:
                await safe_reply(update.message, t("باقي وقت على راتبك، الراتب كل ساعة"))
                return
            amt = random.randint(10000, 50000) * mult
            u_bank["balance"] += amt
            u_bank["last_salary"] = time.time()
            save_data(db)
            await safe_reply(update.message, t(f"تم ايداع راتبك: {amt} ريال"))
            return

        if text == "بخشيش":
            amt = random.randint(1000, 5000) * mult
            u_bank["balance"] += amt
            save_data(db)
            await safe_reply(update.message, t(f"حصلت على بخشيش: {amt} ريال"))
            return

        if text == "حظ":
            amt = random.randint(-10000, 20000)
            if amt > 0:
                win = amt * mult
                u_bank["balance"] += win
                await safe_reply(update.message, t(f"حظك حلو، كسبت {win} ريال"))
            else:
                u_bank["balance"] -= abs(amt)
                await safe_reply(update.message, t(f"حظك سيء، خسرت {abs(amt)} ريال"))
            save_data(db)
            return

        if text.startswith("مضاربه ") or text.startswith("استثمار "):
            try:
                amt = int(text.split()[1])
                if amt <= 0 or amt > u_bank["balance"]:
                    await safe_reply(update.message, t("المبلغ غير صحيح او رصيدك ما يكفي"))
                    return
                if random.choice([True, False]):
                    win = amt * mult
                    u_bank["balance"] += win
                    await safe_reply(update.message, t(f"ربحت في العملية وتم اضافة {win} ريال لرصيدك"))
                else:
                    u_bank["balance"] -= amt
                    await safe_reply(update.message, t(f"خسرت العملية وطار منك {amt} ريال"))
                save_data(db)
            except Exception:
                await safe_reply(update.message, t("اكتب المبلغ بعد الكلمة، مثال: مضاربه 1000"))
            return

        if text == "زرف":
            if not update.message.reply_to_message:
                await safe_reply(update.message, t("لازم ترد على الشخص اللي تبي تزرفه"))
                return
            target_id = str(update.message.reply_to_message.from_user.id)
            if target_id not in db["bank"]:
                await safe_reply(update.message, t("الضحية ما عنده حساب بنكي"))
                return
            if check_jail(target_id):
                await safe_reply(update.message, t("الشخص مسجون ما تقدر تزرفه"))
                return
            if random.choice([True, False, False]):
                steal_amt = int(db["bank"][target_id]["balance"] * random.uniform(0.01, 0.10)) * mult
                if steal_amt > 0:
                    db["bank"][target_id]["balance"] -= steal_amt
                    u_bank["balance"] += steal_amt
                    await safe_reply(update.message, t(f"تم زرف {steal_amt} ريال بنجاح"))
                else:
                    await safe_reply(update.message, t("الضحية مطفر ماعنده شي"))
            else:
                fine = int(u_bank["balance"] * 0.05)
                u_bank["balance"] -= fine
                await safe_reply(update.message, t(f"الشرطة مسكتك وتم تغريمك {fine} ريال"))
            save_data(db)
            return

        if text == "العجله":
            if u_bank["balance"] < WHEEL_COST:
                await safe_reply(update.message, t("رصيدك ما يكفي، العجلة ب 5 مليون ريال"))
                return
            u_bank["balance"] -= WHEEL_COST
            prize = random.choice(["سيارة", "ماسة", "x2", "خسارة"])
            if prize in ["سيارة", "ماسة"]:
                u_bank["inventory"][prize] = u_bank["inventory"].get(prize, 0) + 1
                await safe_reply(update.message, t(f"مبروك، ربحت {prize} من العجلة"))
            elif prize == "x2":
                u_bank["x2_expiry"] = time.time() + 180
                await safe_reply(update.message, t("مبروك، ربحت x2 تدبيل لكل شيء لمدة 3 دقائق"))
            else:
                await safe_reply(update.message, t("حظ اوفر، ما ربحت شيء هذي المرة"))
            save_data(db)
            return

        if text == "ممتلكاتي":
            inv = u_bank.get("inventory", {})
            if not inv:
                await safe_reply(update.message, t("ما عندك اي ممتلكات حاليا"))
            else:
                msg = "ممتلكاتك:\n"
                for item, count in inv.items():
                    if count > 0:
                        msg += f"- {count} {item}\n"
                msg += f"\nالرصيد: {u_bank['balance']} ريال\nالأسهم: {u_bank['stocks']}"
                await safe_reply(update.message, t(msg))
            return

        if text.startswith("شراء ") and not text.startswith("شراء اسهم "):
            parts = text.split()
            if len(parts) >= 3:
                try:
                    qty = int(parts[1])
                    item = " ".join(parts[2:])
                    if item in ITEMS_PRICES:
                        cost = ITEMS_PRICES[item] * qty
                        if u_bank["balance"] >= cost:
                            u_bank["balance"] -= cost
                            u_bank["inventory"][item] = u_bank["inventory"].get(item, 0) + qty
                            save_data(db)
                            await safe_reply(update.message, t(f"تم شراء {qty} {item} بنجاح"))
                        else:
                            await safe_reply(update.message, t(f"رصيدك ما يكفي، سعر الـ {item} هو {ITEMS_PRICES[item]}"))
                    else:
                        await safe_reply(update.message, t("هذا الشيء غير متوفر للبيع"))
                except Exception:
                    await safe_reply(update.message, t("اكتب الامر صح، مثال: شراء 2 سيارة"))
            return

        if text.startswith("بيع ") and not text.startswith("بيع اسهم "):
            parts = text.split()
            if len(parts) >= 3:
                try:
                    qty = int(parts[1])
                    item = " ".join(parts[2:])
                    if u_bank["inventory"].get(item, 0) >= qty:
                        gain = int(ITEMS_PRICES[item] * 0.8) * qty
                        u_bank["inventory"][item] -= qty
                        u_bank["balance"] += gain
                        save_data(db)
                        await safe_reply(update.message, t(f"تم بيع {qty} {item} بمبلغ {gain} ريال"))
                    else:
                        await safe_reply(update.message, t("ما عندك هذا العدد من الممتلكات"))
                except Exception:
                    await safe_reply(update.message, t("اكتب الامر صح، مثال: بيع 2 سيارة"))
            return

        if text.startswith("اهداء "):
            if not update.message.reply_to_message:
                await safe_reply(update.message, t("لازم ترد على الشخص اللي تبي تهديه"))
                return
            target_id = str(update.message.reply_to_message.from_user.id)
            if target_id not in db["bank"]:
                await safe_reply(update.message, t("المستلم ما عنده حساب بنكي"))
                return
            parts = text.split()
            if len(parts) >= 3:
                try:
                    qty = int(parts[1])
                    item = " ".join(parts[2:])
                    if u_bank["inventory"].get(item, 0) >= qty:
                        u_bank["inventory"][item] -= qty
                        db["bank"][target_id]["inventory"][item] = db["bank"][target_id]["inventory"].get(item, 0) + qty
                        save_data(db)
                        await safe_reply(update.message, t(f"تم اهداء {qty} {item} بنجاح"))
                    else:
                        await safe_reply(update.message, t("ما عندك هذا العدد لتهديه"))
                except Exception:
                    await safe_reply(update.message, t("اكتب الامر صح، مثال: اهداء 2 سيارة بالرد"))
            return

        if text == "سعر الاسهم":
            if time.time() - db["market"]["last_update"] > 300:
                db["market"]["price"] = random.randint(50, 1000)
                db["market"]["last_update"] = time.time()
                save_data(db)
            await safe_reply(update.message, t(f"سعر السهم الحالي هو: {db['market']['price']} ريال"))
            return

        if text.startswith("شراء اسهم "):
            try:
                qty = int(text.split()[2])
                price = db["market"]["price"]
                cost = price * qty
                if cost > 0 and u_bank["balance"] >= cost:
                    u_bank["balance"] -= cost
                    u_bank["stocks"] += qty
                    save_data(db)
                    await safe_reply(update.message, t(f"تم شراء {qty} سهم بقيمة {cost} ريال"))
                else:
                    await safe_reply(update.message, t("رصيدك ما يكفي لشراء هذي الاسهم"))
            except Exception:
                pass
            return

        if text.startswith("بيع اسهم "):
            try:
                qty = int(text.split()[2])
                price = db["market"]["price"]
                gain = price * qty
                if qty > 0 and u_bank["stocks"] >= qty:
                    u_bank["stocks"] -= qty
                    u_bank["balance"] += gain
                    save_data(db)
                    await safe_reply(update.message, t(f"تم بيع {qty} سهم بقيمة {gain} ريال"))
                else:
                    await safe_reply(update.message, t("ما عندك هذا العدد من الاسهم"))
            except Exception:
                pass
            return

        if text == "قرض":
            if u_bank["loan"] > 0:
                await safe_reply(update.message, t("عندك قرض حالي لازم تسدده اول"))
                return
            loan_amt = random.randint(100000, 2000000)
            u_bank["loan"] = loan_amt
            u_bank["loan_due"] = time.time() + 86400
            u_bank["balance"] += loan_amt
            save_data(db)
            await safe_reply(update.message, t(f"تم ايداع قرض بقيمة {loan_amt} ريال في حسابك، معك 24 ساعة للسداد او بتنسجن"))
            return

        if text == "ديوني":
            if u_bank["loan"] > 0:
                await safe_reply(update.message, t(f"عليك ديون بقيمة: {u_bank['loan']} ريال"))
            else:
                await safe_reply(update.message, t("ما عليك اي ديون الحمدلله"))
            return

        if text == "سداد ديوني":
            if u_bank["loan"] > 0:
                if u_bank["balance"] >= u_bank["loan"]:
                    u_bank["balance"] -= u_bank["loan"]
                    u_bank["loan"] = 0
                    u_bank["loan_due"] = 0
                    u_bank["is_jailed"] = False
                    save_data(db)
                    await safe_reply(update.message, t("تم سداد ديونك بالكامل وفك سجنك اذا كنت مسجون"))
                else:
                    await safe_reply(update.message, t("رصيدك ما يكفي لسداد ديونك"))
            else:
                await safe_reply(update.message, t("ما عليك ديون عشان تسددها"))
            return

        if text == "سجني":
            if u_bank["is_jailed"]:
                await safe_reply(update.message, t("انت مسجون حاليا بسبب الديون، سدد ديونك عشان تطلع"))
            else:
                await safe_reply(update.message, t("انت حر طليق ولست مسجون"))
            return

        if text == "ديونه" and update.message.reply_to_message:
            target_id = str(update.message.reply_to_message.from_user.id)
            if target_id in db["bank"] and db["bank"][target_id]["loan"] > 0:
                await safe_reply(update.message, t(f"هذا الشخص عليه ديون بقيمة: {db['bank'][target_id]['loan']} ريال"))
            else:
                await safe_reply(update.message, t("هذا الشخص ما عليه اي ديون"))
            return

        if text == "سداد ديونه" and update.message.reply_to_message:
            target_id = str(update.message.reply_to_message.from_user.id)
            if target_id in db["bank"] and db["bank"][target_id]["loan"] > 0:
                target_loan = db["bank"][target_id]["loan"]
                if u_bank["balance"] >= target_loan:
                    u_bank["balance"] -= target_loan
                    db["bank"][target_id]["loan"] = 0
                    db["bank"][target_id]["loan_due"] = 0
                    db["bank"][target_id]["is_jailed"] = False
                    save_data(db)
                    await safe_reply(update.message, t("كفو، تم سداد ديون الشخص وفك سجنه من حسابك"))
                else:
                    await safe_reply(update.message, t("رصيدك ما يكفي عشان تسدد عنه"))
            return

    # ------------------ التوبات ------------------
    if text == "توب القروبات":
        if not db["group_games"]:
            await safe_reply(update.message, t("مافي قروبات لعبت للحين"))
            return
        sorted_groups = sorted(db["group_games"].items(), key=lambda x: x[1], reverse=True)[:20]
        msg = "توب 20 قروب في الالعاب:\n\n"
        for i, (gid, count) in enumerate(sorted_groups, 1):
            gname = db["group_names"].get(gid, "مجموعة غير معروفة")
            msg += f"{i} - {gname} : {count} لعبة\n"
        await safe_reply(update.message, t(msg))
        return

    if text in ["توب المتفاعلين", "المتفاعلين"]:
        if update.message.chat.type not in ['group', 'supergroup']:
            await safe_reply(update.message, t("هذا الامر يشتغل في المجموعات بس"))
            return
        group_msgs = db["group_msgs"].get(chat_id, {})
        if not group_msgs:
            await safe_reply(update.message, t("مافي تفاعل مسجل بهالقروب للحين"))
            return
        sorted_users = sorted(group_msgs.items(), key=lambda x: x[1], reverse=True)[:20]
        msg = "توب أكثر 20 متفاعل في القروب\n\n"
        for i, (uid, count) in enumerate(sorted_users, 1):
            uname = db["user_names"].get(uid, "عضو")
            msg += f"{i}) {count} | {uname}\n"

        btn_text = db["settings"].get("top_btn", {}).get("text", "اخفاء التوب")
        btn_emoji = db["settings"].get("top_btn", {}).get("emoji", "")
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(f"{btn_text} {btn_emoji}".strip(), callback_data="hide_top")]])
        await safe_reply(update.message, t(msg), reply_markup=reply_markup)
        return

    # ------------------ الأوامر اللي تعتمد على الرد (الهمسة، الرفع.. الخ) ------------------
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        target_id = str(target_user.id)
        target_role = get_user_role(chat_id, int(target_id))
        target_weight = ROLES[target_role]

        if text == "مسح":
            if issuer_weight < ROLES["ادمن"]:
                await safe_reply(update.message, t("هذا الأمر للمشرفين وأعلى"))
                return
            try:
                await update.message.reply_to_message.delete()
                await update.message.delete()
            except Exception:
                await safe_reply(update.message, t("البوت ماله صلاحية مسح الرسايل"))
            return

        if text in ["اهمس", "ه"]:
            if target_user.is_bot:
                await safe_reply(update.message, t("يا غبي مايمديك تهمس للبوت"))
                return
            if target_id == user_id:
                await safe_reply(update.message, t("يا حمار ماتقدر تهمس لنفسك"))
                return

            w_id = str(random.randint(100000, 999999))
            bot_info = await context.bot.get_me()
            db["whispers"][w_id] = {
                "from_id": user_id, "from_name": user.first_name,
                "to_id": target_id, "to_name": target_user.first_name,
                "chat_id": chat_id, "text": ""
            }
            save_data(db)

            btn_url = f"https://t.me/{bot_info.username}?start=w_{w_id}"
            keyboard = [[InlineKeyboardButton(t("اهمس هنا"), url=btn_url)]]
            await safe_reply(update.message,
                t(f"تم تحديد الهمسه لـ {target_user.first_name}\nاضغط الزر لكتابة الهمسة"),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        if text.startswith("رفع "):
            if issuer_weight < ROLES["مالك"]:
                await safe_reply(update.message, t("ما تقدر ترفع رتب، صلاحياتك ما تسمح"))
                return
            new_role = text.replace("رفع ", "").strip()
            if new_role in ROLES and ROLES[new_role] < issuer_weight:
                if chat_id not in db["roles"]:
                    db["roles"][chat_id] = {}
                db["roles"][chat_id][target_id] = new_role
                save_data(db)
                await safe_reply(update.message, t(f"ابشر، تم رفع {target_user.first_name} الى رتبة {new_role}"))
            else:
                await safe_reply(update.message, t("الرتبة مو موجودة او تحاول ترفع شخص اعلى من رتبتك"))
            return

        if text in ["حظر", "طرد", "تقييد", "كتم"]:
            if issuer_weight < ROLES["ادمن"]:
                return
            if target_weight >= issuer_weight:
                await safe_reply(update.message, t("ما تقدر تسوي شي لشخص رتبته اعلى او تساوي رتبتك"))
                return
            try:
                if text == "حظر":
                    await context.bot.ban_chat_member(chat_id, target_id)
                    await safe_reply(update.message, t(f"تم حظره من المجموعه\nالمستخدم {target_user.first_name}"))
            except Exception:
                await safe_reply(update.message, t("صار خطأ، تأكد ان البوت مشرف وصلاحياته كاملة"))
            return

    # ------------------ الأوامر العامة والأخيرة ------------------
    if text == "نادي المطور":
        dev_msg = (
            f"نداء للمطور من مجموعة: {update.message.chat.title}\n"
            f"المرسل: {user.first_name} | الايدي: {user.id}\n"
            f"اليوزر: @{user.username if user.username else 'بدون يوزر'}\n"
        )
        await context.bot.send_message(chat_id=DEVELOPER_ID, text=t(dev_msg))
        await safe_reply(update.message, t("تم ارسال طلبك للمطور سيتم الرد عليك قريبا."))
        return

    if text.lower() in ["ايدي", "ا", "id"]:
        user_photos = await context.bot.get_user_profile_photos(user.id, limit=1)
        id_template = db.get("chat_templates", {}).get(chat_id, {}).get("id", f"iD: #الايدي\nName: #الاسم\nUser Name: #يوزره\nRank: #الرتبة\nMsg: #الرسائل")
        caption = format_reply_text(id_template, user, chat_id)

        if user_photos.total_count > 0:
            await safe_reply_photo(update.message, user_photos.photos[0][-1].file_id, t(caption))
        else:
            await safe_reply(update.message, t(caption))
        return

    if text.startswith("ماريا "):
        prompt = text.replace("ماريا ", "").strip()
        status_msg = await safe_reply(update.message, t("يتم التفكير"))
        try:
            ai_reply = await asyncio.to_thread(get_fast_ai_response, prompt)
            await safe_reply(status_msg, t(ai_reply))
        except Exception:
            await safe_reply(status_msg, t("صار خطأ بسيط جرب ثانية"))
        return

# ================= خادم الويب للحفاظ على البوت =================
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write("بوت الحماية شغال 100%".encode('utf-8'))
    def log_message(self, format, *args):
        pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(ChatMemberHandler(track_bot_joins, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_text))
    print("البوت شغال باقصى سرعة وجاهز بكل التحديثات القوية مع دعم رموز البريميوم المتحركة!")
    app.run_polling()
