from flask import Flask, request, abort
import logging
import json
import lineJson
import os

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError

from linebot.models import TextMessage, MessageEvent, TextSendMessage, StickerSendMessage, ImageSendMessage, VideoSendMessage

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from bs4 import BeautifulSoup


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
        imgUrl = get_google_image_with_chrome(message)
        sendMsg = ImageSendMessage(original_content_url=imgUrl, preview_image_url= imgUrl)
        line_bot_api.reply_message(event.reply_token, sendMsg)


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)


def get_google_image_with_chrome(text):
    url = 'https://www.google.com.tw/search?hl=zh-TW&tbm=isch&source=hp&biw=1918&bih=947&ei=mbsHW52SL8ae8QWYz4CgAg&q='+text+'&oq='+text+'&gs_l=img.3..0l3j0i10k1l2j0i30k1l5.766.3823.0.4106.6.6.0.0.0.0.98.350.6.6.0....0...1ac.1j4.64.img..0.6.349....0.WN5xu1do3tM'
    chrome_bin = os.environ.get('GOOGLE_CHROME_SHIM', None)
    chrome_options = Options()
    chrome_options.binary_location = chrome_bin
    driver = webdriver.Chrome(chrome_options=chrome_options)
    driver.get(url)
    html = driver.page_source
    driver.close()
    bfsoup = BeautifulSoup(html, 'lxml')
    img = bfsoup.find_all('img')[0]['src']
    return img