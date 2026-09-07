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

# ฟังก์ชันเลือกโมเดลตามโหมด
def get_model(user_text):
    if user_text.lower().startswith("pro:"):
        return genai.GenerativeModel("gemini-3.5-pro"), user_text[4:].strip(), 512
    else:
        return genai.GenerativeModel("gemini-3.5-flash"), user_text.strip(), 256

# ฟังก์ชันประมวลผลข้อความ
def process_text(user_id, user_text):
    try:
        model, query, max_tokens = get_model(user_text)
        response = model.generate_content(
            query,
            generation_config={"max_output_tokens": max_tokens}
        )
        answer = response.text if response.text else "ไม่สามารถสร้างคำตอบได้"
        line_bot_api.push_message(user_id, TextSendMessage(text=answer))
    except Exception as e:
        print("Gemini error:", e)
        line_bot_api.push_message(user_id, TextSendMessage(text="เกิดข้อผิดพลาดในการประมวลผล"))

# ฟังก์ชันประมวลผลรูปภาพ
def process_image(user_id, message_id, mode="flash"):
    try:
        message_content = line_bot_api.get_message_content(message_id)
        with open("temp.jpg", "wb") as f:
            for chunk in message_content.iter_content():
                f.write(chunk)

        # เลือกโมเดลตามโหมด
        if mode == "pro":
            model = genai.GenerativeModel("gemini-3.5-pro")
            max_tokens = 512
        else:
            model = genai.GenerativeModel("gemini-3.5-flash")
            max_tokens = 256

        with open("temp.jpg", "rb") as img_file:
            response = model.generate_content(
                [{"image": img_file}],
                generation_config={"max_output_tokens": max_tokens}
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

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="โอเคครับ รอสักครู่...")
    )

    threading.Thread(target=process_text, args=(user_id, user_text)).start()

# ✅ Handler สำหรับรูปภาพ
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    user_id = event.source.user_id

    # ถ้าอยากใช้ pro mode → ส่งรูปพร้อมข้อความว่า "pro"
    mode = "pro" if "pro" in event.message.contentProvider.type.lower() else "flash"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"โอเคครับ กำลังวิเคราะห์รูป ({mode})...")
    )

    threading.Thread(target=process_image, args=(user_id, event.message.id, mode)).start()

