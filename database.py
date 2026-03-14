import sqlite3
import pickle
import os

class BotDB:
    def __init__(self):
        # --- [ توحيد المسار الملكي المعزول ] ---
        # المسار الرئيسي والموحد (المصدر الوحيد للحقيقة)
        self.base_dir = "/app/data/anas_bot"
        
        # التأكد من وجود المجلد وصلاحياته
        if not os.path.exists(self.base_dir):
            try:
                os.makedirs(self.base_dir, exist_ok=True)
                print(f"✅ تم إنشاء المجلد المعزول: {self.base_dir}")
            except Exception as e:
                print(f"⚠️ فشل إنشاء المجلد، سيتم استخدام المسار الافتراضي: {e}")
                self.base_dir = "/app/data"

        # تحديد مسار ملف قاعدة البيانات داخل المجلد المعزول
        self.db_path = os.path.join(self.base_dir, "misk_bot.db")
            
        # الاتصال بقاعدة البيانات
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # إنشاء الجداول الأساسية
        self.cursor.execute('CREATE TABLE IF NOT EXISTS ranks (gid TEXT, uid TEXT, rank TEXT, PRIMARY KEY(gid, uid))')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS locks (gid TEXT, feature TEXT, status INTEGER DEFAULT 0, PRIMARY KEY(gid, feature))')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS replies (gid TEXT, word TEXT, reply TEXT, media_id BLOB DEFAULT NULL, PRIMARY KEY(gid, word))')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS settings (gid TEXT, key TEXT, value TEXT, PRIMARY KEY(gid, key))')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS activity (gid TEXT, uid TEXT, count INTEGER DEFAULT 0, PRIMARY KEY(gid, uid))')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS image_blacklist (hash TEXT PRIMARY KEY)')
        
        try:
            self.cursor.execute('CREATE TABLE IF NOT EXISTS ranks_new (gid TEXT, uid TEXT, rank TEXT, PRIMARY KEY(gid, uid))')
            self.cursor.execute('INSERT OR IGNORE INTO ranks_new SELECT gid, uid, rank FROM ranks')
            self.cursor.execute('DROP TABLE ranks')
            self.cursor.execute('ALTER TABLE ranks_new RENAME TO ranks')
        except: pass 

        self.conn.commit()

    def increase_messages(self, gid, uid):
        self.cursor.execute("INSERT OR IGNORE INTO activity (gid, uid, count) VALUES (?, ?, 0)", (str(gid), str(uid)))
        self.cursor.execute("UPDATE activity SET count = count + 1 WHERE gid=? AND uid=?", (str(gid), str(uid)))
        self.conn.commit()

    def get_user_messages(self, gid, uid):
        self.cursor.execute("SELECT count FROM activity WHERE gid=? AND uid=?", (str(gid), str(uid)))
        row = self.cursor.fetchone()
        return row[0] if row else 0

    def get_top_active(self, gid, limit=5):
        self.cursor.execute("SELECT uid, count FROM activity WHERE gid=? ORDER BY count DESC LIMIT ?", (str(gid), limit))
        return self.cursor.fetchall()

    def is_globally_banned(self, uid):
        self.cursor.execute("SELECT 1 FROM ranks WHERE uid=? AND rank='مطرود' LIMIT 1", (str(uid),))
        return self.cursor.fetchone() is not None

    def set_rank(self, gid, uid, rank):
        self.cursor.execute("DELETE FROM ranks WHERE uid=?", (str(uid),))
        self.cursor.execute("INSERT INTO ranks (gid, uid, rank) VALUES (?, ?, ?)", (str(gid), str(uid), rank))
        self.conn.commit()

    def get_rank(self, gid, uid):
        self.cursor.execute("SELECT rank FROM ranks WHERE uid=? LIMIT 1", (str(uid),))
        row = self.cursor.fetchone()
        return row[0] if row else "عضو"

    def get_rank_value(self, uid):
        rank_name = self.get_rank(None, uid)
        ranks_weight = {"المنشئ": 5, "مالك": 4, "مدير": 3, "ادمن": 2, "مميز": 1, "عضو": 0}
        return ranks_weight.get(rank_name, 0)

    def toggle_lock(self, gid, feature, status):
        self.cursor.execute("INSERT OR REPLACE INTO locks (gid, feature, status) VALUES (?, ?, ?)", (str(gid), feature, status))
        self.conn.commit()

    def is_locked(self, gid, feature):
        self.cursor.execute("SELECT status FROM locks WHERE gid=? AND feature=?", (str(gid), feature))
        row = self.cursor.fetchone()
        return row[0] == 1 if row else False

    def set_reply(self, gid, word, reply_text, media_id=None):
        self.cursor.execute("DELETE FROM replies WHERE gid=? AND word=?", (str(gid), word))
        m_data = pickle.dumps(media_id) if media_id else None
        self.cursor.execute("INSERT INTO replies (gid, word, reply, media_id) VALUES (?, ?, ?, ?)", (str(gid), word, reply_text, m_data))
        self.conn.commit()

    def delete_reply(self, gid, word):
        self.cursor.execute("DELETE FROM replies WHERE gid=? AND word=?", (str(gid), word))
        self.conn.commit()

    def get_reply_data(self, gid, word):
        self.cursor.execute("SELECT reply, media_id FROM replies WHERE gid=? AND word=?", (str(gid), word))
        row = self.cursor.fetchone()
        if row:
            reply_text, m_data = row
            try:
                media_obj = pickle.loads(m_data) if m_data else None
            except:
                media_obj = None
            return reply_text, media_obj
        return None

    def set_setting(self, gid, key, value):
        self.cursor.execute("INSERT OR REPLACE INTO settings (gid, key, value) VALUES (?, ?, ?)", (str(gid), key, value))
        self.conn.commit()

    def get_setting(self, gid, key):
        self.cursor.execute("SELECT value FROM settings WHERE gid=? AND key=?", (str(gid), key))
        row = self.cursor.fetchone()
        return row[0] if row else "off"

    def add_image_hash(self, img_hash):
        self.cursor.execute("INSERT OR IGNORE INTO image_blacklist (hash) VALUES (?)", (img_hash,))
        self.conn.commit()

    def is_image_blacklisted(self, img_hash):
        self.cursor.execute("SELECT 1 FROM image_blacklist WHERE hash=? LIMIT 1", (img_hash,))
        return self.cursor.fetchone() is not None

db = BotDB()
