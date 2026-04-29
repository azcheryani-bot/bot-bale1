import os
import time
import requests

# تنظیمات
GEMINI_KEY = os.getenv("GEMINI_KEY")
BALE_TOKEN = os.getenv("BALE_TOKEN")

# استفاده از یک پروکسی HTTPS رایگان و معتبر به جای V2Ray برای تست پایداری
# یا استفاده از آدرس ورکر کلاودفلر که قبلا ساختی (امن‌ترین راه)
PROXY_DOMAIN = "crimson-scene-23ee.a-z-cheryani.workers.dev"

def get_gemini_response(user_text):
    try:
        # دقت کن که v1/models/... بعد از دامنه ورکر حتما باشد
        url = f"https://{PROXY_DOMAIN}/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
        
        payload = {
            "contents": [{
                "parts": [{"text": user_text}]
            }]
        }
        
        # در این روش نیازی به Proxies در requests نیست چون ورکر خودش نقش پروکسی را دارد
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            res_json = response.json()
            return res_json['candidates'][0]['content']['parts'][0]['text']
        else:
            # این بخش به ما می‌گوید گوگل دقیقاً چه ایرادی گرفته
            return f"گوگل ارور داد: {response.status_code} - {response.text[:100]}"
    except Exception as e:
        return f"خطای اتصال به ورکر: {str(e)[:50]}"

def bot_loop():
    last_id = 0
    print("--- Bot Started on GitHub Actions ---", flush=True)
    start_time = time.time()
    
    while time.time() - start_time < 20000: # حدود ۵.۵ ساعت
        try:
            updates_url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/getUpdates?offset={last_id + 1}&timeout=20"
            res = requests.get(updates_url, timeout=30).json()
            
            if res.get("ok") and res.get("result"):
                for update in res["result"]:
                    last_id = update["update_id"]
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"]["text"]
                        
                        reply = get_gemini_response(text)
                        
                        send_url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage"
                        requests.post(send_url, json={"chat_id": chat_id, "text": reply})
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)
        time.sleep(1)

if __name__ == "__main__":
    bot_loop()
