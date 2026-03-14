import os
import io
from telethon import events
from database import db
from hasher import get_image_hash
# استيراد العناصر الأساسية من الملف الرئيسي
from __main__ import client, ALLOWED_GROUPS, check_privilege 

# استدعاء المسار الموحد من قاعدة البيانات مباشرة
PROTECT_DIR = db.base_dir

@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def ranks_manager_system(event):
    msg = event.raw_text
    gid = str(event.chat_id)

    # التحقق من الصلاحية (ادمن فأعلى)
    if not await check_privilege(event, "ادمن"):
        return

    # --- ميزة حظر بصمة الصورة (الميزة الوحيدة التي تركناها هنا لمنع الزحام في main) ---
    if msg == "حظر صورة" and event.is_reply:
        reply_msg = await event.get_reply_message()
        if reply_msg and reply_msg.photo:
            try:
                photo_bytes = await reply_msg.download_media(file=io.BytesIO())
                img_hash = get_image_hash(photo_bytes)
                db.add_image_hash(img_hash)
                await reply_msg.delete()
                await event.respond("🚫 **تم حظر بصمة هذه الصورة بنجاح.**\nسيتم حذفها تلقائياً إذا أرسلها عضو آخر.")
            except Exception as e:
                print(f"Error in Image Hash: {e}")
                await event.respond("❌ فشل حظر بصمة الصورة.")
        else:
            await event.respond("⚠️ يرجى الرد على صورة بكلمة 'حظر صورة'.")

# تم نقل أوامر (رفع، تنزيل، كتم، حظر، كشف) إلى ملف main.py لمنع التداخل والردود المزدوجة.
