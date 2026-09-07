from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import google.generativeai as genai
import os

app = Flask(__name__)

# อ่านค่า Environment Variables
channel_access_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
channel_secret = os.environ.get("LINE_CHANNEL_SECRET")
gemini_api_key = os.environ.get("GEMINI_API_KEY")

if not channel_access_token or not channel_secret or not gemini_api_key:
    raise ValueError("Missing environment variables")

# ตั้งค่า LINE และ Gemini
configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)
genai.configure(api_key=gemini_api_key)

# ใช้โมเดลใหม่ (ไม่ต้อง v1beta แล้ว)
model = genai.GenerativeModel("gemini-1.5-flash")
response = model.generate_content(prompt)


@app.route("/")
def home():
    return "LINE AI QA Bot is running"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    # Prompt สำหรับ QA Assistant
    prompt = f"""
คุณคือ QA Assistant
หน้าที่:
- วิเคราะห์ Defect
- Root Cause Analysis
- 5 Why
- Corrective Action
- Preventive Action
- Supplier Claim

ตอบเป็นภาษาไทย ใช้ศัพท์ QA/QC และโรงงาน

คำถาม:
{event.message.text}
"""

    try:
        # ใช้ API ใหม่ (ไม่มี v1beta แล้ว)
        response = model.generate_content(prompt)
        reply_text = response.text if hasattr(response, "text") else response.candidates[0].content.parts[0].text

    except Exception as e:
        reply_text = f"เกิดข้อผิดพลาด: {e}"

    # ส่งข้อความกลับไปที่ LINE
    try:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)]
                )
            )
    except Exception as e:
        print("LINE reply error:", e)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
