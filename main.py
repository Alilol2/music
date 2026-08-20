import os
import json
import asyncio
import random
import time
from datetime import datetime, timedelta
import nest_asyncio
from g4f.client import Client
from telegram import Update, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ChatMemberHandler, CallbackQueryHandler

# تفعيل التوافق مع بيئة جوجل كولاب
nest_asyncio.apply()

# ================= الإعدادات الأساسية =================
TOKEN = "5845566822:AAGJGPGclHybO3r-0mL1I9kGDxduR7R6nr8"
DEVELOPER_ID = 5543325412 
BOT_NAME = "ماريا"
DEV_NAME = "محمد الهاشمي"
DEV_BIO = "#515 ~ @e515bot"
# =======================================================

DATA_FILE = 'data.json'

adding_reply_state = {}
changing_word_state = {} 
creating_button_state = {} 
adding_alias_state = {} 

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
            for k in ["custom_replies", "msg_count", "bank", "group_games", "group_msgs", "group_names", "user_names", "link_disabled", "settings", "word_replacements", "whispers", "command_aliases", "chat_settings", "marriages"]:
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
        "roles": {}, "muted": {}, "custom_replies": {}, "msg_count": {},
        "stats": {"users": [], "groups": []}, "bank": {}, "market": {"price": 100, "last_update": 0},
        "group_games": {}, "group_msgs": {}, "group_names": {}, "user_names": {},
        "link_disabled": {}, "game_words": ["مدرسة", "تليجرام", "سيارة", "كمبيوتر", "السعودية", "برمجة"],
        "settings": {"top_btn": {"text": "اخفاء التوب", "emoji": ""}}, "word_replacements": {},
        "whispers": {}, "command_aliases": {}, "chat_settings": {}, "marriages": {}
    }

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = load_data()

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
                await update.message.reply_text(t("اكتب همستك الحين:"))
                return
    await update.message.reply_text(t("هلا ومرحبا"))

# --- تحديث وإصلاح الذكاء الاصطناعي واسم ماريا ---
def get_fast_ai_response(prompt):
    try:
        c = Client()
        response = c.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "اسمك ماريا، وأنتي مساعدة ذكية تسولفين باللهجة السعودية البحتة والعامية وبأسلوب عفوي وسريع جداً كأنك بنت سعودية. ممنوع استخدام أي إيموجات أو رموز تعبيرية أو نجوم أو هاشتاقات أو علامات تنسيق نهائياً."},
                {"role": "user", "content": prompt}
            ]
        )
        raw_text = response.choices[0].message.content
        return raw_text.replace("*", "").replace("#", "").replace("`", "").replace("_", "").replace("-", "").strip()
    except Exception: 
        return "السيرفرات عليها ضغط شوي الحين، جرب تسألني بعد ثواني."

def format_reply_text(text, user, chat_title="المجموعة"):
    name = user.first_name or "المستخدم"
    username = f"@{user.username}" if user.username else "بدون يوزر"
    return text.replace("#الاسم", name).replace("#يوزره", username).replace("#اليوزر", username).replace("#الايدي", str(user.id)).replace("#الرتبة", "عضو")

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
            
            await query.message.edit_text(t(msg), reply_markup=generate_xo_board(game_id))
            del xo_games[game_id]
            return
            
        game["turn"] = game["p2"] if user_id == game["p1"] else game["p1"]
        next_turn_name = game["p2_name"] if user_id == game["p1"] else game["p1_name"]
        
        await query.message.edit_text(t(f"لعبة اكس او مستمرة\nالدور الان على: {next_turn_name}"), reply_markup=generate_xo_board(game_id))
        return

    # --- قوائم الأوامر ---
    if data == "cmd_main":
        await query.answer()
        await query.message.edit_text(t("اهلا بك في قائمة اوامر ماريا\nاختر القسم اللي تبيه من الازرار تحت:"), reply_markup=generate_menu_keyboard())
        return
    
    if data == "cmd_games":
        await query.answer()
        msg = "اوامر الالعاب:\n\n- سرعة / لعبة سرعة\n- اكس او [بالرد]\n- لعبة كلمات\n- لعبة رياضيات\n- لعبة عواصم\n- لعبة تفكيك\n- لعبة تركيب\n- كت تويت / كت\n- صراحة / صراحه\n- لو خيروك\n- عقاب\n- زواج [بالرد] / طلاق\n- زوجي / زوجتي\n- توب القروبات\n- توب المتفاعلين"
        await query.message.edit_text(t(msg), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="cmd_main")]]))
        return

    if data == "cmd_bank":
        await query.answer()
        msg = "اوامر البنك والاقتصاد:\n\n- انشاء حساب بنكي\n- فلوسي\n- راتب\n- بخشيش\n- زرف [بالرد]\n- استثمار / مضاربه [المبلغ]\n- حظ\n- العجله\n- ممتلكاتي\n- شراء / بيع / اهداء [العدد] [الشيء]\n- سعر الاسهم / شراء اسهم / بيع اسهم\n- قرض / ديوني / سداد ديوني\n- ديونه / سداد ديونه [بالرد]\n- سجني"
        await query.message.edit_text(t(msg), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="cmd_main")]]))
        return

    if data == "cmd_protect":
        await query.answer()
        msg = "اوامر الحماية (للمشرفين فقط):\n(تطبق على الأعضاء اللي رتبتهم اقل من مميز)\n\n- قفل الروابط / فتح الروابط\n- قفل الصور / فتح الصور\n- قفل الملصقات / فتح الملصقات\n- قفل التوجيه / فتح التوجيه"
        await query.message.edit_text(t(msg), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="cmd_main")]]))
        return

    if data == "cmd_admin":
        await query.answer()
        msg = "اوامر الادارة والمشرفين:\n\n- حظر / طرد / كتم / تقييد [بالرد]\n- الغاء حظر / الغاء كتم / الغاء تقييد [بالرد]\n- مسح [بالرد]\n- تثبيت / الغاء التثبيت [بالرد]\n- رفع / تنزيل [بالرد]\n- ضع اسم / ضع وصف\n- تفعيل الرابط / تعطيل الرابط\n- اضف كلمة"
        await query.message.edit_text(t(msg), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="cmd_main")]]))
        return

    if data == "cmd_general":
        await query.answer()
        msg = "الاوامر العامة:\n\n- ايدي / ا / id\n- معلوماتي\n- القروب\n- الوقت / التاريخ\n- احسب [مسألة]\n- زخرفة [نص]\n- قول [نص]\n- رتبتي\n- رتبته [بالرد]\n- الرابط\n- الردود العامه\n- تيست [سؤالك]\n- اهمس / ه [بالرد]\n- المطور / نادي المطور\n- الاوامر / م"
        await query.message.edit_text(t(msg), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="cmd_main")]]))
        return

    if data == "cmd_dev":
        if user_id != str(DEVELOPER_ID):
            await query.answer(t("معليش، هذا القسم خاص بالمطور فقط! يمنع الدخول."), show_alert=True)
            return
        await query.answer()
        msg = "اوامر المطور (Dev):\n\n- اضف امر (لصنع اختصار لأي امر)\n- صنع زر (لارسال رسالة بزر شفاف ورابط)\n- تغير كلمه (لاستبدال الكلمات بالنظام الذكي)\n- تعديل زر (زر اخفاء التوب)\n- اضف رد عام / حذف رد"
        await query.message.edit_text(t(msg), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="cmd_main")]]))
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

    # --- نظام الحماية المتطور (رتبة مميز وأعلى مستثنيين تماماً) ---
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
                warning_msg = await update.message.reply_text(t(f"عذرا عزيزي {user.first_name}، يمنع ارسال {reason} في هذه المجموعة."))
                asyncio.create_task(delete_after(warning_msg, 5))
            except Exception:
                pass
            return

    text = update.message.text or update.message.caption
    if not text:
        return
    text = text.strip()

    # --- تعريف المتغيرات المهمة هنا ---
    text_normalized = text.replace("إلغاء", "الغاء").replace("فك ", "الغاء ")

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
                    await update.message.reply_text(t("تم ارسال الهمسة للقروب بنجاح!"))
                except Exception:
                    await update.message.reply_text(t("فشلت عملية ارسال الهمسة، يمكن البوت انطرد من القروب."))
                
                del pending_whispers[user_id_int]
                return
    
    # تحديث إحصائيات المستخدمين والقروبات
    db["user_names"][user_id] = user.first_name
    if update.message.chat.type in ['group', 'supergroup']:
        db["group_names"][chat_id] = update.message.chat.title
        if chat_id not in db["group_msgs"]:
            db["group_msgs"][chat_id] = {}
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
        msg = "اهلا بك في قائمة اوامر ماريا\nاختر القسم اللي تبيه من الازرار تحت:"
        await update.message.reply_text(t(msg), reply_markup=generate_menu_keyboard())
        return

    # ------------------ نظام اختصار الأوامر ------------------
    if user_id_int in adding_alias_state:
        state = adding_alias_state[user_id_int]
        step = state.get("step")

        if step == "waiting_for_old_cmd":
            state["old_cmd"] = text
            state["step"] = "waiting_for_new_cmd"
            await update.message.reply_text(t("ممتاز، الحين ارسل الاختصار أو الأمر الجديد اللي تبيه (مثلاً: ظ):"))
            return
            
        elif step == "waiting_for_new_cmd":
            old_cmd = state["old_cmd"]
            db["command_aliases"][text] = old_cmd
            save_data(db)
            del adding_alias_state[user_id_int]
            await update.message.reply_text(t(f"تم بنجاح! الحين تقدر تستخدم '{text}' بدال '{old_cmd}'."))
            return

    if text == "اضف امر":
        if issuer_weight < ROLES["مالك"]:
            await update.message.reply_text(t("معليش هذا الامر للمالك والـ Dev فقط"))
            return
        adding_alias_state[user_id_int] = {"step": "waiting_for_old_cmd"}
        await update.message.reply_text(t("ارسل الأمر الأساسي اللي تبي تسوي له اختصار (مثلاً: حظر)"))
        return

    # ------------------ الأوامر والمعلومات العامة الجديدة ------------------
    if text == "الوقت":
        ksa_time = datetime.utcnow() + timedelta(hours=3)
        await update.message.reply_text(t(f"الوقت الان في السعودية: {ksa_time.strftime('%I:%M %p')}"))
        return
        
    if text == "التاريخ":
        ksa_time = datetime.utcnow() + timedelta(hours=3)
        await update.message.reply_text(t(f"التاريخ اليوم: {ksa_time.strftime('%Y-%m-%d')}"))
        return
        
    if text == "معلوماتي":
        msg = f"معلوماتك الشخصية:\nالاسم: {user.first_name}\nاليوزر: @{user.username if user.username else 'لا يوجد'}\nالايدي: {user.id}\nرتبتك بالقروب: {issuer_role}\nرسائلك: {db['msg_count'].get(str(user.id), 1)}\nرصيدك البنكي: {db['bank'].get(str(user.id), {}).get('balance', 0)} ريال"
        await update.message.reply_text(t(msg))
        return
        
    if text == "القروب":
        if update.message.chat.type == "private":
            await update.message.reply_text(t("هذا الامر للمجموعات فقط"))
            return
        msg = f"معلومات المجموعة:\nالاسم: {update.message.chat.title}\nالايدي: {update.message.chat.id}\nعدد الرسائل المسجلة: {sum(db['group_msgs'].get(chat_id, {}).values())}"
        await update.message.reply_text(t(msg))
        return
        
    if text.startswith("احسب "):
        calc = text.replace("احسب ", "").strip()
        try:
            allowed = "0123456789+-*/(). "
            if all(c in allowed for c in calc):
                res = eval(calc)
                await update.message.reply_text(t(f"الناتج: {res}"))
            else:
                await update.message.reply_text(t("ارقام وعمليات حسابية فقط يا ذكي"))
        except Exception:
            await update.message.reply_text(t("مسألة خاطئة، تأكد من الارقام"))
        return
            
    if text.startswith("زخرفة "):
        word = text.replace("زخرفة ", "").strip()
        zakhrafa = " ".join([c + "ـ" for c in word])
        await update.message.reply_text(t(f"الكلمة المزخرفة:\n{zakhrafa}"))
        return
        
    if text.startswith("قول "):
        word = text.replace("قول ", "").strip()
        try:
            await update.message.delete()
        except Exception:
            pass
        await update.message.reply_text(t(word))
        return

    # ------------------ ألعاب التليجرام الجديدة والاجتماعية ------------------
    if text in ["كت تويت", "كت"]:
        await update.message.reply_text(t(random.choice(CUT_TWEET)))
        return
        
    if text in ["صراحة", "صراحه"]:
        await update.message.reply_text(t(random.choice(SARAHA)))
        return
        
    if text in ["لو خيروك"]:
        await update.message.reply_text(t(random.choice(KHYROK)))
        return
        
    if text in ["عقاب"]:
        await update.message.reply_text(t(random.choice(EQAB)))
        return

    # ------------------ نظام الزواج واكس او بالرد ------------------
    if update.message.reply_to_message:
        target_id = str(update.message.reply_to_message.from_user.id)
        
        if text == "زواج":
            if target_id == user_id:
                await update.message.reply_text(t("تبي تتزوج نفسك؟ صاحي انت!"))
                return
            if update.message.reply_to_message.from_user.is_bot:
                await update.message.reply_text(t("البوتات للبرمجة مو للزواج"))
                return
            if user_id in db.get("marriages", {}):
                await update.message.reply_text(t("انت متزوج من قبل، طلق اول!"))
                return
            if target_id in db.get("marriages", {}):
                await update.message.reply_text(t("هذا الشخص متزوج، ابعد عن المشاكل!"))
                return
            
            db["marriages"][user_id] = target_id
            db["marriages"][target_id] = user_id
            save_data(db)
            msg = f"مبروووك! تم زواج {user.first_name} من {update.message.reply_to_message.from_user.first_name} بالرفاه والبنين"
            await update.message.reply_text(t(msg))
            return

        if text in ["اكس او", "لعبة اكس او"]:
            if target_id == user_id:
                await update.message.reply_text(t("تبي تلعب مع نفسك؟"))
                return
            if update.message.reply_to_message.from_user.is_bot:
                await update.message.reply_text(t("ما تقدر تتحدى البوت بالاكس او"))
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
            await update.message.reply_text(t(msg), reply_markup=generate_xo_board(game_id))
            return

    if text == "طلاق":
        if user_id in db.get("marriages", {}):
            partner_id = db["marriages"][user_id]
            del db["marriages"][user_id]
            if partner_id in db["marriages"]:
                del db["marriages"][partner_id]
            save_data(db)
            await update.message.reply_text(t("ابغض الحلال.. تم الطلاق بنجاح وانفصلتوا"))
            return
        await update.message.reply_text(t("انت مو متزوج اصلا عشان تطلق!"))
        return

    if text in ["زوجي", "زوجتي"]:
        if user_id in db.get("marriages", {}):
            partner_id = db["marriages"][user_id]
            partner_name = db["user_names"].get(partner_id, "عضو مجهول")
            await update.message.reply_text(t(f"شريك حياتك هو: {partner_name}"))
            return
        await update.message.reply_text(t("انت سنجل بائس مو متزوج"))
        return

    # ------------------ نظام الألعاب المصغرة مع التوقيت والمراكز ------------------
    if chat_id in active_math_game and text == active_math_game[chat_id]["answer"]:
        game_data = active_math_game.pop(chat_id)
        elapsed = time.time() - game_data["start"]
        prize = win_game(user_id, 3000)
        msg = f"كفو يا {user.first_name} جوابك صح!\nاستغرقت {elapsed:.2f} ثانية"
        if prize:
            msg += f"\nربحت {prize} ريال بالبنك"
        await update.message.reply_text(t(msg))
        return

    if chat_id in active_capitals_game and text == active_capitals_game[chat_id]["answer"]:
        game_data = active_capitals_game.pop(chat_id)
        elapsed = time.time() - game_data["start"]
        prize = win_game(user_id, 4000)
        msg = f"وحش يا {user.first_name} الجواب هو {text}!\nاستغرقت {elapsed:.2f} ثانية"
        if prize:
            msg += f"\nربحت {prize} ريال بالبنك"
        await update.message.reply_text(t(msg))
        return

    if chat_id in active_tafkik_game and text == active_tafkik_game[chat_id]["answer"]:
        game_data = active_tafkik_game.pop(chat_id)
        elapsed = time.time() - game_data["start"]
        prize = win_game(user_id, 3000)
        msg = f"بطل يا {user.first_name} فككت الكلمة صح!\nاستغرقت {elapsed:.2f} ثانية"
        if prize:
            msg += f"\nربحت {prize} ريال بالبنك"
        await update.message.reply_text(t(msg))
        return

    if chat_id in active_tarkib_game and text == active_tarkib_game[chat_id]["answer"]:
        game_data = active_tarkib_game.pop(chat_id)
        elapsed = time.time() - game_data["start"]
        prize = win_game(user_id, 3000)
        msg = f"ذيبان يا {user.first_name} ركبت الكلمة صح!\nاستغرقت {elapsed:.2f} ثانية"
        if prize:
            msg += f"\nربحت {prize} ريال بالبنك"
        await update.message.reply_text(t(msg))
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
                await update.message.reply_text(t(msg))
                return
            else:
                await update.message.reply_text(t(f"المركز {len(game['winners'])} لـ {user.first_name} في {elapsed:.2f} ثانية! باقي {3 - len(game['winners'])} مراكز"))
                return

    if text in ["رياضيات", "لعبة رياضيات"]:
        a = random.randint(1, 100)
        b = random.randint(1, 100)
        op = random.choice(["+", "-", "*"])
        active_math_game[chat_id] = {"answer": str(eval(f"{a}{op}{b}")), "start": time.time()}
        await update.message.reply_text(t(f"أول شخص يحل هالمسألة يفوز:\n{a} {op} {b} = ؟"))
        return

    if text in ["عواصم", "لعبة عواصم"]:
        country, capital = random.choice(list(CAPITALS.items()))
        active_capitals_game[chat_id] = {"answer": capital, "start": time.time()}
        await update.message.reply_text(t(f"أول شخص يكتب عاصمة ( {country} ) يفوز:"))
        return

    if text in ["تفكيك", "لعبة تفكيك"]:
        word = random.choice(db["game_words"])
        active_tafkik_game[chat_id] = {"answer": " ".join(list(word)), "start": time.time()}
        await update.message.reply_text(t(f"أول شخص يفكك هالكلمة يفوز:\n{word}"))
        return

    if text in ["تركيب", "لعبة تركيب"]:
        word = random.choice(db["game_words"])
        active_tarkib_game[chat_id] = {"answer": word, "start": time.time()}
        await update.message.reply_text(t(f"أول شخص يركب هالحروف يفوز:\n{' '.join(list(word))}"))
        return

    if text in ["سرعة", "سرعه", "لعبة سرعة", "لعبة سرعه"]:
        word = random.choice(db["game_words"])
        active_speed_game[chat_id] = {"word": word, "start": time.time(), "winners": []}
        await update.message.reply_text(t(f"اسرع 3 يكتبون هالكلمة يفوزون:\n\n{word}"))
        return

    # ------------------ نظام الأقفال والإدارة المتطورة ------------------
    if text.startswith("قفل ") or text.startswith("فتح "):
        if issuer_weight < ROLES["ادمن"]:
            await update.message.reply_text(t("هذا الأمر للمشرفين وأعلى"))
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
        await update.message.reply_text(t(f"تم {action} {target} بنجاح"))
        return

    if text.startswith("ضع اسم "):
        if issuer_weight < ROLES["ادمن"]:
            return
        new_name = text.replace("ضع اسم ", "").strip()
        try:
            await context.bot.set_chat_title(chat_id, new_name)
            await update.message.reply_text(t("تم تغيير اسم المجموعة بنجاح"))
        except Exception:
            await update.message.reply_text(t("البوت ماله صلاحية يغير الاسم"))
        return

    if text.startswith("ضع وصف "):
        if issuer_weight < ROLES["ادمن"]:
            return
        new_desc = text.replace("ضع وصف ", "").strip()
        try:
            await context.bot.set_chat_description(chat_id, new_desc)
            await update.message.reply_text(t("تم تغيير وصف المجموعة بنجاح"))
        except Exception:
            await update.message.reply_text(t("البوت ماله صلاحية يغير الوصف"))
        return

    # ------------------ نظام مسح المطور (الجديد والمحسن) ------------------
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        target_id = str(target_user.id)
        target_role = get_user_role(chat_id, int(target_id))
        target_weight = ROLES[target_role]

        if text == "مسح":
            if issuer_weight < ROLES["ادمن"]:
                await update.message.reply_text(t("هذا الأمر للمشرفين وأعلى"))
                return
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=update.message.reply_to_message.message_id)
                await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
            except Exception:
                await update.message.reply_text(t("ما قدرت امسح! تأكد إني (مشرف) وعندي صلاحية (حذف رسائل المستخدمين)."))
            return
            
        if text == "تثبيت":
            if issuer_weight < ROLES["ادمن"]:
                return
            try:
                await update.message.reply_to_message.pin()
                await update.message.reply_text(t("تم تثبيت الرسالة"))
            except Exception:
                await update.message.reply_text(t("ما عندي صلاحية تثبيت"))
            return
            
        if text == "الغاء التثبيت" or text == "الغاء تثبيت":
            if issuer_weight < ROLES["ادمن"]:
                return
            try:
                await update.message.reply_to_message.unpin()
                await update.message.reply_text(t("تم الغاء تثبيت الرسالة"))
            except Exception:
                await update.message.reply_text(t("ما عندي صلاحية"))
            return

    # ------------------ نظام صنع الأزرار الحرة بالروابط ------------------
    if user_id_int in creating_button_state:
        state = creating_button_state[user_id_int]
        step = state.get("step")

        if step == "waiting_for_msg_text":
            state["msg_text"] = text
            state["step"] = "waiting_for_btn_text"
            await update.message.reply_text(t("ممتاز، الحين ارسل النص اللي تبيه يطلع داخل الزر (تقدر تحط ايموجي كيبورد عادي معه):"))
            return

        elif step == "waiting_for_btn_text":
            state["btn_text"] = text
            state["step"] = "waiting_for_btn_url"
            await update.message.reply_text(t("بطل، اخر خطوة: ارسل الرابط اللي يوديه الزر (لازم يبدأ بـ http أو https):"))
            return

        elif step == "waiting_for_btn_url":
            if not text.startswith("http"):
                await update.message.reply_text(t("الرابط لازم يبدأ بـ http أو https، حاول مره ثانية:"))
                return
            
            msg_text = state["msg_text"]
            btn_text = state["btn_text"]
            btn_url = text
            
            keyboard = [[InlineKeyboardButton(btn_text, url=btn_url)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            del creating_button_state[user_id_int]
            await update.message.reply_text(msg_text, reply_markup=reply_markup)
            await update.message.reply_text(t("تم انشاء الزر وارسال الرسالة بنجاح!"))
            return

    if text == "صنع زر":
        if issuer_weight < ROLES["ادمن"]:
            await update.message.reply_text(t("معليش هذا الامر للادارة فقط"))
            return
        creating_button_state[user_id_int] = {"step": "waiting_for_msg_text"}
        await update.message.reply_text(t("حلو، وش تبي يكون النص الأساسي للرسالة؟ (الكلام اللي فوق الزر)"))
        return

    # ------------------ نظام تغيير الكلمات (الذكي) ------------------
    if user_id_int in changing_word_state:
        state = changing_word_state[user_id_int]
        step = state.get("step")

        if step == "waiting_for_old_word":
            state["old_word"] = text
            state["step"] = "waiting_for_new_word"
            await update.message.reply_text(t("ممتاز، الحين اكتب الكلمة أو الجملة الجديدة اللي تبيها تطلع بدالها:"))
            return
            
        elif step == "waiting_for_new_word":
            old_word = state["old_word"]
            db["word_replacements"][old_word] = text
            save_data(db)
            del changing_word_state[user_id_int]
            await update.message.reply_text(t(f"تم التغيير بنجاح! من اليوم أي رسالة فيها '{old_word}' بتتغير إلى '{text}'"))
            return

    if text == "تغير كلمه":
        if issuer_weight < ROLES["مالك"]:
            await update.message.reply_text(t("معليش هذا الامر للمالك والـ Dev فقط"))
            return
        changing_word_state[user_id_int] = {"step": "waiting_for_old_word"}
        await update.message.reply_text(t("اكتب الكلمة الأساسية اللي تبي تغيرها (نفس ما تطلع بالبوت بالضبط):"))
        return

    # ------------------ نظام إضافة الردود وتعديل الزر ------------------
    if user_id_int in adding_reply_state:
        state = adding_reply_state[user_id_int]
        step = state.get("step")

        if step == "waiting_for_btn_text":
            db["settings"]["top_btn"]["text"] = text
            state["step"] = "waiting_for_btn_emoji"
            await update.message.reply_text(t("حلو، الحين ارسل الايموجي اللي تبيه مع الزر (ايموجي عادي مو مميز)"))
            return

        elif step == "waiting_for_btn_emoji":
            db["settings"]["top_btn"]["emoji"] = text
            save_data(db)
            del adding_reply_state[user_id_int]
            await update.message.reply_text(t("تم حفظ الزر بنجاح"))
            return

        elif step == "waiting_for_keyword":
            state["keyword"] = text
            state["step"] = "waiting_for_reply_content"
            help_message = (
                "حسنا يمكنك اضافة\n"
                "( نص,صوره,فيديو,متحركه,بصمه,ملف )\n"
                "ويمكنك اضافة الرد بتلك الطريقة :\n"
                "#الاسم - اسم العضو\n"
                "#يوزره - يوزر الرد\n"
                "#اليوزر - يوزر مرسل الرساله\n"
                "#الرسائل - عدد رسائل المستخدم\n"
                "#الايدي - ايدي المستخدم\n"
                "#الرتبة - رتبة المستخدم\n"
                "#التعديل - عدد تعديلات\n"
                "#النقاط - نقاط المستخدم"
            )
            await update.message.reply_text(t(help_message))
            return

        elif step == "waiting_for_reply_content":
            keyword = state.get("keyword")
            if keyword:
                if keyword not in db["custom_replies"]:
                    db["custom_replies"][keyword] = []
                db["custom_replies"][keyword].append(text)
                save_data(db)
                await update.message.reply_text(t("تم اضافة الرد لكل المجموعات"))
                state["step"] = "waiting_for_more_replies"
            return

        elif step == "waiting_for_more_replies":
            keyword = state.get("keyword")
            if text.lower() in ["تم", "خلاص"]:
                del adding_reply_state[user_id_int]
                await update.message.reply_text(t("تم الانتهاء وحفظ جميع الردود بنجاح"))
                return
            else:
                if keyword:
                    db["custom_replies"][keyword].append(text)
                    save_data(db)
                    await update.message.reply_text(t(f"تم اضافة الرد باقى {len(db['custom_replies'][keyword])}\nتم اضافة الرد ارسل رد اخر او ارسل تم"))
                return

    if text == "تعديل زر":
        if issuer_weight < ROLES["مالك"]:
            await update.message.reply_text(t("معليش هذا الامر للمالك والـ Dev فقط"))
            return
        adding_reply_state[user_id_int] = {"step": "waiting_for_btn_text"}
        await update.message.reply_text(t("وش الكلام اللي تبيه بالزر؟ (مثلاً: اخفاء التوب)"))
        return

    # ------------------ نظام الرابط ------------------
    if text == "تعطيل الرابط":
        if issuer_weight < ROLES["ادمن"]:
            await update.message.reply_text(t("هذا الامر للادمن واعلى"))
            return
        db["link_disabled"][chat_id] = True
        save_data(db)
        await update.message.reply_text(t("تم تعطيل الرابط بنجاح"))
        return

    if text == "تفعيل الرابط":
        if issuer_weight < ROLES["ادمن"]:
            await update.message.reply_text(t("هذا الامر للادمن واعلى"))
            return
        db["link_disabled"][chat_id] = False
        save_data(db)
        await update.message.reply_text(t("تم تفعيل الرابط بنجاح"))
        return

    if text == "الرابط":
        if db["link_disabled"].get(chat_id, False):
            await update.message.reply_text(t("المشرفين عطلوا الرابط"))
            return
        try:
            link = await context.bot.export_chat_invite_link(chat_id)
            await update.message.reply_text(t(f"رابط المجموعة:\n{link}"))
        except Exception:
            await update.message.reply_text(t("البوت مو مشرف او ماعنده صلاحية دعوة المستخدمين"))
        return

    # ------------------ الردود العامة ------------------
    if text == "الردود العامه":
        replies = db.get("custom_replies", {})
        if not replies:
            await update.message.reply_text(t("مافي ردود عامة مضافة حاليا"))
            return
        msg = "قائمة الردود العامة المضافة:\n\n"
        for i, key in enumerate(replies.keys(), 1):
            msg += f"{i} - {key}\n"
        await update.message.reply_text(t(msg))
        return

    # ------------------ أوامر حظر ورفع بالرد ------------------
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        target_id = str(target_user.id)
        target_role = get_user_role(chat_id, int(target_id))
        target_weight = ROLES[target_role]

        if text in ["اهمس", "ه"]:
            if target_user.is_bot:
                await update.message.reply_text(t("عذرا لا يمكنك الهمس للبوتات!"))
                return
            if target_id == user_id:
                await update.message.reply_text(t("عذرا لا يمكنك الهمس لنفسك!"))
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
            await update.message.reply_text(
                t(f"تم تحديد الهمسه لـ {target_user.first_name}\nاضغط الزر لكتابة الهمسة"),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        if text == "رتبته":
            await update.message.reply_text(t(f"رتبته هي {target_role}"))
            return

        if text.startswith("رفع "):
            if issuer_weight < ROLES["مالك"]:
                await update.message.reply_text(t("ما تقدر ترفع رتب، صلاحياتك ما تسمح"))
                return
            new_role = text.replace("رفع ", "").strip()
            if new_role in ROLES and ROLES[new_role] < issuer_weight:
                if chat_id not in db["roles"]:
                    db["roles"][chat_id] = {}
                db["roles"][chat_id][target_id] = new_role
                save_data(db)
                await update.message.reply_text(t(f"ابشر، تم رفع {target_user.first_name} الى رتبة {new_role}"))
            else:
                await update.message.reply_text(t("الرتبة مو موجودة او تحاول ترفع شخص اعلى من رتبتك"))
            return

        if text == "تنزيل":
            if issuer_weight < ROLES["مالك"] or issuer_weight <= target_weight:
                await update.message.reply_text(t("ما تملك صلاحية تنزيل هذا الشخص"))
                return
            if chat_id in db["roles"] and target_id in db["roles"][chat_id]:
                del db["roles"][chat_id][target_id]
                save_data(db)
            await update.message.reply_text(t(f"تم تنزيل {target_user.first_name} وصار عضو عادي"))
            return

        if text in ["حظر", "طرد", "تقييد", "كتم"]:
            if issuer_weight < ROLES["ادمن"]:
                return
            if target_weight >= issuer_weight:
                await update.message.reply_text(t("ما تقدر تسوي شي لشخص رتبته اعلى او تساوي رتبتك"))
                return
            try:
                if text == "حظر":
                    await context.bot.ban_chat_member(chat_id, target_id)
                    await update.message.reply_text(t(f"تم حظره من المجموعه\nالمستخدم {target_user.first_name}"))
                elif text == "طرد":
                    await context.bot.ban_chat_member(chat_id, target_id)
                    await context.bot.unban_chat_member(chat_id, target_id)
                    await update.message.reply_text(t(f"تم طرده من المجموعه\nالمستخدم {target_user.first_name}"))
                elif text == "تقييد":
                    await context.bot.restrict_chat_member(chat_id, target_id, permissions=ChatPermissions(can_send_messages=False))
                    await update.message.reply_text(t(f"تم تقييده من المجموعه\nالمستخدم {target_user.first_name}"))
                elif text == "كتم":
                    if chat_id not in db["muted"]:
                        db["muted"][chat_id] = []
                    if target_id not in db["muted"][chat_id]:
                        db["muted"][chat_id].append(target_id)
                        save_data(db)
                    await update.message.reply_text(t(f"تم كتمه من المجموعه\nالمستخدم {target_user.first_name}"))
            except Exception:
                await update.message.reply_text(t("صار خطأ، تأكد ان البوت مشرف وصلاحياته كاملة"))
            return

        if text_normalized in ["الغاء حظر", "الغاء تقييد", "الغاء كتم"]:
            if issuer_weight < ROLES["ادمن"]:
                return
            try:
                if text_normalized == "الغاء حظر":
                    await context.bot.unban_chat_member(chat_id, target_id, only_if_banned=True)
                    await update.message.reply_text(t(f"تم الغاء حظره من المجموعه\nالمستخدم {target_user.first_name}"))
                elif text_normalized == "الغاء تقييد":
                    await context.bot.restrict_chat_member(
                        chat_id, target_id,
                        permissions=ChatPermissions(
                            can_send_messages=True, can_send_audios=True, can_send_documents=True,
                            can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
                            can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True,
                            can_add_web_page_previews=True
                        )
                    )
                    await update.message.reply_text(t(f"تم الغاء تقييده من المجموعه\nالمستخدم {target_user.first_name}"))
                elif text_normalized == "الغاء كتم":
                    if chat_id in db["muted"] and target_id in db["muted"][chat_id]:
                        db["muted"][chat_id].remove(target_id)
                        save_data(db)
                    await update.message.reply_text(t(f"تم الغاء كتمه من المجموعه\nالمستخدم {target_user.first_name}"))
            except Exception:
                await update.message.reply_text(t("صار خطأ، تأكد ان الشخص موجود وبوت مشرف"))
            return

    # ------------------ الأوامر العامة الأخيرة ------------------
    if text == "نادي المطور":
        dev_msg = (
            f"نداء للمطور من مجموعة: {update.message.chat.title}\n"
            f"المرسل: {user.first_name} | الايدي: {user.id}\n"
            f"اليوزر: @{user.username if user.username else 'بدون يوزر'}\n"
        )
        await context.bot.send_message(chat_id=DEVELOPER_ID, text=t(dev_msg))
        await update.message.reply_text(t("تم ارسال طلبك للمطور سيتم الرد عليك قريبا."))
        return

    if text == "المطور":
        dev_photos = await context.bot.get_user_profile_photos(DEVELOPER_ID, limit=1)
        caption = (
            f"Dev Bot: {BOT_NAME}\n"
            "ــــــــــــــــــــــــــــــــــــــ\n"
            f"Dev: {DEV_NAME}\n"
            f"Bio: {DEV_BIO}"
        )
        if dev_photos.total_count > 0:
            await update.message.reply_photo(photo=dev_photos.photos[0][-1].file_id, caption=t(caption))
        else:
            await update.message.reply_text(t(caption))
        return

    if text.lower() in ["ايدي", "ا", "id"]:
        user_photos = await context.bot.get_user_profile_photos(user.id, limit=1)
        msg_cnt = db["msg_count"].get(str(user.id), 1)
        uname = f"@{user.username}" if user.username else "None"
        
        caption = (
            f"iD: {user.id}\n"
            f"Name: {user.first_name}\n"
            f"User Name: {uname}\n"
            f"Rank: {issuer_role}\n"
            f"Msg: {msg_cnt}"
        )
        
        if user_photos.total_count > 0:
            await update.message.reply_photo(photo=user_photos.photos[0][-1].file_id, caption=t(caption))
        else:
            await update.message.reply_text(t(caption))
        return

    if text.startswith("اضف كلمة "):
        if issuer_weight < ROLES["ادمن"]:
            await update.message.reply_text(t("هذا الامر للادمن واعلى"))
            return
        new_word = text.replace("اضف كلمة ", "").strip()
        if new_word and new_word not in db["game_words"]:
            db["game_words"].append(new_word)
            save_data(db)
            await update.message.reply_text(t(f"تم اضافة الكلمة الى قائمة الالعاب بنجاح"))
        else:
            await update.message.reply_text(t("الكلمة موجودة من قبل"))
        return

    if text in ["لعبة كلمات", "لعبة الكلمات"]:
        if not db["game_words"]:
            await update.message.reply_text(t("مافي كلمات مضافة، ضيفوا كلمات اول بامر: اضف كلمة"))
            return
        word = random.choice(db["game_words"])
        letters = list(word)
        random.shuffle(letters)
        shuffled = "".join(letters)
        if shuffled == word and len(word) > 1:
            random.shuffle(letters)
            shuffled = "".join(letters)
        active_word_game[chat_id] = {"answer": word, "start": time.time()}
        await update.message.reply_text(t(f"اسرع واحد يرتب هالكلمة يفوز:\n\n{shuffled}"))
        return

    if text.startswith("ماريا "):
        prompt = text.replace("ماريا ", "").strip()
        status_msg = await update.message.reply_text(t("جاري..."))
        try:
            ai_reply = get_fast_ai_response(prompt)
            await status_msg.edit_text(t(ai_reply))
        except Exception:
            await status_msg.edit_text(t("صار خطأ بسيط جرب ثانية"))
        return

    if text == "رتبتي":
        await update.message.reply_text(t(f"رتبتك {issuer_role}"))
        return

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_callback))
app.add_handler(ChatMemberHandler(track_bot_joins, ChatMemberHandler.MY_CHAT_MEMBER))
app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_text))
print("البوت شغال باقصى سرعة وجاهز بكل التحديثات القوية")
app.run_polling()
