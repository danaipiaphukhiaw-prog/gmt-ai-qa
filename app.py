from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import google.generativeai as genai
import os

app = Flask(__name__)

# LINE setup
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# Gemini setup
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-3.5-flash")

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print("Error:", e)
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_text = event.message.text

    # ตอบทันทีว่า "กำลังประมวลผล..."
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="กำลังประมวลผล...")
    )

    try:
        # เรียก Gemini (จำกัด output ไม่ให้ยาวเกินไป)
        response = model.generate_content(
            user_text,
            generation_config={"max_output_tokens": 512}
        )

        answer = response.text if response.text else "ไม่สามารถสร้างคำตอบได้"

        # ส่งผลลัพธ์จริงกลับไปด้วย push_message
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

