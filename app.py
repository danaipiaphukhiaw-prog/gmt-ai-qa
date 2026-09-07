from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
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

def process_with_gemini(user_id, user_text):
    try:
        response = model.generate_content(
            user_text,
            generation_config={"max_output_tokens": 256}  # จำกัดให้ตอบสั้นลง → เร็วขึ้น
        )
        answer = response.text if response.text else "ไม่สามารถสร้างคำตอบได้"
        line_bot_api.push_message(user_id, TextSendMessage(text=answer))
    except Exception as e:
        print("Gemini error:", e)
        line_bot_api.push_message(user_id, TextSendMessage(text="เกิดข้อผิดพลาดในการประมวลผล"))

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_text = event.message.text

    # ตอบทันทีว่า "กำลังประมวลผล..."
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="โอเคครับ รอสักครู่...")
    )

    # ประมวลผลใน thread แยก → ไม่บล็อกการตอบทันที
    threading.Thread(target=process_with_gemini, args=(user_id, user_text)).start()
