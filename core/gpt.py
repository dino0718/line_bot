from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from core.config import Config

# 初始化 GPT-4 LLM
llm = ChatOpenAI(
    model_name="gpt-4",
    openai_api_key=Config.OPENAI_API_KEY,
    temperature=0.7  # 調整溫度以改變回應的創意程度
)

def chat_with_gpt(user_input):
    """
    使用 LangChain 的 GPT-4 模型進行對話
    """
    try:
        response = llm([
            SystemMessage(content="你是Lume（路梅），一個溫暖和專業的心理陪伴者，請以朋友的語氣回答問題並且使用人類會用的用詞、關心來回復。"),
            HumanMessage(content=user_input)
        ])
        return response.content.strip()
    except Exception as e:
        print(f"GPT-4 API 錯誤：{e}")
        return "抱歉，我目前無法回應，請稍後再試 🙏"
