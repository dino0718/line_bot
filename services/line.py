from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage
from core.config import Config

line_bot_api = LineBotApi(Config.CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(Config.CHANNEL_SECRET)

def send_message(user_id, text):
    line_bot_api.push_message(user_id, TextSendMessage(text=text))

def reply_message(reply_token, text):
    line_bot_api.reply_message(reply_token, TextSendMessage(text=text))
