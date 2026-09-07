from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import google.generativeai as genai
import os

app = Flask(__name__)

# ==========================
# LINE
# ==========================

line_bot_api = LineBotApi(
    os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
)

handler = WebhookHandler(
    os.getenv("LINE_CHANNEL_SECRET")
)

# ==========================
# GEMINI
# ==========================

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODEL = "gemini-3.5-flash"

# ==========================
# HOME
# ==========================

@app.route("/")
def home():
    return "GMT AI QA V5"

# ==========================
# WEBHOOK
# ==========================

@app.route("/callback", methods=["POST"])
def callback():

    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    handler.handle(body, signature)

    return "OK"

# ==========================
# LINE EVENT
# ==========================

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    user_text = event.message.text
    lower_text = user_text.lower()

    # HELP

    if lower_text == "help":

        answer = """
🤖 GMT AI QA Assistant

คำสั่ง

5why: ปัญหา

car: ปัญหา

claim: รายละเอียดเคลม

translate: ข้อความ

ตัวอย่าง

5why: Burr on side top panel

car: Paint bulge

claim: Vendor CRESTEC Qty 3 pcs Burr

translate: พบรอยบุบบริเวณด้านข้าง Top Panel
"""

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=answer)
        )

        return

    # 5WHY

    if lower_text.startswith("5why:"):

        prompt = f"""
ตอบเฉพาะ Format นี้

Problem:
Why1:
Why2:
Why3:
Why4:
Why5:
RootCause:
CorrectiveAction:
PreventiveAction:

Problem:
{user_text[5:].strip()}
"""

    # CAR

    elif lower_text.startswith("car:"):

        prompt = f"""
สร้าง Corrective Action Report

Problem:
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

    # CLAIM

    elif lower_text.startswith("claim:"):

        prompt = f"""
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

    # TRANSLATE

    elif lower_text.startswith("translate:"):

        prompt = f"""
Translate the following text into professional QA/QC English.

Text:
{user_text[10:].strip()}
"""

    # QA ANALYSIS

    else:

        prompt = f"""
คุณคือ GMT Quality Center QA Analysis Engine

ห้ามทักทาย
ห้ามแนะนำตัว
ห้ามใช้คำว่า
- ยินดีต้อนรับ
- สวัสดี
- ผมคือ
- ผู้ช่วย
- AI Assistant

ตอบเป็นภาษาไทย

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
{user_text}
"""

    try:

        model = genai.GenerativeModel(MODEL)

        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.1,
                "max_output_tokens": 800
            }
        )

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

    except Exception as e:

        error_text = str(e)

        if "429" in error_text:

            answer = """
⚠️ AI QA ใช้งานถึงขีดจำกัดชั่วคราว

Gemini API เกินโควต้าฟรี

กรุณารอประมาณ 1 นาที
แล้วลองใหม่อีกครั้ง
"""

        else:

            answer = f"""
⚠️ เกิดข้อผิดพลาด

{error_text[:300]}
"""

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=answer)
    )

# ==========================
# START
# ==========================

if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 10000)
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
