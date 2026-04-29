import os
import json
import time
import subprocess
import requests

# --- تنظیمات توکن‌ها (این‌ها را در GitHub Secrets ست کرده‌اید) ---
GEMINI_KEY = os.getenv("GEMINI_KEY")
BALE_TOKEN = os.getenv("BALE_TOKEN")

# --- تنظیمات کانفیگ V2Ray (بر اساس VMess شما) ---
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
    """دانلود، نصب و اجرای V2Ray Core"""
    try:
        print("--- Downloading V2Ray Core ---", flush=True)
        # دانلود هسته لینوکس 64 بیت
        os.system("curl -L -o v2ray.zip https://github.com/v2fly/v2ray-core/releases/latest/download/v2ray-linux-64.zip")
        os.system("unzip -o v2ray.zip && chmod +x v2ray")
        
        # نوشتن فایل تنظیمات
        with open("config.json", "w") as f:
            json.dump(V2_CONFIG, f)
        
        print("--- Starting V2Ray Tunnel ---", flush=True)
        # اجرای وی‌توری در پس‌زمینه
        subprocess.Popen(["./v2ray", "run", "-c", "config.json"])
        
        # زمان دادن به تونل برای برقراری اتصال (۱۰ ثانیه)
        time.sleep(10)
        print("--- Tunnel should be ready now ---", flush=True)
    except Exception as e:
        print(f"Setup Error: {e}", flush=True)

def get_gemini_response(user_text):
    """ارسال درخواست به جمینی از داخل تونل SOCKS5"""
    try:
        # استفاده از ورژن v1 (پایدار)
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
        
        # پروکسی محلی که توسط وی‌توری ایجاد شده
        # استفاده از socks5h برای انتقال DNS از داخل تونل
        proxies = {
            "http": "socks5h://127.0.0.1:10808",
            "https": "socks5h://127.0.0.1:10808"
        }
        
        payload = {
            "contents": [{"parts": [{"text": user_text}]}]
        }
        
        print(f"--- Sending request to Gemini via V2Ray Tunnel ---", flush=True)
        response = requests.post(url, json=payload, proxies=proxies, timeout=30)
        
        if response.status_code == 200:
            res_json = response.json()
            return res_json['candidates'][0]['content']['parts'][0]['text']
        else:
            err_data = response.json()
            err_msg = err_data.get('error', {}).get('message', 'Unknown Error')
            print(f"!!! Google Error {response.status_code}: {err_msg}", flush=True)
            return f"خطا از سمت گوگل (پروکسی متصل است): {err_msg[:100]}"
            
    except Exception as e:
        print(f"!!! Request Exception: {e}", flush=True)
        return "تونل وی‌توری پاسخگو نیست. احتمالاً سرور قطع شده است."

def send_message(chat_id, text):
    """ارسال پیام مستقیم به بله (بدون پروکسی)"""
    url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage"
    try:
        # بله در خارج از ایران فیلتر نیست، پس مستقیم می‌فرستیم تا سریع‌تر باشد
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=15)
    except Exception as e:
        print(f"Bale Send Error: {e}", flush=True)

def bot_loop():
    """حلقه اصلی ربات"""
    setup_v2ray()
    last_update_id = 0
    print("--- Bale Bot is Running with V2Ray Tunnel ---", flush=True)
    
    # اجرای اکشن برای حدود ۶ ساعت
    start_time = time.time()
    while time.time() - start_time < 21000:
        try:
            # دریافت پیام‌ها از بله
            url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=20"
            response = requests.get(url, timeout=30)
            res = response.json()
            
            if res.get("ok") and res.get("result"):
                for update in res["result"]:
                    last_update_id = update["update_id"]
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        user_text = update["message"]["text"]
                        
                        print(f"New Msg from {chat_id}: {user_text[:15]}", flush=True)
                        reply = get_gemini_response(user_text)
                        send_message(chat_id, reply)
        except Exception as e:
            print(f"Loop Error: {e}", flush=True)
            time.sleep(5)
        
        time.sleep(1)

if __name__ == "__main__":
    bot_loop()
