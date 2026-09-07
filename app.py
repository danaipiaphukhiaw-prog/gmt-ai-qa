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

# ใช้ gemini-pro (รุ่นที่ Render รองรับ ไม่ต้องแก้ runtime)
model = genai.GenerativeModel("gemini-pro")

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
        response = model.generate_content(prompt)
        reply_text = response.text if response.text else "ไม่สามารถประมวลผลคำตอบได้ในขณะนี้"
    except Exception as e:
        print("Gemini error:", e)
        reply_text = "เกิดข้อผิดพลาดในการประมวลผล กรุณาลองใหม่อีกครั้ง"

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
