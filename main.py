import os
import requests
import time

GEMINI_KEY = os.getenv("GEMINI_KEY")
BALE_TOKEN = os.getenv("BALE_TOKEN")

def get_gemini_response(user_text):
    try:
        # استفاده از ورژن 1 (پایدار) و مدل 1.5 فلش که جدیدترین استاندارد است
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
        
        headers = {'Content-Type': 'application/json'}
        # ساختار بدنه درخواست در ورژن 1 کمی دقیق‌تر است
        payload = {
            "contents": [{
                "parts": [{"text": user_text}]
            }]
        }
        
        print("--- Connecting via v1 Endpoint ---", flush=True)
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        res_json = response.json()
        
        if response.status_code == 200:
            return res_json['candidates'][0]['content']['parts'][0]['text']
        
        # اگر باز هم خطای منطقه یا مدل داد، از مدل جایگزین در v1 استفاده می‌کنیم
        elif response.status_code == 404 or response.status_code == 400:
            print("--- Attempting fallback to Pro model in v1 ---", flush=True)
            url_pro = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={GEMINI_KEY}"
            response = requests.post(url_pro, json=payload, headers=headers, timeout=15)
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            
            return "متأسفانه گوگل این سرور را مسدود کرده است. لطفاً از کلید دیگری استفاده کنید."
            
        else:
            error_msg = res_json.get('error', {}).get('message', 'Unknown Error')
            return f"خطای گوگل: {error_msg}"
            
    except Exception as e:
        return f"خطای ارتباط: {str(e)[:50]}"

def send_message(chat_id, text):
    url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10)
    except:
        pass

def bot_loop():
    last_update_id = 0
    print("--- ربات با آدرس دهی v1 فعال شد ---", flush=True)
    
    start_time = time.time()
    while time.time() - start_time < 21000: 
        try:
            url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=20"
            resp = requests.get(url, timeout=30)
            res = resp.json()
            
            if res.get("ok") and res.get("result"):
                for update in res["result"]:
                    last_update_id = update["update_id"]
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"]["text"]
                        print(f"Received: {text[:10]}", flush=True)
                        reply = get_gemini_response(text)
                        send_message(chat_id, reply)
        except:
            time.sleep(5)
        time.sleep(1)

if __name__ == "__main__":
    bot_loop()
