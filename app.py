from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage
)
import google.generativeai as genai
import os
import threading

app = Flask(__name__)

# ======================================
# LINE
# ======================================

line_bot_api = LineBotApi(
    os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
)

handler = WebhookHandler(
    os.getenv("LINE_CHANNEL_SECRET")
)

# ======================================
# GEMINI
# ======================================

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODEL_PRO = "gemini-3.5-pro"
MODEL_FLASH = "gemini-3.5-flash"


# ======================================
# HOME
# ======================================

@app.route("/")
def home():
    return "GMT AI QA is running"


# ======================================
# WEBHOOK
# ======================================

@app.route("/callback", methods=["POST"])
def callback():

    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    handler.handle(body, signature)

    return "OK"


# ======================================
# MODEL SELECTOR
# ======================================

def get_model(user_text):

    if user_text.lower().startswith("pro:"):
        return (
            genai.GenerativeModel(MODEL_PRO),
            user_text[4:].strip(),
            512
        )

    return (
        genai.GenerativeModel(MODEL_FLASH),
        user_text.strip(),
        256
    )


# ======================================
# PROCESS TEXT
# ======================================

def process_text(user_id, user_text):

    try:

        lower_text = user_text.lower()

        # ==================================
        # 5 WHY
        # ==================================
        if lower_text.startswith("5why:"):

            query = f"""
สร้าง 5 Why Analysis ภาษาไทย

ปัญหา:
{user_text[5:].strip()}

กฎ:
- ห้ามเกริ่นนำ
- ห้ามอธิบายเพิ่มเติม
- ตอบเฉพาะรูปแบบด้านล่าง
- ตอบสั้น กระชับ

Format:

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

            model = genai.GenerativeModel(MODEL_FLASH)

            response = model.generate_content(
                query,
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 256
                }
            )

        # ==================================
        # CAR
        # ==================================
        elif lower_text.startswith("car:"):

            query = f"""
คุณคือ QA Manager

สร้าง Corrective Action Report (CAR)

หัวข้อ:
{user_text[4:].strip()}

Format:

Problem Description:
Containment Action:
Root Cause:
Corrective Action:
Preventive Action:
Verification Method:
Responsible Person:
Target Date:
"""

            model = genai.GenerativeModel(MODEL_FLASH)

            response = model.generate_content(
                query,
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 512
                }
            )

        # ==================================
        # CLAIM
        # ==================================
        elif lower_text.startswith("claim:"):

            query = f"""
คุณคือ Supplier Quality Engineer

เขียน Supplier Claim ภาษาอังกฤษ

ข้อมูล:
{user_text[6:].strip()}

Format:

Subject:

Part Number:
Model:
Vendor:
Qty:

Problem:

Request:
Please investigate the root cause and provide corrective action.

Best Regards
GMT Quality Center
"""

            model = genai.GenerativeModel(MODEL_FLASH)

            response = model.generate_content(
                query,
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 512
                }
            )

        # ==================================
        # TRANSLATE
        # ==================================
        elif lower_text.startswith("translate:"):

            query = f"""
Translate the following text into professional QA/QC English.

Text:

{user_text[10:].strip()}
"""

            model = genai.GenerativeModel(MODEL_FLASH)

            response = model.generate_content(
                query,
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 256
                }
            )

        # ==================================
        # NORMAL QA
        # ==================================
        else:

            model, query_text, max_tokens = get_model(user_text)

            query = f"""
คุณคือ GMT Quality Center AI Assistant

บทบาท:
- Senior QA Engineer
- Supplier Quality Engineer
- Incoming Quality Control
- In Process Quality Control
- Final Quality Inspection
- Customer Complaint Specialist

ความเชี่ยวชาญ:
- Defect Analysis
- Root Cause Analysis
- 5 Why
- Fishbone Analysis
- Corrective Action
- Preventive Action
- Supplier Claim
- CAR
- 8D Report
- Quality Report Writing
- Manufacturing Process Improvement

กฎการตอบ:

1. ตอบเป็นภาษาไทย
2. ใช้ศัพท์ QA/QC และโรงงาน
3. ไม่ตอบแบบ Chatbot ทั่วไป
4. ตอบแบบ QA Engineer มืออาชีพ
5. ตอบแบบเป็นหัวข้อ

Format:

Defect Description:

Possible Cause:
- Cause 1
- Cause 2
- Cause 3

Risk Assessment:

Containment Action:

Corrective Action:

Preventive Action:

คำถาม:

{query_text}
"""

            response = model.generate_content(
                query,
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": max_tokens
                }
            )

        try:
            answer = response.text[:3500]
        except Exception:
            answer = "ไม่สามารถสร้างคำตอบได้"

        print("QUESTION:", user_text)
        print("ANSWER:", answer[:300])

        line_bot_api.push_message(
            user_id,
            TextSendMessage(text=answer)
        )

    except Exception as e:

        print("Gemini Error:", e)

        line_bot_api.push_message(
            user_id,
            TextSendMessage(
                text="ระบบประมวลผลขัดข้อง กรุณาลองใหม่อีกครั้ง"
            )
        )


# ======================================
# LINE TEXT EVENT
# ======================================

@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):

    user_id = event.source.user_id
    user_text = event.message.text

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=
"""🤖 GMT AI QA Assistant

กำลังวิเคราะห์ข้อมูล...

คำสั่งที่รองรับ

5why: ปัญหา
car: ปัญหา
claim: รายละเอียดเคลม
translate: ข้อความ

กรุณารอสักครู่..."""
        )
    )

    threading.Thread(
        target=process_text,
        args=(user_id, user_text)
    ).start()


# ======================================
# START
# ======================================

if __name__ == "__main__":
    app.run()
