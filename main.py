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
                return base64.b64encode(file_content).decode('utf-8'), "image/jpeg"
            else:
                return file_content.decode('utf-8'), None
    except Exception as e:
        print(f"!!! Download Error: {e}", flush=True)
    return None, None

def get_gemini_response(user_text, image_data=None, mime_type=None):
    """تلاش برای گرفتن پاسخ با سوئیچ خودکار بین تمام مدل‌های تصویر ارسالی شما"""
    
    # لیست کامل مدل‌ها بر اساس اولویت قدرت و تازگی (سال ۲۰۲۶)
    models_to_try = [
        "gemini-3.0-pro",
        "gemini-3.0-flash",
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b"
    ]
    
    last_status = ""

    for model_name in models_to_try:
        try:
            url = f"https://{PROXY_DOMAIN}/v1beta/models/{model_name}:generateContent?key={GEMINI_KEY}"
            
            parts = []
            if user_text: parts.append({"text": user_text})
            if image_data:
                parts.append({
                    "inline_data": {
                        "mime_type": mime_type or "image/jpeg",
                        "data": image_data
                    }
                })

            if not parts: return "پیام خالی است."

            payload = {"contents": [{"parts": parts}]}
            print(f"--- Trying model: {model_name} ---", flush=True)
            
            response = requests.post(url, json=payload, timeout=45)
            
            if response.status_code == 200:
                res_json = response.json()
                return res_json['candidates'][0]['content']['parts'][0]['text']
            
            # اگر خطای Quota (429) یا سرور (503/500/404) داد، برو سراغ بعدی
            else:
                print(f"!!! {model_name} failed with status {response.status_code}. Switching...", flush=True)
                last_status = f"خطای {response.status_code}"
                continue

        except Exception as e:
            print(f"!!! Error with {model_name}: {e}", flush=True)
            continue

    return f"متأسفانه هیچ‌کدام از مدل‌ها در حال حاضر پاسخگو نیستند. (آخرین وضعیت: {last_status})"

def bot_loop():
    """حلقه اصلی ربات با پشتیبانی از متن، عکس و فایل‌های متنی"""
    last_id = 0
    print("--- Bale Gemini Multi-Model Bot Started ---", flush=True)
    
    start_time = time.time()
    # ۵ ساعت و ۵۰ دقیقه اجرا برای هماهنگی با GitHub Actions
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

                    # مدیریت عکس
                    if "photo" in message:
                        file_id = message["photo"][-1]["file_id"]
                        image_data, mime_type = download_bale_file(file_id, is_image=True)
                        if not user_text: user_text = "این تصویر را تحلیل کن"

                    # مدیریت فایل‌های متنی
                    elif "document" in message:
                        file_id = message["document"]["file_id"]
                        f_name = message["document"].get("file_name", "").lower()
                        if f_name.endswith(('.txt', '.py', '.json', '.js', '.cpp', '.h', '.html', '.css', '.md')):
                            content, _ = download_bale_file(file_id, is_image=False)
                            if content:
                                user_text = f"محتوای فایل '{f_name}':\n\n{content}\n\nسوال کاربر: {user_text or 'تحلیل کن'}"

                    if user_text or image_data:
                        print(f"Processing message from {chat_id}...", flush=True)
                        reply = get_gemini_response(user_text, image_data, mime_type)
                        
                        send_url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage"
                        requests.post(send_url, json={"chat_id": chat_id, "text": reply}, timeout=20)
                            
        except Exception as e:
            print(f"!!! Loop Error: {e}", flush=True)
            time.sleep(5)
            
        time.sleep(1)

if __name__ == "__main__":
    bot_loop()
