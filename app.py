from flask import Flask, request, abort
import logging
import json
import lineJson
import os

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError

from linebot.models import TextMessage, MessageEvent, TextSendMessage, StickerSendMessage, ImageSendMessage, VideoSendMessage

import requests

from bs4 import BeautifulSoup


app = Flask(__name__)

# Channel Access Token
line_bot_api = LineBotApi('wxTNX1jIXxlXW4bZqEkZ59PdPLrnhQCCo/qMj3EB62aJomjGqsB8rG8Bl6g4zc/YDrHnouTCGbZPINFM6oDyuE9WhnrXeB9Aqb76qiyYlaWcE/9vBXSjrbMA73XH72x+6QSGPPNlvVNcy2R4uZVzjQdB04t89/1O/w1cDnyilFU=')
# Channel Secret
handler = WebhookHandler('ff13f12d5bcfa432e5643dcc7a9685ca')

ig_headers = {
        'upgrade-insecure-requests': "1",
        'user-agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36",
        'accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        'accept-language': "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6,zh-CN;q=0.5",
        'cache-control': "no-cache"
}


def get_ig_user(text):
    url = 'https://www.instagram.com/'+text+'/'
    response = requests.request("GET", url, headers=ig_headers)
    html = response.text
    bfsoup = BeautifulSoup(html, 'lxml')
    jsonStr = str(bfsoup.find_all('script')[2].text).replace('window._sharedData = ', '')[:-1]
    jsons = json.loads(jsonStr)
    imgs = []
    entry_data = jsons['entry_data']
    profilePages = entry_data['ProfilePage']
    for profilePage in profilePages:
        graphql = profilePage['graphql']
        user = graphql['user']
        media = user['edge_owner_to_timeline_media']
        edges = media['edges']
        for edge in edges:
            node = edge['node']
            src = node['thumbnail_resources'][4]['src']
            if len(imgs) < 5:
                imgs.append(src)
    return imgs


def get_ig_image(url):
    url = url
    response = requests.request("GET", url, headers=ig_headers)
    html = response.text
    bfsoup = BeautifulSoup(html, 'lxml')
    jsonStr = str(bfsoup.find_all('script')[2].text).replace('window._sharedData = ', '')[:-1]
    # logging.info(jsonStr)
    jsons = json.loads(jsonStr)
    imgs = []
    mp4 = []
    entry_data = jsons['entry_data']
    for pg in entry_data['PostPage']:
        graphql = pg['graphql']
        shortcode_media = graphql['shortcode_media']
        child = shortcode_media['edge_sidecar_to_children']
        for edge in child['edges']:
            node = edge['node']
            if node['is_video'] is True:
                url = node['video_url']
                img = node['display_resources'][0]['src']
                mp4.append(url+','+img)
            else:
                src = node['display_resources'][2]['src']
                imgs.append(src)
    ig_map = {'img': imgs, 'mp4': mp4}
    return ig_map


def get_google_image(text):
    url = "https://www.google.com/search"

    querystring = {"q": text, "tbm": "isch"}

    headers = {
        'upgrade-insecure-requests': "1",
        'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36",
        'accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        'accept-language': "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6,zh-CN;q=0.5",
        'cache-control': "no-cache",
    }
    img = ''
    response = requests.request("GET", url, headers=headers, params=querystring)
    html = response.text
    bfsoup = BeautifulSoup(html, 'lxml')
    for imgs in bfsoup.find_all('img'):
        if imgs.has_attr('data-src'):
            img = imgs['data-src']
    logging.info(img)
    return img


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
    elif message.find('ig:') != -1:
        if message.find('http') != -1:
            url = message[3:]
            imgMap = get_ig_image(url)
            sendMsg = []
            imgUrls = imgMap['img']
            mp4s = imgMap['mp4']
            for imgUrl in imgUrls:
                logging.info(imgUrl)
                if len(sendMsg) < 5:
                    sendMsg.append(ImageSendMessage(original_content_url=imgUrl, preview_image_url=imgUrl))
            for mp4 in mp4s:
                logging.info(mp4)
                mp4Url = str(mp4).split(',')
                if len(sendMsg) < 5:
                    sendMsg.append(VideoSendMessage(original_content_url=mp4Url[0],
                                                    preview_image_url=mp4Url[1]))
            line_bot_api.reply_message(event.reply_token, sendMsg)
        else:
            text = message[3:]
            imgUrls = get_ig_user(text)
            sendMsg = []
            for imgUrl in imgUrls:
                logging.info(imgUrl)
                sendMsg.append(ImageSendMessage(original_content_url=imgUrl, preview_image_url=imgUrl))
            line_bot_api.reply_message(event.reply_token, sendMsg)
    elif message.find('g:') != -1:
        gMsg = message[3:]
        imgUrl = get_google_image(gMsg)
        sendMsg = ImageSendMessage(original_content_url=imgUrl, preview_image_url=imgUrl)
        line_bot_api.reply_message(event.reply_token, sendMsg)
    elif message == '打招呼':
        sendMsg = TextSendMessage(text='志鈞哥，馬克哥 早安!!')
        line_bot_api.reply_message(event.reply_token, sendMsg)
    elif message.find('治軍') != -1:
        sendMsg = TextSendMessage(text='志鈞拉 幹')
        line_bot_api.reply_message(event.reply_token, sendMsg)
    #elif message.find('在') != -1:
    #    sendMsg = TextSendMessage(text='再拉 幹')
    #    line_bot_api.reply_message(event.reply_token, sendMsg)
    elif message.find('幹') != -1:
        sendMsg = []
        sendMsg.append(TextSendMessage(text='我是格魯特'))
        imgUrl = 'https://drive.google.com/open?id=1ZU3SDRBqtfzV-TNyJqm8TTidDcPGFKpN'
        sendMsg.append(ImageSendMessage(original_content_url=imgUrl, preview_image_url=imgUrl))
        line_bot_api.reply_message(event.reply_token, sendMsg)
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

