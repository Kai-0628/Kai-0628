from flask import Flask, request, abort
import requests, re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import (MessageEvent, TextMessage, TextSendMessage,)



app = Flask(__name__)

msg_tip = """10分鐘內沒有相關訊息
先好好待著吧(￣ 3￣)y▂ξ"
---------------
也有可能網站沒更新
1分鐘後可以再查詢試試
"""

line_bot_api = LineBotApi( '1g1Z56BGdY1RKAtQjxjLi9w65pBMtrBh3Rn2YJuZBNvCu6bpj3ECeIJqx+MoCChKi135DP0x5HRK3EZcvlYdJWj3aXK8vMLl9IgWB4bn2cz3hzbpRnJ0jUoZM/UeL4KXkF7IyObIWhpSy8RtVkJ1sgdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('709ce11febe5e5763bfc72d2a359cdf0')


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
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message_text = event.message.text
    url = "https://scweb.cwb.gov.tw/"
    page = requests.get(url)
    # page.encoding="utf-8"
    soup = BeautifulSoup(page.text, "html.parser")
    nodes = soup.find_all('tr', onmouseover="myClick(0)")
    links = {}
    for node in nodes:
        link = node.find("a")
        links[link.text] = f"{url}{link.get('href')}"
    for key in links.keys():
        result = requests.get(links[key])
        result.encoding = "utf-8"
        soup = BeautifulSoup(result.text, "html.parser")
        trs = soup.find_all('div', 'eqResultBoxBg clear')
        table = {}
        for i in range(len(trs)):
            tr = trs[i]
            tds = tr.find_all('li')
            key = tds[1].text
            ls = []
            for j in range(0, 6):
                ls.append(tds[j].text.replace('\n', '').replace('\r', '').replace(' ', ''))
            table[key] = ls
            # print(table[key])
    # t1 = datetime.now()
    t1 = datetime(2022, 10, 28, 23, 31, 12, 926763)#測試地震接近時間用
    # print('現在時間：', t1)

    ss = [float(s) for s in re.findall(r'-?\d+\.?\d*', key)]# 抓取數字
    t2 = datetime(int(f'{ss[0]:.0f}') + 1911,
                  int(f'{ss[1]:.0f}')
                  , int(f'{ss[2]:.0f}')
                  , int(f'{ss[3]:.0f}')
                  , int(f'{ss[4]:.0f}')
                  , int(f'{ss[5]:.0f}'))
    # print('地震時間：', t2)

    if t1 - t2 < timedelta(minutes=10):
        msg = f'Σ( ° △ °)→→{"，".join(table[key])}'
        # print(msg)
    else:
        msg = msg_tip
        # print(msg)

    if message_text == '地震':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg))


if __name__ == "__main__":
    app.run()