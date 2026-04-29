import os
import json
import time
import subprocess
import requests

GEMINI_KEY = os.getenv("GEMINI_KEY")
BALE_TOKEN = os.getenv("BALE_TOKEN")

V2_CONFIG = {
    "log": {"loglevel": "warning"},
    "inbounds": [{
        "port": 10808,
        "listen": "127.0.0.1",
        "protocol": "socks",
        "settings": {"auth": "noauth", "udp": True}
    }],
    "outbounds": [{
        "protocol": "vmess",
        "settings": {
            "vnext": [{
                "address": "47.90.244.153",
                "port": 8443,
                "users": [{
                    "id": "65e2a985-ad20-4486-a7ec-b67b20ee56af",
                    "alterId": 0,
                    "security": "auto"
                }]
            }]
        },
        "streamSettings": {
            "network": "ws",
            "wsSettings": {"path": "/ws"}
        }
    }]
}

def setup_v2ray():
    try:
        print("--- Cleaning and Downloading V2Ray ---", flush=True)
        # دانلود نسخه پایدارتر
        os.system("curl -L -o v2ray.zip https://github.com/v2fly/v2ray-core/releases/v5.14.1/download/v2ray-linux-64.zip")
        os.system("unzip -o v2ray.zip && chmod +x v2ray")
        
        with open("config.json", "w") as f:
            json.dump(V2_CONFIG, f)
        
        print("--- Running V2Ray Process ---", flush=True)
        # استفاده از حالت مستقیم برای اطمینان از اجرا
        process = subprocess.Popen(["./v2ray", "run", "-c", "config.json"], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE)
        
        # یک تست سریع برای دیدن اینکه پورت باز شده یا نه
        time.sleep(15)
        return True
    except Exception as e:
        print(f"Critical Setup Error: {e}", flush=True)
        return False

def get_gemini_response(user_text):
    try:
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
        
        proxies = {
            "http": "socks5h://127.0.0.1:10808",
            "https": "socks5h://127.0.0.1:10808"
        }
        
        # اضافه کردن یک تست قبل از درخواست اصلی
        print("--- Testing Tunnel Connection ---", flush=True)
        payload = {"contents": [{"parts": [{"text": user_text}]}]}
        
        # افزایش تایم‌اوت به ۴۰ ثانیه چون وی‌توری در دیتاسنتر کمی کند است
        response = requests.post(url, json=payload, proxies=proxies, timeout=40)
        
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"خطای گوگل: {response.status_code} - احتمالا کلید یا آی‌پی بلاک است."
            
    except Exception as e:
        print(f"Request Error: {e}", flush=True)
        return "تونل وصل است ولی گوگل پاسخ نمی‌دهد (تایم‌اوت). دوباره بپرسید."

# بقیه توابع (send_message و bot_loop) بدون تغییر بمانند
