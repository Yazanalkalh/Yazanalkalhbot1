from flask import Flask
from threading import Thread
import os

app = Flask(__name__)

@app.route('/')
def home():
    """هذا الرابط سيتم استدعاؤه من Render لإبقاء الخدمة نشطة."""
    return "Bot server is running!"

def run():
    """يقوم بتشغيل خادم Flask."""
    # Render يوفر متغير PORT تلقائياً
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

def start_webserver():
    """يبدأ تشغيل خادم الويب في خيط منفصل (thread)."""
    # التشغيل في خيط يضمن أن الخادم لا يمنع البوت من العمل
    server_thread = Thread(target=run)
    server_thread.start()



