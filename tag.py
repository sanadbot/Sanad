import asyncio
from telethon import events, types
from database import db
# التعديل لمنع Circular Import وتعليق قاعدة البيانات
from __main__ import client, ALLOWED_GROUPS, check_privilege 

# قاموس لتتبع عمليات التاغ الجارية لإمكانية إيقافها
active_tagging = {}

@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def tag_handler(event):
    msg = event.raw_text
    chat_id = event.chat_id
    gid = str(chat_id)

    # التحقق من الصلاحية (يجب أن يكون مدير فأعلى لاستخدام التاغ)
    if not await check_privilege(event, "مدير"):
        return

    # --- 1. أمر بدء المنشن (تاغ للكل) الشامل ---
    if msg in ["تاغ", "منشن", "تاق"]:
        # إذا كانت هناك عملية منشن جارية، نمنع البدء بجديدة لتجنب تكرار الرسائل
        if gid in active_tagging and active_tagging[gid]:
            await event.respond("⚠️ هناك عملية **تاغ ملكية** جارية بالفعل!")
            return

        active_tagging[gid] = True
        await event.respond("📣 جاري بدء **المنشن الشامل** لجميع أعضاء Monopoly...")

        # جلب قائمة الأعضاء بالكامل من المجموعة
        members = await client.get_participants(chat_id)
        
        # تقسيم الأعضاء لمجموعات (مثلاً 5 أعضاء في كل رسالة لتجنب سبام التليجرام)
        chunk_size = 5
        for i in range(0, len(members), chunk_size):
            # التحقق إذا قام الإدمن بإيقاف التاغ يدوياً أثناء العملية
            if not active_tagging.get(gid, False):
                break
            
            chunk = members[i:i + chunk_size]
            tag_msg = ""
            for user in chunk:
                if not user.bot: # استثناء البوتات من المنشن لتقليل الزخم
                    tag_msg += f"[{user.first_name}](tg://user?id={user.id})  "
            
            if tag_msg:
                try:
                    await client.send_message(chat_id, tag_msg)
                    # تأخير بسيط (2 ثانية) لتجنب حظر البوت مؤقتاً (Flood Wait)
                    await asyncio.sleep(2)
                except Exception:
                    continue

        if active_tagging.get(gid):
            await event.respond("✅ تم اكتمال **المنشن الشامل** بنجاح يا مدير.")
            active_tagging[gid] = False

    # --- 2. أمر إيقاف المنشن يدوياً ---
    elif msg in ["ايقاف التاغ", "ايقاف المنشن", "وقف التاغ"]:
        if gid in active_tagging and active_tagging[gid]:
            active_tagging[gid] = False
            await event.respond("🛑 تم **إيقاف** عملية المنشن بنجاح بطلب من الإدارة.")
        else:
            await event.respond("❌ لا توجد عملية **تاغ** نشطة حالياً لإيقافها.")

    # --- 3. أمر منشن مخصص للمدراء فقط ---
    elif msg in ["تاغ للمدراء", "منشن للمدراء"]:
        await event.respond("📢 جاري استدعاء **طاقم الإدارة الموقر**...")
        # استخدام الفلتر الصحيح من تليثون لجلب الإدمنية فقط
        admins = await client.get_participants(chat_id, filter=types.ChannelParticipantsAdmins())
        
        admin_tags = "👮‍♂️ **نداء عاجل لطاقم الإدارة:**\n\n"
        for admin in admins:
            if not admin.bot:
                admin_tags += f"▫️ [{admin.first_name}](tg://user?id={admin.id})\n"
        
        await client.send_message(chat_id, admin_tags)
