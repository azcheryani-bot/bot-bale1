import os
import time
import requests

# --- تنظیمات اولیه از طریق Secrets گیت‌هاب ---
GEMINI_KEY = os.getenv("GEMINI_KEY")
BALE_TOKEN = os.getenv("BALE_TOKEN")

# آدرس ورکر کلاودفلر شما
PROXY_DOMAIN = "crimson-scene-23ee.a-z-cheryani.workers.dev"

def get_gemini_response(user_text):
    """ارسال متن به گوگل از طریق ورکر کلاودفلر"""
    try:
        # آدرس کامل API جمینی نسخه v1
        url = f"https://{PROXY_DOMAIN}/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}"
        
        payload = {
            "contents": [{
                "parts": [{"text": user_text}]
            }]
        }
        
        print(f"--- Sending request to Gemini via Cloudflare ---", flush=True)
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            res_json = response.json()
            # استخراج متن پاسخ از ساختار JSON گوگل
            return res_json['candidates'][0]['content']['parts'][0]['text']
        else:
            # در صورت خطا، متن خطا را برای دی‌باگ برمی‌گردانیم
            error_info = response.text[:100]
            print(f"!!! Google Error: {response.status_code} - {error_info}", flush=True)
            return f"خطای گوگل: {response.status_code}. لطفاً دوباره تلاش کنید."
            
    except Exception as e:
        print(f"!!! Connection Error: {e}", flush=True)
        return "متأسفانه ارتباط با سرور هوش مصنوعی برقرار نشد."

def bot_loop():
    """حلقه اصلی برای دریافت و پاسخ به پیام‌های بله"""
    last_id = 0
    print("--- Bale Bot Started ---", flush=True)
    
    # ثبت زمان شروع اجرا
    start_time = time.time() 
    
    # این همان خط مورد نظر است که اجازه می‌دهد ربات حدود ۵ ساعت و ۵۰ دقیقه بیدار بماند
    while time.time() - start_time < 21000: 
        try:
            # دریافت پیام‌ها از بله
            updates_url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/getUpdates?offset={last_id + 1}&timeout=20"
            response = requests.get(updates_url, timeout=30)
            res = response.json()
            
            if res.get("ok") and res.get("result"):
                for update in res["result"]:
                    last_id = update["update_id"]
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        user_text = update["message"]["text"]
                        
                        print(f"Received message from {chat_id}", flush=True)
                        
                        # دریافت پاسخ از جمینی
                        reply = get_gemini_response(user_text)
                        
                        # ارسال پاسخ به کاربر در بله
                        send_url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage"
                        post_res = requests.post(send_url, json={"chat_id": chat_id, "text": reply}, timeout=15)
                        
                        if post_res.status_code == 200:
                            print(f"Reply sent successfully.", flush=True)
                        else:
                            print(f"Failed to send reply to Bale: {post_res.status_code}", flush=True)
                            
        except Exception as e:
            print(f"Loop Error: {e}", flush=True)
            time.sleep(5) # صبر در صورت بروز خطای شبکه
            
        time.sleep(1) # وقفه کوتاه بین هر بررسی

if __name__ == "__main__":
    bot_loop()
