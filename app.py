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
    return "GMT AI QA V3"


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
ตอบเฉพาะตามรูปแบบด้านล่าง

Problem:
Why1:
Why2:
Why3:
Why4:
Why5:
RootCause:
CorrectiveAction:
PreventiveAction:

ปัญหา:
{user_text[5:].strip()}

ข้อกำหนด
- ห้ามเกริ่นนำ
- ห้ามเขียนบทสรุป
- ห้ามใช้คำว่า
  ยินดีต้อนรับ
  สวัสดี
  ในฐานะ
  ขอเสนอ
  รายงาน
- ตอบสั้น กระชับ
"""

            model = genai.GenerativeModel(MODEL_FLASH)

            response = model.generate_content(
                query,
                generation_config={
                    "temperature": 0.0,
                    "max_output_tokens": 180
                }
            )

        # ==================================
        # CAR
        # ==================================
        elif lower_text.startswith("car:"):

            query = f"""
สร้าง Corrective Action Report (CAR)

ปัญหา:
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
                    "temperature": 0.1,
                    "max_output_tokens": 300
                }
            )

        # ==================================
        # CLAIM
        # ==================================
        elif lower_text.startswith("claim:"):

            query = f"""
Write Supplier Claim Email

Information:
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
                    "temperature": 0.1,
                    "max_output_tokens": 300
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
                    "temperature": 0.1,
                    "max_output_tokens": 200
                }
            )

        # ==================================
        # NORMAL QA
        # ==================================
        else:

            model, query_text, max_tokens = get_model(user_text)

            query = f"""
คุณคือ GMT Quality Center QA Analysis Engine

หน้าที่:
- Defect Analysis
- Root Cause Analysis
- Supplier Quality
- Process Quality
- Corrective Action
- Preventive Action

ข้อกำหนด:
- ห้ามทักทาย
- ห้ามแนะนำตัว
- ห้ามใช้คำว่า ยินดีต้อนรับ
- ห้ามใช้คำว่า สวัสดี
- ห้ามใช้คำว่า ผมคือ
- ห้ามใช้คำว่า ฉันคือ
- ห้ามใช้คำว่า ผู้ช่วย
- ห้ามใช้คำว่า AI Assistant
- ห้ามใช้คำว่า ในฐานะ
- ห้ามใช้คำว่า ขอเสนอ
- ห้ามใช้คำว่า เรียนทีมงาน

ตอบเป็นภาษาไทยเท่านั้น

Format:

Defect Description:

Possible Cause:
1.
2.
3.

Risk Assessment:

Containment Action:

Corrective Action:

Preventive Action:

ข้อมูล:
{query_text}
"""

            response = model.generate_content(
                query,
                generation_config={
                    "temperature": 0.1,
                    "max_output_tokens": max_tokens
                }
            )

        try:

            answer = response.text[:1200]

            bad_words = [
                "ยินดีต้อนรับครับ",
                "ยินดีต้อนรับ",
                "สวัสดีครับ",
                "สวัสดี",
                "ผมคือ",
                "ฉันคือ",
                "ผู้ช่วย",
                "AI Assistant",
                "ในฐานะ",
                "ขอเสนอ",
                "เรียนทีมงาน"
            ]

            for word in bad_words:
                answer = answer.replace(word, "")

        except Exception:

            answer = "ไม่สามารถสร้างคำตอบได้"

        print("=" * 40)
        print("QUESTION:", user_text)
        print("ANSWER:")
        print(answer)
        print("=" * 40)

        chunks = [
            answer[i:i + 1000]
            for i in range(0, len(answer), 1000)
        ]

        for chunk in chunks:

            line_bot_api.push_message(
                user_id,
                TextSendMessage(text=chunk)
            )

    except Exception as e:

        print("Gemini Error:", e)

        line_bot_api.push_message(
            user_id,
            TextSendMessage(
                text=f"ERROR: {str(e)}"
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

ตัวอย่างคำสั่ง:

5why: Burr on side top panel

car: Paint bulge

claim: Vendor CRESTEC Qty 3 pcs Burr

translate: พบรอยบุบบริเวณด้านข้าง Top Panel

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
