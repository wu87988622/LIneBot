from flask import Flask, request, abort
import logging
import json
import lineJson
import os

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError

from linebot.models import TextMessage, MessageEvent, TextSendMessage, StickerSendMessage, ImageSendMessage, VideoSendMessage


app = Flask(__name__)

# Channel Access Token
line_bot_api = LineBotApi('wxTNX1jIXxlXW4bZqEkZ59PdPLrnhQCCo/qMj3EB62aJomjGqsB8rG8Bl6g4zc/YDrHnouTCGbZPINFM6oDyuE9WhnrXeB9Aqb76qiyYlaWcE/9vBXSjrbMA73XH72x+6QSGPPNlvVNcy2R4uZVzjQdB04t89/1O/w1cDnyilFU=')
# Channel Secret
handler = WebhookHandler('ff13f12d5bcfa432e5643dcc7a9685ca')


# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    logging.basicConfig(level=logging.INFO)
    #Json Post
    #j = json.loads(body, object_hook=lineJson.as_lineJson)
    #type(j)

    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = str(event.message.text)
    logging.info(message)
    if message == '貼圖':
        sendMsg = StickerSendMessage(package_id='1', sticker_id='15')
        line_bot_api.reply_message(event.reply_token, sendMsg)
    else:
        sendMsg = VideoSendMessage(original_content_url='https://media.giphy.com/media/kaq6GnxDlJaBq/giphy.mp4',
                                   preview_image_url='https://media.giphy.com/media/kaq6GnxDlJaBq/giphy.gif')
        line_bot_api.reply_message(event.reply_token, sendMsg)


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
