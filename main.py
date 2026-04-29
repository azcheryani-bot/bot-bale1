import os
import time
import requests
import base64

# --- تنظیمات اولیه از طریق Secrets گیت‌هاب ---
GEMINI_KEY = os.getenv("GEMINI_KEY")
BALE_TOKEN = os.getenv("BALE_TOKEN")
PROXY_DOMAIN = "crimson-scene-23ee.a-z-cheryani.workers.dev"

def download_bale_file(file_id, is_image=True):
    """دانلود فایل از سرور بله و تبدیل به فرمت قابل فهم برای جمینی"""
    try:
        get_file_url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/getFile?file_id={file_id}"
        file_info = requests.get(get_file_url).json()
        
        if file_info.get("ok"):
            file_path = file_info["result"]["file_path"]
            download_url = f"https://tapi.bale.ai/file/bot{BALE_TOKEN}/{file_path}"
            file_content = requests.get(download_url).content
            
            if is_image:
                # تبدیل عکس به Base64 برای ارسال به گوگل
                return base64.b64encode(file_content).decode('utf-8'), "image/jpeg"
            else:
                # خواندن متن داخل فایل (مثل .txt یا .py)
                return file_content.decode('utf-8'), None
    except Exception as e:
        print(f"!!! Download Error: {e}", flush=True)
    return None, None

def get_gemini_response(user_text, image_data=None, mime_type=None):
    """ارسال داده‌ها به جمینی ۲.۵ فلش از طریق ورکر کلاودفلر"""
    try:
        url = f"https://{PROXY_DOMAIN}/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
        
        parts = []
        if user_text:
            parts.append({"text": user_text})
        
        if image_data:
            parts.append({
                "inline_data": {
                    "mime_type": mime_type or "image/jpeg",
                    "data": image_data
                }
            })

        if not parts:
            return "پیام شما خالی است."

        payload = {"contents": [{"parts": parts}]}
        print(f"--- Sending request to Gemini (Multi-modal) ---", flush=True)
        response = requests.post(url, json=payload, timeout=45)
        
        if response.status_code == 200:
            res_json = response.json()
            return res_json['candidates'][0]['content']['parts'][0]['text']
        else:
            print(f"!!! Google Error: {response.status_code} - {response.text[:100]}", flush=True)
            return f"خطای گوگل: {response.status_code}"
            
    except Exception as e:
        print(f"!!! Gemini Request Error: {e}", flush=True)
        return "خطا در ارتباط با هوش مصنوعی."

def bot_loop():
    """حلقه اصلی ربات با پشتیبانی از فایل و عکس"""
    last_id = 0
    print("--- Bale Bot (Full Version) Started ---", flush=True)
    
    start_time = time.time()
    # اجرا برای ۵ ساعت و ۵۰ دقیقه
    while time.time() - start_time < 21000:
        try:
            updates_url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/getUpdates?offset={last_id + 1}&timeout=20"
            response = requests.get(updates_url, timeout=30)
            res = response.json()
            
            if res.get("ok") and res.get("result"):
                for update in res["result"]:
                    last_id = update["update_id"]
                    message = update.get("message", {})
                    chat_id = message.get("chat", {}).get("id")
                    if not chat_id: continue

                    user_text = message.get("text") or message.get("caption")
                    image_data = None
                    mime_type = None

                    # ۱. بررسی وجود عکس
                    if "photo" in message:
                        file_id = message["photo"][-1]["file_id"] # گرفتن باکیفیت‌ترین نسخه
                        image_data, mime_type = download_bale_file(file_id, is_image=True)
                        if not user_text: user_text = "این تصویر را تحلیل کن"

                    # ۲. بررسی وجود فایل متنی
                    elif "document" in message:
                        file_id = message["document"]["file_id"]
                        f_name = message["document"].get("file_name", "").lower()
                        # لیست فرمت‌های متنی مجاز
                        if f_name.endswith(('.txt', '.py', '.json', '.js', '.cpp', '.h', '.html', '.css')):
                            content, _ = download_bale_file(file_id, is_image=False)
                            if content:
                                user_text = f"محتوای فایل '{f_name}':\n\n{content}\n\nتوضیح کاربر: {user_text or 'این فایل را بررسی کن'}"

                    # ارسال به جمینی اگر متن یا عکسی وجود داشت
                    if user_text or image_data:
                        print(f"Processing message from {chat_id}", flush=True)
                        reply = get_gemini_response(user_text, image_data, mime_type)
                        
                        send_url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage"
                        requests.post(send_url, json={"chat_id": chat_id, "text": reply}, timeout=20)
                        print(f"Reply sent to {chat_id}", flush=True)
                            
        except Exception as e:
            print(f"!!! Loop Error: {e}", flush=True)
            time.sleep(5)
            
        time.sleep(1)

if __name__ == "__main__":
    bot_loop()
