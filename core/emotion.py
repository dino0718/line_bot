from transformers import pipeline

# 使用中文情緒分析模型
sentiment_analyzer = pipeline(
    "sentiment-analysis",
    model="uer/roberta-base-finetuned-jd-binary-chinese"
)

def analyze_emotion(message):
    """
    分析消息的情緒
    """
    try:
        result = sentiment_analyzer(message)[0]
        label = result['label']  # 標籤：POSITIVE、NEGATIVE
        if label == "POSITIVE":
            return "正面"
        elif label == "NEGATIVE":
            return "負面"
        else:
            return "中性"
    except Exception as e:
        print(f"情緒分析錯誤：{e}")
        return "未知"
