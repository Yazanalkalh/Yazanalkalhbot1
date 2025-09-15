# -*- coding: utf-8 -*-
from flask import Flask
from threading import Thread
import os

# تهيئة تطبيق Flask
app = Flask('')

@app.route('/')
def home():
    """
    هذه هي الصفحة الرئيسية للخادم.
    وجودها يضمن أن Render Health Checks تنجح ويبقى البوت يعمل.
    """
    return "Bot web server is alive and running!"

def run():
    """
    تشغيل خادم Flask.
    يستخدم متغير البيئة PORT الذي توفره Render، أو 8080 كقيمة افتراضية.
    """
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def start_webserver():
    """
    تبدأ هذه الدالة خادم الويب في خيط منفصل (thread).
    هذا يمنع الخادم من إيقاف (blocking) عمل البوت الرئيسي.
    """
    try:
        # إنشاء خيط جديد لتشغيل دالة run
        server_thread = Thread(target=run)
        # تعيين الخيط كـ daemon يسمح للبرنامج الرئيسي بالخروج حتى لو كان الخيط لا يزال يعمل
        server_thread.daemon = True
        server_thread.start()
        return True
    except Exception as e:
        print(f"Error starting web server thread: {e}")
        return False