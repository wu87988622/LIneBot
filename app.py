from flask import Flask, request, abort
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
    logging.info(img)
    return img


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
    #if message.find('484') != -1:
    #    imgurl='https://lh6.googleusercontent.com/899QWPLNxIQvhW4Qkiyq_U6uM_qzDfdQubAZqMMh-Qmnt1htP4kSk-AHBhyZEBXw6Vo3HbEKRmVgaYTi9E2p=w1036-h949'
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
                                image_url='https://lh3.googleusercontent.com/JNeGjyE0WkOjxfjFMAVD8PXk2J_bIf4F-rixyZ73sa53CgkS-kReZ81IBeJVD54w3VfQu8DWvQa4SYlb2dBcwBJf6bF4JkVxijjbjux8ZivBJ9UMLdrDfIWsqQp37xiBtIGpORl9gdXUVEctK9P-GBYSG-Y-ElCh92i_0gn8duB3ya8ki0sQlqzx5eyn4o0vZOlyeYyjo8BoUp9ZRjOjMJQ1RdGh8765jjXGd3wBNO1ahlHjDdETAKSJOpWNQoUo9OQ_JjdePpbNyKhqL891bJzv9HeJ7wL7BiuP_dEOupKsm3CiFW-X783ryt3wQt2sI4bTYLRmys0sgWFgjp_s8-dBFGgeGNXyDeGc4Cbqd34WXn_j5udAePDSWHexc1Oc7CSB9k5TCqLoTM84tlhA4yRjtfsE-L-oqWcG2vU2W6LD-F0_rWF_AO7JF4PVisnQh1K7IxOYOdI0gjlyUXkRDhDQr3T3Noky85Hqe1DcyQVXd0LnfPvfhFW13eCNGsjHPXX4sn1siSH_JdDvJiMsxTA1ZgPEPch0vR75h8EllFUgSskY5Cjs93065zLWxwih=w1920-h917',
                                action=MessageTemplateAction(
                                    label='志鈞哥',
                                    text='我要幹到你口吐白沫'
                                )
                            ),
                            ImageCarouselColumn(
                                image_url='https://lh3.googleusercontent.com/5qaR5cpA1IfeJX3PizOYAz5yfVQtrYw4SAgE5WTDg7UYnwrAqZ7-8IAo2RJAZ3mlJPob3VgtfqLBBpQGsKi_03njhJse_X-w7YqKMv_H1-5KW3178X9JCLVE_npJUeYuTABPLXxcMvCZKTuu-1hFcZlj9BHhom2eS_mHx0llcykcS5URO8pvzKeP7loj9E9zYMhTZlRzj3JUSAPUXsUoTtHDakJf8BhOACapLzJQkITqXTBtmPV5V75PXOjZdou_XTrSBumGA8d0gw4L-yljs1O-bAuXry4YdwrIBjztmnReUzBtJbEUyeIcbXIAOF3DlwMD44nb1FCbd90evljhcO2vu0-NWK9RyaIT5pe6dXitbTNH_eVfQ2s73J538QqLCMFzm6eyLGG9KqP-IKAg4_Z0BK3z1r41Za83GX9Wsg-zWzhZNHsvQV_xhBWPHjOJdZvAwcWzrMtfZ8PtKPGetMEIKp4KGOkQM23iyNlc0dHXFMAFjUOkMlOFrPpcjKE8-t_qYea6-Jq70ZIh0eQCSo6QZfZMro8r941hTE5CJsNlm4Ie01tAoSjto9baDl7c=w1337-h855',
                                action=MessageTemplateAction(
                                    label='小妹錯了',
                                    text='我要幹到你口吐白沫'
                                )
                            ),
                            ImageCarouselColumn(
                                image_url='https://lh3.googleusercontent.com/s9gXgnRq4wBIuZuuna4qRGeJYeVSrMo5KENucRpHFmOXsoQzPMcKOoOwXwhSixhLsirXuWhpubcC2nvjJZn_dJhKbmkAUThovAvdv0ob-Da2X0jjwueC4m5X6BTfa60gGVYivOhBoWkdPbptX6k34us568uXW3X6U3LOnQ6CPnVkWSIe-wd-gm7cppnX2dWLyR7Gao2Bo-Q6lK8kVp9vbxlDdkHWnE-4EPPM1n7VdUTLLswNchHiBVbymBt3D-s6RkF-_bzC8WiLyQZV-RXwjzxQ4Hkc_rf36NGYsFpFWV9LxNNWOhGn3NRcOwaesp5BAunDnUbcX1eReoMP3syX2DimhioZr08JWhP1MGx6J2OJiQ8joOip4xqpZgEp0qb1MXvdZDIrFJf0OWu4ZKYE40VYAuZf_Ubg7NBOkIv9g4poDR5ShrdUWUDwgz0jSPb7Ln6UWtJzYsyH5yZP5oWScYzhxHBy1rWXXO0FWyx0s_1vXURHyU3KTkiFqM0XeGp5sEtGrgpeJuwCR0RGrTk3NeZYlQwhsOpPJ6lAf51AUwN4rFe171HEVS8b6V6Dhln-=w1337-h855',
                                action=MessageTemplateAction(
                                    label='只好露出',
                                    text='我要幹到你口吐白沫'
                                )
                            ),
                            ImageCarouselColumn(
                                image_url='https://lh3.googleusercontent.com/glFSI4c-N9NmAaBejdv3diJucS88goyOpot-tlZ1Kzug0pE8deJGVPqKFNvbj11OuiQVoCkyllNIx6QwSQMDABZtx-F2DFJiTlamQ409c5ra4DUzVOnlAB9feXtKm1QAw4hDBBZuEa9ogkoMkJEnWcPJzDOtza7ECkilOBoue3D0T5Zn-EmVjC6Efa64UYz_ZymYeJhraMcZ6asAQw2Cj530iLtbR54HDyTDp9VH0L9tGxnl4RtjUq_9k6iQO9RfP-VcmlUZmeRzlsC7W23ojzvzDN727jFQX-A79_YA99epqJxe4KaTq6esav53xBhisEkjdRF8NQn2WwPS77reoNElTVNaUPpdjkeTS_CWos7vc6PBuLMki8vIEtFtH0PVlkh5b5jl8dnHSlbY896tF2XpZRL2vhTi1D2ZY6z04GqJqemYgbwbVM6hvbCFry8k-bivwGfF4mR9eOhiS2idpgRxn8LdlkXg62E9ERt3v1Sph9tFiyf1ciEU6dmJguO9SKlGBD7r_W012hg3JcCTOMrn-dF0mRoKbX9KVQETB3-BOp84w6LBPLwDTu9k9ahW=w1337-h855',
                                action=MessageTemplateAction(
                                    label='胸部',
                                    text='我要幹到你口吐白沫'
                                )
                            )
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

