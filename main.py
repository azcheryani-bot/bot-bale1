import os
import requests
import time

GEMINI_KEY = os.getenv("GEMINI_KEY")
BALE_TOKEN = os.getenv("BALE_TOKEN")

def get_gemini_response(user_text):
    try:
        # استفاده از قدیمی‌ترین و پایدارترین مدل برای عبور از محدودیت منطقه
        # مدل gemini-1.0-pro کمترین حساسیت را به آی‌پی دیتاسنترها دارد
        model = "gemini-1.0-pro"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_KEY}"
        
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [{"parts": [{"text": user_text}]}]
        }
        
        print(f"--- Trying to bypass region lock with {model} ---", flush=True)
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        res_json = response.json()
        
        if response.status_code == 200:
            return res_json['candidates'][0]['content']['parts'][0]['text']
        
        elif response.status_code == 403:
            return "گوگل دسترسی این سرور را به دلیل محدودیت منطقه‌ای مسدود کرده است. باید از پروکسی استفاده شود."
        
        else:
            error_msg = res_json.get('error', {}).get('message', 'Unknown Error')
            print(f"!!! Status {response.status_code}: {error_msg}", flush=True)
            return f"خطای سرویس: {error_msg[:100]}"
            
    except Exception as e:
        return f"خطای اتصال شبکه: {str(e)[:50]}"

def send_message(chat_id, text):
    url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10)
    except:
        pass

def bot_loop():
    last_update_id = 0
    print("--- ربات با مدل کلاسیک استارت خورد ---", flush=True)
    
    start_time = time.time()
    while time.time() - start_time < 21000: 
        try:
            url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=20"
            res = requests.get(url, timeout=30).json()
            
            if res.get("ok") and res.get("result"):
                for update in res["result"]:
                    last_update_id = update["update_id"]
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"]["text"]
                        print(f"New Message: {text[:10]}", flush=True)
                        reply = get_gemini_response(text)
                        send_message(chat_id, reply)
        except:
            time.sleep(5)
        time.sleep(1)

if __name__ == "__main__":
    bot_loop()
