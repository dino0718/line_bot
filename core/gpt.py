from core.database import get_user_profile, fetch_chat_history
from datetime import datetime
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from core.config import Config
from transformers import pipeline

# 初始化情緒分析模型
sentiment_analyzer = pipeline("sentiment-analysis")

# 初始化 GPT-4
llm = ChatOpenAI(
    model_name="gpt-4",
    temperature=0.7,
    openai_api_key=Config.OPENAI_API_KEY
)

# LangChain 記憶對話
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

# 設定 Prompt
template = """你是 Lume（路梅），一個溫暖的心理陪伴者。

{chat_history}

用戶: {user_input}
Lume:"""
prompt = PromptTemplate(
    input_variables=["chat_history", "user_input"],
    template=template
)

# 建立 LangChain Chain
conversation = LLMChain(
    llm=llm,
    prompt=prompt,
    memory=memory
)

def chat_with_gpt(user_id, user_input):
    """
    透過 LangChain 記憶對話，讓 GPT-4 記住用戶過去的對話內容
    """
    # 取得聊天記錄
    chat_history = fetch_chat_history(user_id)

    # 取得用戶基本資料
    user_profile = get_user_profile(user_id)

    # **確保 `user_info` 變數存在**
    if user_profile:
        birth_date = user_profile.get("birth_date", None)
        if birth_date:
            # 假設 `birth_date` 是 `datetime.date` 類型，直接使用 `.year`
            age = datetime.now().year - birth_date.year
            user_info = f"姓名: {user_profile.get('name', '未知')}, 年齡: {age}, 興趣: {user_profile.get('interests', '未填寫')}, 心情: {user_profile.get('mood', '未填寫')}"
        else:
            user_info = f"姓名: {user_profile.get('name', '未知')}, 興趣: {user_profile.get('interests', '未填寫')}, 心情: {user_profile.get('mood', '未填寫')}"
    else:
        user_info = "尚未提供個人資料"

    # **確保 `chat_history` 至少有空字串，避免 LangChain 拋錯**
    if not chat_history:
        chat_history = "（沒有聊天記錄）"

    # **合併用戶資訊和輸入作為單一變數**
    combined_input = f"【用戶資訊】{user_info}\n\n【用戶問題】{user_input}"

    # 呼叫 GPT-4
    response = conversation.invoke({"user_input": combined_input})

    return response["text"].strip()

def analyze_emotion(message):
    """
    分析消息的情緒
    """
    try:
        result = sentiment_analyzer(message)[0]
        label = result['label']  # 標籤：POSITIVE、NEGATIVE、NEUTRAL
        score = result['score']  # 置信分數
        if label == "POSITIVE":
            return "正面"
        elif label == "NEGATIVE":
            return "負面"
        else:
            return "中性"
    except Exception as e:
        print(f"情緒分析錯誤：{e}")
        return "未知"