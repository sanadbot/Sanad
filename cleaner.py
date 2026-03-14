import asyncio
import os
import re
from telethon import events, functions, types
from database import db
from __main__ import client, ALLOWED_GROUPS, check_privilege 

OWNER_ID = 5010882230

# دالة مساعدة لجلب معرف المستخدم سواء كان بالرد، اليوزر، أو الآي دي
async def get_user_from_event(event):
    if event.is_reply:
        reply = await event.get_reply_message()
        return reply.sender_id
    
    args = event.text.split()
    if len(args) > 1:
        user_input = args[1]
        try:
            if user_input.isdigit(): return int(user_input)
            user_entity = await client.get_entity(user_input)
            return user_entity.id
        except: return None
    return None

@client.on(events.NewMessage(chats=ALLOWED_GROUPS))
async def cleaner_handler(event):
    msg = event.raw_text
    chat_id = event.chat_id

    # --- [ 1. نظام الرفع والتنزيل ] ---
    if msg.startswith(("رفع ادمن", "رفع مميز", "تنزيل")):
        if not await check_privilege(event, "ادمن"): return
        target_id = await get_user_from_event(event)
        if not target_id: return await event.respond("⚠️ يرجى استخدام الرد أو وضع اليوزر/الآي دي.")
        
        if "رفع ادمن" in msg:
            # الرفع لمرتبة ادمن حصراً للمدير والمالك
            if not await check_privilege(event, "مدير"): return
            db.set_rank(chat_id, target_id, "ادمن")
            await event.respond(f"🎖️ تم رفع المستخدم ({target_id}) إلى **ادمن**.")
        
        elif "رفع مميز" in msg:
            # الرفع لمميز متاح للادمن فما فوق
            db.set_rank(chat_id, target_id, "مميز")
            await event.respond(f"🌟 تم منح المستخدم ({target_id}) رتبة **مميز**.")
            
        elif "تنزيل" in msg:
            if target_id == OWNER_ID: return await event.respond("⚠️ حماية ملكية: لا يمكن تنزيل المالك.")
            db.set_rank(chat_id, target_id, "عضو")
            await event.respond(f"📉 تم تنزيل المستخدم ({target_id}) إلى رتبة **عضو**.")

    # --- [ 2. نظام العقوبات (الآن متاح بالكامل للأدمن) ] ---
    if msg.startswith(("كتم", "حظر", "طرد", "تقييد", "انذار", "الغاء الكتم", "رفع الكتم", "فك التقييد", "الغاء التقييد")):
        # فحص: هل الشخص المرسل ادمن فما فوق؟
        if not await check_privilege(event, "ادمن"): return
        
        target_id = await get_user_from_event(event)
        if not target_id: return
        if target_id == OWNER_ID: return await event.respond("👑 لا يمكن تنفيذ عقوبة بحق المالك.")
        
        try:
            # الكتم والتقييد
            if msg.startswith(("كتم", "تقييد")):
                await client.edit_permissions(chat_id, target_id, send_messages=False)
                await event.respond(f"🚫 تم تقييد/كتم المستخدم ({target_id}) بنجاح.")
            
            # الحظر والطرد (تم تعديل الصلاحية لتصبح لـ "الادمن" أيضاً)
            elif msg.startswith(("حظر", "طرد")):
                await client.kick_participant(chat_id, target_id)
                await event.respond(f"✈️ تم طرد المستخدم ({target_id}) من المجموعة.")
            
            # رفع العقوبات
            elif msg.startswith(("الغاء الكتم", "رفع الكتم", "فك التقييد", "الغاء التقييد")):
                await client.edit_permissions(chat_id, target_id, send_messages=True, send_media=True, send_stickers=True, send_gifs=True)
                await event.respond(f"😇 تم رفع القيود عن المستخدم ({target_id}).")
            
            # الإنذار
            elif msg.startswith("انذار"):
                await event.respond(f"⚠️ إنذار رسمي للمستخدم ({target_id}).")
                
        except Exception as e:
            await event.respond(f"❌ فشل التنفيذ: تأكد من أن البوت مشرف ولديه صلاحيات كاملة.")

    # --- [ 3. نظام المسح (متاح للأدمن) ] ---
    if msg.startswith("مسح "):
        if not await check_privilege(event, "ادمن"): return
        parts = msg.split()
        if len(parts) > 1 and parts[1].isdigit():
            num = min(int(parts[1]), 100)
            await event.delete()
            msgs = await client.get_messages(chat_id, limit=num)
            await client.delete_messages(chat_id, msgs)
            confirm = await event.respond(f"🗑️ تم تطهير **{len(msgs)}** رسالة.")
            await asyncio.sleep(2)
            await confirm.delete()
