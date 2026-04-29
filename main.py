import os
import requests
import time

# دریافت توکن‌ها از Secrets گیت‌هاب
GEMINI_KEY = os.getenv("GEMINI_KEY")
BALE_TOKEN = os.getenv("BALE_TOKEN")

def get_gemini_response(user_text):
    try:
        # استفاده از مدل پایدار
        model = "gemini-1.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_KEY}"
        
        payload = {"contents": [{"parts": [{"text": user_text}]}]}
        response = requests.post(url, json=payload, timeout=15)
        res_json = response.json()
        
        if response.status_code == 200:
            return res_json['candidates'][0]['content']['parts'][0]['text']
        elif response.status_code == 429:
            return "سهمیه رایگان تمام شده. کمی صبر کنید."
        else:
            return f"خطای گوگل: {res_json.get('error', {}).get('message', 'Error')}"
    except Exception as e:
        return f"خطا در اتصال: {str(e)[:50]}"

def send_message(chat_id, text):
    url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10)
    except:
        pass

def bot_loop():
    last_update_id = 0
    print("--- ربات بر روی گیت‌هاب فعال شد ---")
    
    # برای گیت‌هاب بهتر است یک زمان محدود (مثلاً ۵ ساعت) تعریف کنیم
    start_time = time.time()
    while time.time() - start_time < 20000: # حدود ۵.۵ ساعت اجرا
        try:
            url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=20"
            res = requests.get(url, timeout=30).json()
            
            if res.get("ok") and res.get("result"):
                for update in res["result"]:
                    last_update_id = update["update_id"]
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"]["text"]
                        print(f"Received: {text[:10]}")
                        reply = get_gemini_response(text)
                        send_message(chat_id, reply)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)
        time.sleep(1)

if __name__ == "__main__":
    bot_loop()
