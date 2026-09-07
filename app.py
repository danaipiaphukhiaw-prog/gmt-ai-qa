from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
import google.generativeai as genai
import os
import requests

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

# ✅ กรณีข้อความ
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    user_id = event.source.user_id
    user_text = event.message.text

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="กำลังประมวลผล...")
    )

    try:
        response = model.generate_content(
            user_text,
            generation_config={"max_output_tokens": 512}
        )
        answer = response.text if response.text else "ไม่สามารถสร้างคำตอบได้"

        line_bot_api.push_message(user_id, TextSendMessage(text=answer))

    except Exception as e:
        print("Gemini error:", e)
        line_bot_api.push_message(user_id, TextSendMessage(text="เกิดข้อผิดพลาดในการประมวลผล"))

# ✅ กรณีรูปภาพ
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    user_id = event.source.user_id

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="กำลังประมวลผล...")
    )

    try:
        # ดึง binary ของรูปจาก LINE
        message_content = line_bot_api.get_message_content(event.message.id)
        with open("temp.jpg", "wb") as f:
            for chunk in message_content.iter_content():
                f.write(chunk)

        # ส่งรูปเข้า Gemini
        with open("temp.jpg", "rb") as img_file:
            response = model.generate_content(
                [{"image": img_file}],
                generation_config={"max_output_tokens": 512}
            )

        answer = response.text if response.text else "ไม่สามารถวิเคราะห์ภาพได้"
        line_bot_api.push_message(user_id, TextSendMessage(text=answer))

    except Exception as e:
        print("Gemini error:", e)
        line_bot_api.push_message(user_id, TextSendMessage(text="เกิดข้อผิดพลาดในการวิเคราะห์ภาพ"))
