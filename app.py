from flask import Flask, request, abort
import logging
import json
import lineJson
import os

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError

from linebot.models import TextMessage


app = Flask(__name__)

# Channel Access Token
line_bot_api = LineBotApi('')
# Channel Secret
handler = WebhookHandler('')

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    # signature = request.headers['Content-Type: application/json']

    # get request body as text
    logging.basicConfig(level=logging.INFO)
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    j = json.loads(body, object_hook=lineJson.as_lineJson)
    type(j)
    # handle webhook body
    try:
        line_bot_api.push_message(j.lineID, TextMessage(text=j.text))
    except InvalidSignatureError:
        abort(400)

    return 'OK'

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
