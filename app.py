from flask import Flask, request, abort, render_template
import logging
import json
import lineJson
import os
from switch import switch

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError

from linebot.models import TextMessage, MessageEvent, TextSendMessage, StickerSendMessage, ImageSendMessage, VideoSendMessage, TemplateSendMessage, MessageTemplateAction, ImageCarouselTemplate, ImageCarouselColumn

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
    jsonStr = str(bfsoup.find_all('script')[3].text).replace('window._sharedData = ', '')[:-1]
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
    jsonStr = str(bfsoup.find_all('script')[3].text).replace('window._sharedData = ', '')[:-1]
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
    logging.info(img);
    return img


@app.route('/post', methods=['GET', 'POST'])
def post():
    logging.basicConfig(level=logging.INFO)
    body = request.form['post']
    app.logger.info(body)
    if request.methods == 'POST':
        line_bot_api.push_message('Ud272182402cd7a29ad48a1a68d924eee', TextSendMessage(text=body))
        return 'OK'
    elif request.methods == 'GET':
        return render_template('post.html')


@app.route("/ex", methods=['POST'])
def ex():
    logging.basicConfig(level=logging.INFO)
    body = request.get_data(as_text=True)
    app.logger.info(body)
    j = json.loads(body, object_hook=lineJson.as_lineJson)
    type(j)
    try:
        line_bot_api.push_message(j.lineID, TextSendMessage(text=j.text))
    except InvalidSignatureError:
        abort(400)
    return 'OK'


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


@handler.add(MessageEvent)
def handle_sticker_message(event):
    packageId = event.message.package_id
    reply = event.reply_token
    if packageId == '4587' or packageId == '1036951':
        sendMsg = TextSendMessage(text='雞掰醜兔子貼圖')
        line_bot_api.reply_message(reply, sendMsg)


line_bot_url = 'https://itrilinebot.herokuapp.com/static'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = str(event.message.text)
    logging.info(message)
    if message.find('ig:') != -1:
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
    if message.find('g:') != -1:
        gMsg = message[3:]
        imgUrl = get_google_image(gMsg)
        sendMsg = ImageSendMessage(original_content_url=imgUrl, preview_image_url=imgUrl)
        line_bot_api.reply_message(event.reply_token, sendMsg)
    if message.find('治軍') != -1:
        sendMsg = TextSendMessage(text='志鈞拉 幹')
        line_bot_api.reply_message(event.reply_token, sendMsg)
    #if message.find('在') != -1:
    #    sendMsg = TextSendMessage(text='再拉 幹')
    #    line_bot_api.reply_message(event.reply_token, sendMsg)
    #if message.find('幹') != -1:
    #    sendMsg = TextSendMessage(text='I\'m Groot')
    #    line_bot_api.reply_message(event.reply_token, sendMsg)
    # if message.find('484') != -1:
    #    imgurl = line_bot_url + '/484.jpg'
    #    sendMsg = ImageSendMessage(preview_image_url=imgurl, original_content_url=imgurl)
    #    line_bot_api.reply_message(event.reply_token, sendMsg)

    for case in switch(message):
        if case('貼圖'):
            sendMsg = StickerSendMessage(package_id='1', sticker_id='15')
            line_bot_api.reply_message(event.reply_token, sendMsg)
            break
        if case('打招呼'):
            sendMsg = TextSendMessage(text='志鈞哥，馬克哥 早安!!')
            line_bot_api.reply_message(event.reply_token, sendMsg)
            break
        if case('ㄤ'):
            sendMsg = TextSendMessage(text='ㄤㄤ泥豪')
            line_bot_api.reply_message(event.reply_token, sendMsg)
            break
        if case('叫大哥'):
            sendMsg = TextSendMessage(text='大哥好')
            line_bot_api.reply_message(event.reply_token, sendMsg)
            break
        if case('這是什麼'):
            sendMsg = TextSendMessage(text='港幣！')
            line_bot_api.reply_message(event.reply_token, sendMsg)
            break
        if case('我知道'):
            sendMsg = TextSendMessage(text='知道還問')
            line_bot_api.reply_message(event.reply_token, sendMsg)
            break
        if case('我沒有資格問嗎'):
            sendMsg = TextSendMessage(text='有資格！有資格！有資格！')
            line_bot_api.reply_message(event.reply_token, sendMsg)
            break
        if case('getid'):
            if event.source.type == 'user':
                sendMsg = TextSendMessage(text=event.source.user_id)
            elif event.source.type == 'group':
                sendMsg = TextSendMessage(text=event.source.group_id)
            elif event.source.type == 'room':
                sendMsg = TextSendMessage(text=event.source.room_id)
            line_bot_api.reply_message(event.reply_token, sendMsg)
            break
        if case('道歉'):
            if event.source.user_id == 'U96e561374b413379c8fddc22ed185e9e':
                sendMsg = TextSendMessage(text='歷史不是捏造就能改變')
            if event.source.user_id == 'Ud272182402cd7a29ad48a1a68d924eee':
                sendMsg = TextSendMessage(text='Q哥 你頭髮世界直 抱歉')
            if event.source.user_id == 'U0677c83831ba745c15b5bd68e79f7d12':
                sendMsg = TextSendMessage(text='哲哥 抱歉 你水冷最猛')
            if event.source.user_id == 'Ua6e5cc1dc6fbeaca3f6db3f220c2782a':
                sendMsg = TemplateSendMessage(
                    alt_text='Image Carousel template',
                    template=ImageCarouselTemplate(
                        columns=[
                            ImageCarouselColumn(
                                image_url=line_bot_url + '/newsorry.jpg',
                                action=MessageTemplateAction(
                                    label='志鈞哥',
                                    text='我要幹到你口吐白沫'
                                )
                            ),
                            ImageCarouselColumn(
                                image_url=line_bot_url + '/newsorry2.jpg',
                                action=MessageTemplateAction(
                                    label='小妹錯了',
                                    text='我要幹到你口吐白沫'
                                )
                            ),
                            ImageCarouselColumn(
                                image_url=line_bot_url + '/newsorry3.jpg',
                                action=MessageTemplateAction(
                                    label='只好露出',
                                    text='我要幹到你口吐白沫'
                                )
                            ),
                            ImageCarouselColumn(
                                image_url=line_bot_url + '/newsorry4.jpg',
                                action=MessageTemplateAction(
                                    label='胸部',
                                    text='我要幹到你口吐白沫'
                                )
                            ),
                            ImageCarouselColumn(
                                image_url=line_bot_url + '/newsorry5.jpg',
                                action=MessageTemplateAction(
                                    label='胸部',
                                    text='我要幹到你口吐白沫'
                                )
                            ),
                            ImageCarouselColumn(
                                image_url=line_bot_url + '/newsorry6.jpg',
                                action=MessageTemplateAction(
                                    label='胸部',
                                    text='我要幹到你口吐白沫'
                                )
                            ),
                            ImageCarouselColumn(
                                image_url=line_bot_url + '/newsorry7.jpg',
                                action=MessageTemplateAction(
                                    label='胸部',
                                    text='我要幹到你口吐白沫'
                                )
                            ),
                            ImageCarouselColumn(
                                image_url=line_bot_url + '/newsorry8.jpg',
                                action=MessageTemplateAction(
                                    label='胸部',
                                    text='我要幹到你口吐白沫'
                                )
                            ),
                            ImageCarouselColumn(
                                image_url=line_bot_url + '/newsorry9.jpg',
                                action=MessageTemplateAction(
                                    label='胸部',
                                    text='我要幹到你口吐白沫'
                                )
                            ),
                            ImageCarouselColumn(
                                image_url=line_bot_url + '/newsorry10.jpg',
                                action=MessageTemplateAction(
                                    label='胸部',
                                    text='我要幹到你口吐白沫'
                                )
                            ),
                        ]
                    )
                )

            if event.source.user_id == 'U47d7743cf2cae1d0c524c03cdca81775':
                sendMsg = TextSendMessage(text='抱歉 你也是大哥\n葉子媚是個賢妻良母，兩百塊最聰明，戈巴契夫頭髮最長，海珊總統最不愛打仗')
            line_bot_api.reply_message(event.reply_token, sendMsg)
            break
        if case('懺悔'):
            if event.source.user_id == 'U96e561374b413379c8fddc22ed185e9e':
                sendMsg = TextSendMessage(text='才會真正得到尊嚴')
            line_bot_api.reply_message(event.reply_token, sendMsg)
            break
        if case('認錯'):
            if event.source.user_id == 'U96e561374b413379c8fddc22ed185e9e':
                sendMsg = TextSendMessage(text='事實不是說謊就能帶過')
            line_bot_api.reply_message(event.reply_token, sendMsg)
            break
        if case('=='):
            sendMsg = TextSendMessage(text='你以為說==就沒事了嗎?')
            line_bot_api.reply_message(event.reply_token, sendMsg)
            break
        if case('0.0'):
            sendMsg = TextSendMessage(text='靠杯喔')
            line_bot_api.reply_message(event.reply_token, sendMsg)
            break
        if case('=_='):
            sendMsg = TextSendMessage(text='神經病')
            line_bot_api.reply_message(event.reply_token, sendMsg)
            break


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

