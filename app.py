@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    # ตอบกลับทันทีด้วยข้อความ placeholder
    placeholder = "กำลังประมวลผล..."
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=placeholder)]
            )
        )

    # ประมวลผลด้วย Gemini แยกต่างหาก
    prompt = f"""
คุณคือ QA Assistant
หน้าที่:
- วิเคราะห์ Defect
- Root Cause Analysis
- 5 Why
- Corrective Action
- Preventive Action
- Supplier Claim

ตอบเป็นภาษาไทย ใช้ศัพท์ QA/QC และโรงงาน

คำถาม:
{event.message.text}
"""

    try:
        response = model.generate_content(prompt)
        if hasattr(response, "text") and response.text:
            reply_text = response.text
        elif response.candidates and response.candidates[0].content.parts:
            reply_text = response.candidates[0].content.parts[0].text
        else:
            reply_text = "ไม่สามารถประมวลผลคำตอบได้ในขณะนี้"
    except Exception as e:
        reply_text = f"เกิดข้อผิดพลาด: {e}"

    # ส่งผลลัพธ์จริงกลับไปด้วย push_message
    try:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.push_message(
                to=event.source.user_id,
                messages=[TextMessage(text=reply_text)]
            )
    except Exception as e:
        print("LINE push error:", e)
