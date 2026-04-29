import os
import time
import requests
import base64

# --- تنظیمات Secrets ---
GEMINI_KEY = os.getenv("GEMINI_KEY")
BALE_TOKEN = os.getenv("BALE_TOKEN")
PROXY_DOMAIN = "crimson-scene-23ee.a-z-cheryani.workers.dev"

def get_mime_type(file_name):
    """تشخیص هوشمند نوع فایل برای گوگل"""
    ext = file_name.split('.')[-1].lower()
    mapping = {
        'pdf': 'application/pdf',
        'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png',
        'mp4': 'video/mp4', 'mpeg': 'video/mpeg', 'mov': 'video/quicktime',
        'mp3': 'audio/mpeg', 'wav': 'audio/wav', 'ogg': 'audio/ogg',
        'txt': 'text/plain', 'py': 'text/x-python', 'md': 'text/markdown',
        'json': 'application/json', 'js': 'application/javascript'
    }
    return mapping.get(ext, 'application/octet-stream')

def download_bale_file(file_id):
    """دانلود فایل از بله و تبدیل مستقیم به بیس۶۴"""
    try:
        info_url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/getFile?file_id={file_id}"
        file_info = requests.get(info_url).json()
        if file_info.get("ok"):
            path = file_info["result"]["file_path"]
            down_url = f"https://tapi.bale.ai/file/bot{BALE_TOKEN}/{path}"
            content = requests.get(down_url).content
            return base64.b64encode(content).decode('utf-8')
    except Exception as e:
        print(f"!!! Download Error: {e}", flush=True)
    return None

def get_gemini_response(user_text, file_data=None, mime_type=None):
    """سوئیچ هوشمند بین تمامی مدل‌های جدید و پیش‌نمایش"""
    models_to_try = [
        "gemini-3-flash-preview", "gemini-3.0-pro", "gemini-3.0-flash",
        "gemini-2.5-pro-preview", "gemini-2.5-flash-preview", "gemini-2.5-pro",
        "gemini-2.5-flash", "gemini-2.0-flash-exp", "gemini-2.0-flash",
        "gemini-1.5-pro", "gemini-1.5-flash"
    ]
    
    for model_name in models_to_try:
        try:
            url = f"https://{PROXY_DOMAIN}/v1beta/models/{model_name}:generateContent?key={GEMINI_KEY}"
            parts = []
            if user_text: parts.append({"text": user_text})
            if file_data:
                parts.append({"inline_data": {"mime_type": mime_type, "data": file_data}})

            if not parts: return "پیام خالی است."

            payload = {"contents": [{"parts": parts}]}
            print(f"--- Trying model: {model_name} ---", flush=True)
            
            response = requests.post(url, json=payload, timeout=50)
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            print(f"!!! {model_name} failed: {response.status_code}")
        except Exception as e:
            print(f"!!! Error with {model_name}: {e}")
            continue
    return "متأسفانه هیچ‌کدام از مدل‌ها در حال حاضر پاسخگو نیستند."

def bot_loop():
    last_id = 0
    print("--- Ultra Multimodal Bot (2026 Edition) Started ---", flush=True)
    start_time = time.time()
    
    while time.time() - start_time < 21000:
        try:
            updates_url = f"https://tapi.bale.ai/bot{BALE_TOKEN}/getUpdates?offset={last_id + 1}&timeout=20"
            res = requests.get(updates_url, timeout=30).json()
            
            if res.get("ok") and res.get("result"):
                for update in res["result"]:
                    last_id = update["update_id"]
                    msg = update.get("message", {})
                    chat_id = msg.get("chat", {}).get("id")
                    if not chat_id: continue

                    text = msg.get("text") or msg.get("caption")
                    f_data, m_type = None, None

                    # مدیریت هوشمند انواع ورودی
                    if "photo" in msg:
                        f_data = download_bale_file(msg["photo"][-1]["file_id"])
                        m_type = "image/jpeg"
                    elif "document" in msg:
                        f_data = download_bale_file(msg["document"]["file_id"])
                        m_type = get_mime_type(msg["document"].get("file_name", ""))
                    elif "video" in msg:
                        f_data = download_bale_file(msg["video"]["file_id"])
                        m_type = "video/mp4"
                    elif "audio" in msg or "voice" in msg:
                        key = "audio" if "audio" in msg else "voice"
                        f_data = download_bale_file(msg[key]["file_id"])
                        m_type = "audio/mpeg" # یا audio/ogg بسته به فایل

                    if text or f_data:
                        print(f"Processing from {chat_id}...", flush=True)
                        reply = get_gemini_response(text, f_data, m_type)
                        requests.post(f"https://tapi.bale.ai/bot{BALE_TOKEN}/sendMessage", 
                                      json={"chat_id": chat_id, "text": reply}, timeout=20)
        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(5)
        time.sleep(1)

if __name__ == "__main__":
    bot_loop()
