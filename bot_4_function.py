import requests,re
from datetime import datetime,timedelta
from bs4 import BeautifulSoup
from flask import Flask, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *

app = Flask(__name__)

msg_tip = """10分鐘內沒有相關訊息
先好好待著吧(￣ 3￣)y▂ξ"
---------------
也有可能網站沒更新
1分鐘後可以再查詢試試
"""
# Line Bot驗證
line_bot_api = LineBotApi('1g1Z56BGdY1RKAtQjxjLi9w65pBMtrBh3Rn2YJuZBNvCu6bpj3ECeIJqx+MoCChKi135DP0x5HRK3EZcvlYdJWj3aXK8vMLl9IgWB4bn2cz3hzbpRnJ0jUoZM/UeL4KXkF7IyObIWhpSy8RtVkJ1sgdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('709ce11febe5e5763bfc72d2a359cdf0')

#抓取地震資料
def earth_quake():
    links = {}
    table = {}
    url = "https://scweb.cwb.gov.tw/"
    page = requests.get(url)
    page.encoding = "utf-8"
    soup = BeautifulSoup(page.text, "html.parser")
    nodes = soup.find_all('tr', onmouseover="myClick(0)")
    for node in nodes:
        link = node.find("a")
        links[link.text] = f"{url}{link.get('href')}"
    for key in links.keys():
        result = requests.get(links[key])
        result.encoding = "utf-8"
        soup = BeautifulSoup(result.text, "html.parser")
        trs = soup.find_all('div', 'eqResultBoxBg clear')
        for i in range(len(trs)):
            tr = trs[i]
            tds = tr.find_all('li')
            key = tds[1].text
            ls = []
            for j in range(1, 6):
                ls.append(tds[j].text.replace('\n', '').replace('\r', '').replace(' ', ''))
            table[key] = ls
        t1 = datetime.now()
        # t1 = datetime(2022, 10, 18, 11, 0, 12, 926763)
        ss = [float(s) for s in re.findall(r'-?\d+\.?\d*', key)]  # 抓取數字
        t2 = datetime(int(f'{ss[0]:.0f}') + 1911,
                      int(f'{ss[1]:.0f}')
                      , int(f'{ss[2]:.0f}')
                      , int(f'{ss[3]:.0f}')
                      , int(f'{ss[4]:.0f}')
                      , int(f'{ss[5]:.0f}'))
        if t1 - t2 < timedelta(minutes=10):
            data = f'Σ( ° △ °)→→{"，".join(table[key])}'
            print(data)
        else:
            data = msg_tip
            print(data)
    return data

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback(request):
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    print(body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if "地震" in event.message.text:
        result = earth_quake()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=result)
        )
    elif "清單" in event.message.text:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="還沒生出來~")
        )


if __name__ == "__main__":
    app.run()
