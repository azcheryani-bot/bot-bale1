import os
import requests
import time

# دریافت توکن‌ها از Secrets گیت‌هاب
GEMINI_KEY = os.getenv("GEMINI_KEY")
BALE_TOKEN = os.getenv("BALE_TOKEN")
# آدرس ورکر کلاودفلر خودت را اینجا بگذار
PROXY_URL = "crimson-scene-23ee.a-z-cheryani.workers.dev"

def get_gemini_response(user_text):
    try:
        # استفاده از آدرس ورکر به جای آدرس مستقیم گوگل
        url = f"https://{PROXY_URL}/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
        
        payload = {
            "contents": [{"parts": [{"text": user_text}]}]
        }
        
        print(f"--- Requesting via Worker Proxy ---", flush=True)
        response = requests.post(url, json=payload, timeout=20)
        res_json = response.json()
        
        if response.status_code == 200:
            return res_json['candidates'][0]['content']['parts'][0]['text']
        else:
            error_msg = res_json.get('error', {}).get('message', 'Unknown Error')
            return f"خطای گوگل: {error_msg}"
    except Exception as e:
        return f"خطای اتصال: {str(e)[:50]}"

def send_message(chat_id, text):
    url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=15)
    except:
        pass

def bot_loop():
    last_update_id = 0
    print("--- ربات (نسخه پروکسی گیت‌هاب) فعال شد ---", flush=True)
    
    # اجرا برای حدود ۶ ساعت (محدودیت گیت‌هاب اکشن)
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
                        print(f"Received: {text[:15]}", flush=True)
                        
                        reply = get_gemini_response(text)
                        send_message(chat_id, reply)
        except Exception as e:
            print(f"Loop Error: {e}", flush=True)
            time.sleep(5)
        time.sleep(1)

if __name__ == "__main__":
    bot_loop()
