import re
import io
import os
from telethon import events, types
from database import db
from hasher import get_image_hash
# استيراد العناصر الأساسية لضمان الانسجام
from __main__ import client, ALLOWED_GROUPS, check_privilege 

# استدعاء المسار الموحد من قاعدة البيانات مباشرة
PROTECT_DIR = db.base_dir

# خريطة الميزات (الاسم بالعربي : المفتاح في القاعدة)
FEATURES = {
    "الروابط": "links",
    "الصور": "photos",
    "الملصقات": "stickers",
    "المتحركة": "gifs",
    "التوجيه": "forward",
    "المعرفات": "usernames",
    "الفيديوهات": "videos",
    "البصمات": "voice",
    "الملفات": "files",
    "الجهات": "contacts",
    "الترحيب": "welcome_status"
}

# --- 1. معالج الحذف التلقائي (النسخة السريعة والمحمية) ---
@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def auto_protection_handler(event):
    # استثناء المقام السامي (أنس) والمدراء والمميزين من أي قيود
    if await check_privilege(event, "مميز"):
        return

    gid = str(event.chat_id)
    msg = event.raw_text or "" 

    try:
        # 1. فحص الروابط والمعرفات
        if db.is_locked(gid, "links") and re.search(r'(https?://\S+|t\.me/\S+|www\.\S+|\S+\.(me|xyz|info|tk|ml|ga|cf|gq|top|rocks|site|online))', msg):
            await event.delete()
            return

        if db.is_locked(gid, "usernames") and re.search(r'@\S+', msg):
            await event.delete()
            return

        # 2. فحص الوسائط (تحسين الأداء: لا يتم التحميل إلا عند الضرورة)
        if event.photo:
            if db.is_locked(gid, "photos"):
                await event.delete()
                return
            # فحص البصمة فقط إذا كانت الصورة مرسلة من عضو عادي
            photo_bytes = await event.download_media(file=io.BytesIO())
            if db.is_image_blacklisted(get_image_hash(photo_bytes)):
                await event.delete()
                return

        # فحص باقي الأقفال
        checks = {
            "stickers": event.sticker,
            "gifs": event.gif,
            "forward": event.fwd_from,
            "videos": (event.video or event.video_note),
            "voice": event.voice,
            "contacts": event.contact
        }
        
        for key, condition in checks.items():
            if condition and db.is_locked(gid, key):
                await event.delete()
                return

        # فحص الملفات
        if db.is_locked(gid, "files") and event.document and not any([event.voice, event.video, event.gif, event.sticker]):
            await event.delete()

    except Exception: pass 

# --- 2. أوامر التحكم الإداري (قفل / فتح) ---
@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def locks_control_handler(event):
    msg = event.raw_text
    gid = str(event.chat_id)

    # التحقق من أن المنفذ (مدير) فما فوق
    if not await check_privilege(event, "مدير"):
        return

    # معالجة أوامر القفل والفتح
    for ar_name, en_key in FEATURES.items():
        if msg == f"قفل {ar_name}":
            db.set_setting(gid, en_key, "off") if en_key == "welcome_status" else db.toggle_lock(gid, en_key, 1)
            await event.respond(f"🔒 تم قفل **{ar_name}** بنجاح.")
            return
        elif msg == f"فتح {ar_name}":
            db.set_setting(gid, en_key, "on") if en_key == "welcome_status" else db.toggle_lock(gid, en_key, 0)
            await event.respond(f"🔓 تم فتح **{ar_name}** بنجاح.")
            return

    # --- 3. أوامر خاصة بالدردشة (الفتح والقفل الذكي) ---
    if msg == "قفل الدردشة":
        try:
            # نغلق الدردشة على الجميع، لكن الكود في الأعلى سيستثنيك أنت والمدراء
            await client.edit_permissions(event.chat_id, send_messages=False)
            await event.respond("🚫 تم **إغلاق الدردشة**. (المقام السامي والمدراء فقط يمكنهم الكلام).")
        except: await event.respond("❌ فشل القفل.")
            
    elif msg == "فتح الدردشة":
        try:
            await client.edit_permissions(
                event.chat_id, 
                send_messages=True, send_media=True, send_stickers=True, 
                send_gifs=True, send_inline=True, embed_link_previews=True,
                invite_users=False, pin_messages=False, change_info=False
            )
            await event.respond("✅ تم **فتح الدردشة** (عادت الحياة للمملكة).")
        except: await event.respond("❌ فشل الفتح.")

    # --- 4. أوامر الوسائط الجماعية ---
    elif msg == "قفل الوسائط":
        for m in ["photos", "videos", "stickers", "gifs", "voice", "files"]:
            db.toggle_lock(gid, m, 1)
        await event.respond("🔒 تم قفل **جميع الوسائط**.")
        
    elif msg == "فتح الوسائط":
        for m in ["photos", "videos", "stickers", "gifs", "voice", "files"]:
            db.toggle_lock(gid, m, 0)
        await event.respond("🔓 تم فتح **جميع الوسائط**.")
