from services.line import send_message
from core.database import check_user_consent, set_user_consent

def check_consent_and_respond(user_id, user_message):
    """
    檢查使用者是否已同意隱私政策，未同意則要求回覆「同意」
    """
    if not check_user_consent(user_id):  # 查詢 MySQL
        if user_message == "同意":
            set_user_consent(user_id)  # 記錄使用者已同意
            return "感謝你的同意！你現在可以與我聊天了 😊"
        else:
            send_privacy_message(user_id)
            return "請先回覆【同意】，才能開始使用本服務。"
    return None

def send_privacy_message(user_id):
    """ 發送隱私條款 """
    privacy_text = (
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
        "❓ 若有任何疑問，隨時聯繫我們，我們很樂意協助您！\n"
    )
    send_message(user_id, privacy_text)
