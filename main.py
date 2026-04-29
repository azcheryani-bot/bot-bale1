import os
import requests
import time

GEMINI_KEY = os.getenv("GEMINI_KEY")
BALE_TOKEN = os.getenv("BALE_TOKEN")

def get_gemini_response(user_text):
    try:
        # استفاده از v1beta و مدل flash (چون تنها مدلی بود که قبلاً برای شما 404 نداد)
        # اضافه کردن پسوند :generateContent برای اطمینان از متد
        model = "gemini-1.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_KEY}"
        
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [
                {
                    "parts": [{"text": user_text}]
                }
            ]
        }
        
        print(f"--- Trying {model} via v1beta ---", flush=True)
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        res_json = response.json()
        
        if response.status_code == 200:
            return res_json['candidates'][0]['content']['parts'][0]['text']
        
        # اگر باز هم 404 داد، با یک مدل دیگر امتحان کن (Fallback)
        elif response.status_code == 404:
            print("--- Fallback to gemini-pro ---", flush=True)
            url_pro = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_KEY}"
            response = requests.post(url_pro, json=payload, headers=headers, timeout=15)
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            return "گوگل این مدل را در این منطقه پشتیبانی نمی‌کند."
            
        else:
            error_msg = res_json.get('error', {}).get('message', 'Unknown Error')
            return f"گوگل پاسخ نداد: {error_msg[:100]}"
            
    except Exception as e:
        return f"خطای سیستمی: {str(e)[:50]}"

def send_message(chat_id, text):
    url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10)
    except:
        pass

def bot_loop():
    last_update_id = 0
    print("--- ربات مجدداً با استراتژی جدید استارت خورد ---", flush=True)
    
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
                        print(f"Received: {text[:10]}", flush=True)
                        reply = get_gemini_response(text)
                        send_message(chat_id, reply)
        except Exception as e:
            time.sleep(5)
        time.sleep(1)

if __name__ == "__main__":
    bot_loop()
