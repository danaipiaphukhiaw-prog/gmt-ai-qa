from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
import google.generativeai as genai
import os
import threading

app = Flask(__name__)

# LINE setup
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# Gemini setup
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-3.5-flash")

# ฟังก์ชันประมวลผลข้อความ
def process_text(user_id, user_text):
    try:
        response = model.generate_content(
            user_text,
            generation_config={"max_output_tokens": 256}  # ตอบสั้น → เร็วขึ้น
        )
        answer = response.text if response.text else "ไม่สามารถสร้างคำตอบได้"
        line_bot_api.push_message(user_id, TextSendMessage(text=answer))
    except Exception as e:
        print("Gemini error:", e)
        line_bot_api.push_message(user_id, TextSendMessage(text="เกิดข้อผิดพลาดในการประมวลผล"))

# ฟังก์ชันประมวลผลรูปภาพ
def process_image(user_id, message_id):
    try:
        # ดึง binary ของรูปจาก LINE
        message_content = line_bot_api.get_message_content(message_id)
        with open("temp.jpg", "wb") as f:
            for chunk in message_content.iter_content():
                f.write(chunk)

        # ส่งรูปเข้า Gemini
        with open("temp.jpg", "rb") as img_file:
            response = model.generate_content(
                [{"image": img_file}],
                generation_config={"max_output_tokens": 256}
            )

        answer = response.text if response.text else "ไม่สามารถวิเคราะห์ภาพได้"
        line_bot_api.push_message(user_id, TextSendMessage(text=answer))

    except Exception as e:
        print("Gemini error:", e)
        line_bot_api.push_message(user_id, TextSendMessage(text="เกิดข้อผิดพลาดในการวิเคราะห์ภาพ"))

# ✅ Handler สำหรับข้อความ
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    user_id = event.source.user_id
    user_text = event.message.text

    # ตอบทันที
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="โอเคครับ รอสักครู่...")
    )

    # ประมวลผลใน thread แยก
    threading.Thread(target=process_text, args=(user_id, user_text)).start()

# ✅ Handler สำหรับรูปภาพ
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    user_id = event.source.user_id

    # ตอบทันที
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="โอเคครับ กำลังวิเคราะห์รูป...")
    )

    # ประมวลผลใน thread แยก
    threading.Thread(target=process_image, args=(user_id, event.message.id)).start()

