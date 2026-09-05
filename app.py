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

# ตั้งค่า Configuration
configuration = Configuration(access_token=os.environ["LINE_CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["LINE_CHANNEL_SECRET"])
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

model = genai.GenerativeModel("gemini-1.5-flash")

@app.route("/")
def home():
    return "GMT AI QA is running"

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
คุณคือ GMT QA Assistant

หน้าที่:
- วิเคราะห์ Defect
- Root Cause Analysis
- 5 Why
- Corrective Action
- Preventive Action
- Supplier Claim

ตอบเป็นภาษาไทย
ใช้ศัพท์ QA/QC และโรงงาน

คำถาม:
{event.message.text}
"""

    try:
        response = model.generate_content(prompt)
        reply_text = response.text if response.text else "ไม่สามารถประมวลผลคำตอบได้ในขณะนี้"
    except Exception as e:
        reply_text = "เกิดข้อผิดพลาดในการประมวลผลระบบ QA กรุณาลองใหม่อีกครั้ง"

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
