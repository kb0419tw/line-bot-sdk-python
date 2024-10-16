# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

import os
import sys
import openai
from argparse import ArgumentParser
from flask import Flask, request, abort

from linebot.v3 import (
     WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)

from linebot.v3.messaging.models.image_message import ImageMessage

app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
openai.api_key = os.getenv("OPENAI_API_KEY", None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

handler = WebhookHandler(channel_secret)

configuration = Configuration(
    access_token=channel_access_token
)


@app.route("/callback", methods=['POST'])
def callback():
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


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_message = event.message.text

    if len(user_message) > 200:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="請將問題字數縮短至200字元內，以獲得更快的回應。\nPlease simplify your question to within 200 characters.")]
                )
            )
        return
          
    if user_message == 'Please tell me the latest news about Mia.':
        image_message = ImageMessage(
            original_content_url='https://drive.google.com/uc?export=view&id=1xiuRLm1GsCgoH4qvqQi9NVS_frXKXtyW',
            preview_image_url='https://drive.google.com/uc?export=view&id=17Yk0YWrbo8qD02TXp3_KSCvFJShyG3A-'
        )
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="How to let your friends become Mia's friends too?\n1.Long press this message.\n2.Tap "Share" from the menu.\n3.Select the recipient and confirm to share. Done!\n快把 Mia 介紹給好朋友認識吧!\nhttps://lin.ee/ZsYIo32")]
                )
            )
    elif '全世界誰長得最好笑' in user_message:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="你的哀居的ID")]
                )
            )
    else:
        # 创建一个 prompt，将 AI_GUIDELINES 和用户消息结合
        AI_GUIDELINES = '你現在是台灣新住民的專屬隨身問答助理，專注於幫助新來的居民解決生活中的各種問題。請判斷用戶提問時使用的語言（繁體中文、簡體中文、英文、越南文等），以相同語言回應他們的問題。即使在無法回答用戶問題的情況下，仍需以用戶提問的語言回覆。當用戶提問不是使用中文時，請檢查你的回答不能包含「我」、「無法」、「如果」等詞，因為這些中文詞不是用戶使用的語言。你的回答應該簡單易懂，涵蓋以下幾個領域：1. 語言支持：回答用戶問題時，根據用戶的語言需求提供對應語言的回應。2. 生活資訊：提供有關台灣的日常生活、居住、交通、購物等資訊。例如你知道板橋的新住民家庭服務中心地點在新北市板橋區四川路2段16巷5號10樓，電話為0289668500;你也知道如果想要買電信儲值卡，可以到中華電信的下列INDEX門市，地址為臺北市大安區四維路198巷47號、臺北市萬華區青年路110號、臺北市萬華區國興路32號等。3. 文化習俗：介紹台灣的文化、節慶和習俗，幫助用戶適應本地文化。4. 就業機會：提供關於工作機會、求職技巧和職場文化的資訊。5. 醫療服務：解答關於醫療系統、就醫流程和健康保險的問題。6. 戶政手續：指導用戶如何辦理居留證、工作證等必要的官方文件。例如用戶想考汽機車駕照，你知道交通部公路局汽機車線上隨機模擬考系統的網址是https://www.mvdis.gov.tw/m3-simulator-drv/，能夠幫助用戶準備考試。7. 教育資源：提供有關學校、語言學習和其他教育資源的信息。每次回答時，請確保用語簡潔明瞭，並考慮到新住民可能對台灣的生活和制度不太熟悉。請根據用戶的具體需求，提供最合適的解決方案或建議。'
        prompt = f"{AI_GUIDELINES}\nUser: {user_message}\nAI:"

        try:
            response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": AI_GUIDELINES},
                {"role": "user", "content": user_message}
            ],
            max_tokens=150,
            temperature=0.4
            )
            ai_reply = response.choices[0].message.content

        except Exception as e:
            # 处理任何异常并设置错误回复
            ai_reply = "You can find relevant information on this website:\nhttps://ifi.immigration.gov.tw/wSite/mp?mp=1"
            print(f"Error: {e}")

        # 使用 Line Messaging API 将 AI 的回复发送给用户
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=ai_reply)]
                )
            )
     
#def message_text(event):
#    with ApiClient(configuration) as api_client:
#        line_bot_api = MessagingApi(api_client)
#        line_bot_api.reply_message_with_http_info(
#            ReplyMessageRequest(
#                reply_token=event.reply_token,
#                messages=[TextMessage(text=event.message.text)]
#            )
#        )


if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()

    app.run(debug=options.debug, port=options.port)
