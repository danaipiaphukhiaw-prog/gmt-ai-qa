from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
import google.generativeai as genai
import os
import threading

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def get_model(user_text):
    if user_text.lower().startswith("pro:"):
        return genai.GenerativeModel("gemini-3.5-pro"), user_text[4:].strip(), 512
    else:
        return genai.GenerativeModel("gemini-3.5-flash"), user_text.strip(), 256


@app.route("/")
def home():
    return "GMT AI QA is running"


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    handler.handle(body, signature)
    return "OK", 200


def process_text(user_id, user_text):
    try:
        lower_text = user_text.lower()

        if lower_text.startswith("5why:"):
            query = f"""
คุณคือ Senior QA Engineer

ทำ 5 Why Analysis ให้เป็นภาษาไทย

ปัญหา:
{user_text[5:].strip()}

รูปแบบ:
Problem:
Why 1:
Why 2:
Why 3:
Why 4:
Why 5:
Root Cause:
Containment Action:
Corrective Action:
Preventive Action:
"""
            model = genai.GenerativeModel("gemini-3.5-flash")
            response = model.generate_content(query)

        elif lower_text.startswith("car:"):
            query = f"""
คุณคือ QA Manager

ช่วยเขียน Corrective Action Report (CAR)

หัวข้อ:
{user_text[4:].strip()}

รูปแบบ:
Problem Description
Containment Action
Root Cause
Corrective Action
Preventive Action
Verification Method
Responsible Person
Target Date
"""
            model = genai.GenerativeModel("gemini-3.5-flash")
            response = model.generate_content(query)

        elif lower_text.startswith("claim:"):
            query = f"""
คุณคือ Supplier Quality Engineer

ช่วยเขียน Supplier Claim ภาษาอังกฤษ

ข้อมูล:
{user_text[6:].strip()}

รูปแบบ:
Subject:
Part Number:
Model:
Qty:
Problem:
Request:
Please investigate the root cause and provide corrective action.

Best Regards
GMT Quality Center
"""
            model = genai.GenerativeModel("gemini-3.5-flash")
            response = model.generate_content(query)

        else:
            model, query_text, max_tokens = get_model(user_text)

            query = f"""
คุณคือ GMT QA/QC Engineer Assistant

ความเชี่ยวชาญ:
- Incoming Inspection
- In Process Quality Control
- Final Inspection
- Supplier Quality Management
- Root Cause Analysis
- Defect Analysis
- 5 Why
- CAR
- Corrective Action
- Preventive Action

ตอบเป็นภาษาไทย
ใช้ศัพท์ QA/QC โรงงาน

รูปแบบ:
Defect:
Possible Cause:
Containment Action:
Corrective Action:
Preventive Action:

คำถาม:
{query_text}
"""

            response = model.generate_content(
                query,
                generation_config={"max_output_tokens": max_tokens}
            )

        answer = response.text if response.text else "ไม่สามารถสร้างคำตอบได้"

        line_bot_api.push_message(
            user_id,
            TextSendMessage(text=answer)
        )

    except Exception as e:
        print("Gemini error:", e)
        line_bot_api.push_message(
            user_id,
            TextSendMessage(text="เกิดข้อผิดพลาดในการประมวลผล")
        )


@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    user_id = event.source.user_id
    user_text = event.message.text

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="โอเคครับ รอสักครู่...")
    )

    threading.Thread(
        target=process_text,
        args=(user_id, user_text)
    ).start()


if __name__ == "__main__":
    app.run()
