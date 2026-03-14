import os
from telethon import events, Button
from database import db
# استيراد العناصر الأساسية من الملف الرئيسي
from __main__ import client, check_privilege 

# استدعاء المسار الموحد من قاعدة البيانات مباشرة
PROTECT_DIR = db.base_dir

@client.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode('utf-8')
    gid = str(event.chat_id)
    u_id = event.sender_id
    
    # --- [ تحديث أنس: التحقق الهرمي من ضغطة الزر ] ---
    # نتحقق من رتبة الشخص الذي ضغط الزر الآن
    if not await check_privilege(event, "مدير"):
        await event.answer("⚠️ المقام السامي: هذه الأزرار للمدراء فقط!", alert=True)
        return

    # --- القائمة الرئيسية ---
    if data == "show_main":
        btns = [
            [Button.inline("🛡️ نظام الحماية", "show_locks"), Button.inline("🎖️ سجل الرتب", "show_ranks")],
            [Button.inline("📜 دليل الأوامر", "show_cmds"), Button.inline("⚙️ الضبط العام", "show_settings")],
            [Button.inline("❌ إغلاق اللوحة", "close")]
        ]
        await event.edit("👑 **لوحة تحكم Monopoly الملكية** 👑\n\nمرحباً بك يا مدير، اختر القسم المراد التحكم به:", buttons=btns)

    # --- نظام الأقفال (تم تحسين سرعة التحديث) ---
    elif data == "show_locks":
        def get_s(feat): return "🔒" if db.is_locked(gid, feat) else "🔓"
        btns = [
            [Button.inline(f"{get_s('links')} الروابط", "tg_links"), Button.inline(f"{get_s('usernames')} المعرفات", "tg_usernames")],
            [Button.inline(f"{get_s('photos')} الصور", "tg_photos"), Button.inline(f"{get_s('stickers')} الملصقات", "tg_stickers")],
            [Button.inline(f"{get_s('forward')} التوجيه", "tg_forward"), Button.inline(f"{get_s('videos')} الفيديوهات", "tg_videos")],
            [Button.inline("⬅️ رجوع", "show_main")]
        ]
        await event.edit("🔐 **إعدادات الحماية الفورية:**", buttons=btns)

    # --- منطق التبديل (الإصلاح لمنع التعليق) ---
    elif data.startswith("tg_"):
        feature = data.replace("tg_", "")
        if feature == "welcome":
            curr = db.get_setting(gid, "welcome_status")
            db.set_setting(gid, "welcome_status", "off" if curr == "on" else "on")
            await event.answer("✅ تم تحديث حالة الترحيب")
            # تحديث الواجهة بدون استدعاء الدالة من جديد
            w_status = "✅ مفعل" if db.get_setting(gid, "welcome_status") == "on" else "❌ معطل"
            await event.edit("⚙️ **الإعدادات العامة للبوت:**", buttons=[[Button.inline(f"نظام الترحيب: {w_status}", "tg_welcome")],[Button.inline("⬅️ رجوع", "show_main")]])
        else:
            current_l = db.is_locked(gid, feature)
            db.toggle_lock(gid, feature, 0 if current_l else 1)
            await event.answer("⚙️ تم تغيير حالة القفل")
            # تحديث الأزرار فوراً بنفس الطريقة
            def get_s(f): return "🔒" if db.is_locked(gid, f) else "🔓"
            btns_updated = [
                [Button.inline(f"{get_s('links')} الروابط", "tg_links"), Button.inline(f"{get_s('usernames')} المعرفات", "tg_usernames")],
                [Button.inline(f"{get_s('photos')} الصور", "tg_photos"), Button.inline(f"{get_s('stickers')} الملصقات", "tg_stickers")],
                [Button.inline(f"{get_s('forward')} التوجيه", "tg_forward"), Button.inline(f"{get_s('videos')} الفيديوهات", "tg_videos")],
                [Button.inline("⬅️ رجوع", "show_main")]
            ]
            await event.edit("🔐 **إعدادات الحماية الفورية:**", buttons=btns_updated)

    # --- رتب النظام (تحديث الوصف ليتناسب مع الهرم الجديد) ---
    elif data == "show_ranks":
        ranks_text = (
            "🎖️ **الهرم الإداري في Monopoly:**\n"
            "━━━━━━━━━━━━━━\n"
            "👑 **المالك الأساسي (أنس):** حماية مطلقة وصلاحيات كاملة.\n"
            "👑 **المالك:** يتحكم بالمدراء وتحت.\n"
            "🎖️ **المدير:** يتحكم بالأدمن والمميز.\n"
            "🛡️ **الأدمن:** تنفيذ العقوبات (كتم، طرد، حظر).\n"
            "✨ **المميز:** محمي من بعض القيود التلقائية.\n"
            "━━━━━━━━━━━━━━"
        )
        await event.edit(ranks_text, buttons=[[Button.inline("⬅️ رجوع", "show_main")]])

    elif data == "show_cmds":
        # (بقاء نص الأوامر كما هو في ملفك الأصلي)
        await event.edit(event.text, buttons=[[Button.inline("⬅️ العودة للقائمة", "show_main")]])

    elif data == "show_settings":
        w_status = "✅ مفعل" if db.get_setting(gid, "welcome_status") == "on" else "❌ معطل"
        await event.edit("⚙️ **الإعدادات العامة للبوت:**", buttons=[[Button.inline(f"نظام الترحيب: {w_status}", "tg_welcome")],[Button.inline("⬅️ رجوع", "show_main")]])

    elif data == "close":
        await event.delete()
