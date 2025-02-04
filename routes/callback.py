from fastapi import APIRouter, Request, HTTPException
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, FollowEvent
from services.line import handler, reply_message, send_message
from core.database import create_user_db, save_message, get_user_profile, set_user_profile
from core.consent import check_consent_and_respond
from core.gpt import chat_with_gpt
import re
from core.database import save_message_with_emotion  # 引入新的存儲函數

router = APIRouter()

# 記錄用戶資料填寫進度
user_profile_step = {}

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
    當用戶加入好友時，建立專屬資料表，並發送隱私政策
    """
    user_id = event.source.user_id

    # 建立用戶專屬資料表
    create_user_db(user_id)

    # 發送歡迎訊息
    welcome_text = (
        "🌸  歡迎使用 Lume（路梅）  🌸\n\n"
        "Lume 是您的貼心陪伴者，隨時為您提供支持與建議。\n\n"
        
        "😊  Lume 能為您做什麼？ \n"
        " - 傾聽您的心情，提供溫暖的聊天陪伴。\n"
        " - 讓您透過簡單的心理測驗，更了解自己的情緒狀態。\n"
        " - 提供實用的心理健康知識與貼心建議，陪伴您度過每一天。\n\n"
        
        "📢  隱私政策  📢\n\n"
        "1️⃣  我們收集哪些資料？ \n"
        " - Line User ID：用於辨識使用者並提供個人化服務。\n"
        " - 對話內容：您傳送的文字、貼圖、語音可能被記錄以分析需求並回應。\n"
        " - 心理測驗結果：若使用心理測驗功能，系統可能記錄結果以便於優化服務。\n\n"
        
        "✅  請輸入「同意」以繼續使用 Lume 的服務。 \n"
        "❓ 若有任何疑問，隨時聯繫我們，我們很樂意協助您！\n"
    )
    send_message(user_id, welcome_text)

from core.database import create_user_db, save_message, get_user_profile, set_user_profile
import re

# 用戶資料收集步驟
user_profile_step = {}

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """
    處理用戶的文字訊息，並檢查基本資料是否完整
    """
    user_id = event.source.user_id
    user_message = event.message.text.strip()

    # 確保用戶資料表已存在
    create_user_db(user_id)

    # 檢查用戶基本資料
    user_profile = get_user_profile(user_id)

    if not user_profile or not user_profile.get("name") or not user_profile.get("birth_date") or not user_profile.get("interests") or not user_profile.get("mood"):
        if user_id not in user_profile_step:
            user_profile_step[user_id] = 1
            reply_message(event.reply_token, "歡迎回來！為了讓我更認識你，請告訴我你的名字 😊")
            return

        # 填寫名字
        if user_profile_step[user_id] == 1:
            set_user_profile(user_id, name=user_message)
            user_profile_step[user_id] = 2
            reply_message(event.reply_token, "請輸入你的出生年月日（格式：YYYY-MM-DD）")
            return

        # 填寫出生年月日
        if user_profile_step[user_id] == 2:
            if re.match(r'^\d{4}-\d{2}-\d{2}$', user_message):
                set_user_profile(user_id, birth_date=user_message)
                user_profile_step[user_id] = 3
                reply_message(event.reply_token, "你有什麼興趣或喜歡的活動嗎？")
            else:
                reply_message(event.reply_token, "請輸入正確的出生年月日格式，例如：1999-05-20 🙏")
            return

        # 填寫興趣
        if user_profile_step[user_id] == 3:
            set_user_profile(user_id, interests=user_message)
            user_profile_step[user_id] = 4
            reply_message(event.reply_token, "最後，你現在的心情如何？😊")
            return

        # 填寫心情
        if user_profile_step[user_id] == 4:
            set_user_profile(user_id, mood=user_message)
            del user_profile_step[user_id]
            reply_message(event.reply_token, "感謝你告訴我這些資訊！現在我們可以開始聊天了 😊")
            return

    # 儲存用戶消息並記錄情緒
    save_message_with_emotion(user_id, "user", user_message)

    # GPT-4 回應
    gpt_response = chat_with_gpt(user_id, user_message)

    # 儲存 GPT 回應
    save_message_with_emotion(user_id, "bot", gpt_response)

    # 回應用戶
    reply_message(event.reply_token, gpt_response)