from fastapi import APIRouter, Request, HTTPException
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, FollowEvent
from services.line import handler, reply_message, send_message
from core.database import create_user_db
from core.consent import check_consent_and_respond
from core.gpt import chat_with_gpt

router = APIRouter()

@router.post("/callback")
async def callback(request: Request):
    """
    Line Webhook 接收請求
    """
    signature = request.headers.get("X-Line-Signature")
    body = await request.body()

    try:
        handler.handle(body.decode(), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    return {"message": "OK"}

@handler.add(FollowEvent)
def handle_follow(event):
    """
    當用戶加入好友時，建立專屬資料表
    """
    user_id = event.source.user_id

    # 為該用戶建立專屬的 MySQL 資料表
    create_user_db(user_id)

    # 發送歡迎訊息
    welcome_text = (
        "🌸  歡迎使用 Lume（路梅）  🌸\n\n"
        "Lume 是您的貼心陪伴者，隨時為您提供支持與建議。\n\n"
        
        "😊  Lume 能為您做什麼？ \n"
        " - 傾聽您的心情，提供溫暖的聊天陪伴。\n"
        " - 讓您透過簡單的心理測驗，更了解自己的情緒狀態。\n"
        " - 提供實用的心理健康知識與貼心建議，陪伴您度過每一天。\n\n"
        
        "🔒  我們如何保護您的資料安全？ \n"
        " -  加密存儲 ：我們的系統會對您的資料進行加密處理，防止未授權的存取。\n"
        " -  最小化存取 ：我們僅收集提供服務所需的最少資訊。\n"
        " -  匿名分析 ：我們只會以匿名形式統計數據，用於優化服務，絕不洩露您的個人隱私。\n"
        " -  定期檢查 ：我們的系統會進行定期的安全性檢查，確保您的資料受到最嚴格的保護。\n\n"
        
        "📢  隱私政策  📢\n\n"
        "1️⃣  我們收集哪些資料？ \n"
        " - Line User ID：用於辨識使用者並提供個人化服務。\n"
        " - 對話內容：您傳送的文字、貼圖、語音可能被記錄以分析需求並回應。\n"
        " - 心理測驗結果：若使用心理測驗功能，系統可能記錄結果以便於優化服務。\n\n"
        
        "2️⃣  我們如何使用這些資料？ \n"
        " - 回覆您的聊天訊息，提供心理支持。\n"
        " - 優化服務，讓功能更加貼合您的需求（統計分析匿名數據）。\n"
        " - 安全防護：若偵測到高風險訊號，會提供緊急求助資訊。\n\n"
        
        "✅  請輸入「同意」以繼續使用 Lume 的服務。 \n"
        "✅  如若已經同意過，請忽略本訊息，即可開始使用。 \n"
        "❓ 若有任何疑問，隨時聯繫我們，我們很樂意協助您！\n"
    )
    send_message(user_id, welcome_text)

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """
    處理用戶的文字訊息
    """
    user_id = event.source.user_id
    user_message = event.message.text.strip()

    # 檢查是否已同意條款
    consent_reply = check_consent_and_respond(user_id, user_message)
    if consent_reply:
        reply_message(event.reply_token, consent_reply)
        return

    # GPT-4 回應
    gpt_response = chat_with_gpt(user_message)
    reply_message(event.reply_token, gpt_response)
