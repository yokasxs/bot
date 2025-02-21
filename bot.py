import os
import json
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ambil konfigurasi dari .env
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
VERIFICATION_TOKEN = os.getenv("VERIFICATION_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

def get_tenant_access_token():
    """Mendapatkan tenant_access_token dari Lark"""
    url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal/"
    payload = {"app_id": APP_ID, "app_secret": APP_SECRET}

    response = requests.post(url, json=payload).json()
    return response.get("tenant_access_token")

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("📩 Received event:", json.dumps(data, indent=2))

    # Cek apakah ini challenge dari Lark
    if "challenge" in data:
        return jsonify({"challenge": data["challenge"]})

    # Cek apakah ini pesan dari pengguna
    if data.get("event", {}).get("type") == "im.message.receive_v1":
        chat_id = data["event"]["message"]["chat_id"]
        message_content = json.loads(data["event"]["message"]["content"])
        message_text = message_content.get("text", "")

        print(f"📨 User message: {message_text}")

        # Kirim pertanyaan ke OpenAI
        ai_response = get_openai_response(message_text)

        # Kirim pesan balik ke Lark
        send_message(chat_id, ai_response)

    return jsonify({"msg": "ok"})

def get_openai_response(user_input):
    """Mengambil respons dari OpenAI API"""
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": user_input}],
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response.json()["choices"][0]["message"]["content"]

def send_message(chat_id, text):
    """Mengirim pesan ke Lark"""
    token = get_tenant_access_token()
    url = "https://open.larksuite.com/open-apis/message/v4/send/"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"chat_id": chat_id, "msg_type": "text", "content": json.dumps({"text": text})}

    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
