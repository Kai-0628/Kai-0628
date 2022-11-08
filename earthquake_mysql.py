from datetime import datetime
import random,time,re,requests
import mysql.connector as mysql
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

#Chrome與chromedriver版本必須相同，不然開啟網頁及閃退

def getData(yyyy,mm):
    select_quantity = Select(browser.find_element(By.NAME, "table_length"))  # 選取下拉選單
    select_quantity.select_by_value("-1")#網頁檢查ALL資料數值為-1
    select_block = browser.find_element(By.NAME, "Search")
    select_block.clear()  # 清除選單內文字（可以手動輸入的選單）
    select_block.send_keys(f'{yyyy},{mm}')  # 輸入日期
    select_block.send_keys(u'\ue007')  # 模擬鍵盤按Enter鍵
    time.sleep(1)#暫停1秒鐘才抓取資料
    # select_block.send_keys(u'\ue004')  # 模擬鍵盤按Tab鍵

    try:
        WebDriverWait(browser, 20).until(EC.presence_of_element_located((By.TAG_NAME,'td')))
    except:
        print("跳出來的失敗了...ORZ")


    # 爬取網頁資料
    page = browser.page_source
    soup=BeautifulSoup(page,'html.parser')
    trs=soup.find_all('td','d-lg-none')
    url="https://scweb.cwb.gov.tw"
    links = {}  # 存放網址
    table = {}
    for tr in trs:
        link = tr.find("a")  # 搜尋標籤<a>裡href的連結網址
        links[link.text] = f"{url}{link.get('href')}"
        # print(links[link.text])
    for key in links.keys():  # key為標題
        result = requests.get(links[key])  # 訪問上階段node抓的網址
        result.encoding = "utf-8"
        soup = BeautifulSoup(result.text, "html.parser")  # 樹狀節點分析（資料整理）
        trs = soup.find_all('div', 'eqResultBoxBg clear')  # 搜尋標籤<div>裡關鍵字裡的標題，抓取行數內容
        # print(trs)
        for i in range(len(trs)):
            tr = trs[i]
            tds = tr.find_all('div')  #搜尋標籤<div>裡的內容
            key = tds[1].text  # 定義時間列給後面時間差判定使用
            ss= [float(s) for s in re.findall(r'-?\d+\.?\d*', key)]  #因為時間是民國年，使用key抓取時間文字內數字
            key=datetime(int(f'{ss[0]:.0f}')+1911
                         ,int(f'{ss[1]:.0f}')
                         ,int(f'{ss[2]:.0f}')
                         ,int(f'{ss[3]:.0f}')
                         ,int(f'{ss[4]:.0f}')
                         ,int(f'{ss[5]:.0f}'))#換算西元年及時間格式排列yyyy:mm:dd HH:MM:SS
            print(key)#列印用來看程式是否運作及進度
            ls = []
            for j in range(1, 6):  # 抓取需要列的內容，第0個是小區域及編號不需要，從1開始抓取資料。
                ls.append(tds[j].text.replace('\n', '').replace('\r', '').replace(' ', ''))  # 轉字串，並把有\n,\r及空格的部分取消掉
            table[key] = ls
    delay = random.randint(1, 3) + random.random()
    time.sleep(delay)#預防被鎖IP
    return table


ops=Options()
ops.add_argument('--headless')#無頭，不顯示瀏覽器
ops.add_argument('--disable-qpu')
browser=webdriver.Chrome("chromedriver.exe",options=ops)
browser.get("https://scweb.cwb.gov.tw/zh-tw/earthquake/data")

try:
    WebDriverWait(browser, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'td')))
except:
    print("連線有問題")

# getData(2022,11)

conn=mysql.connect(host="localhost",user="資料庫賬號",password="資料庫密碼",database="資料庫名稱")
cursor=conn.cursor()
cmd="insert into 台灣地震 (發震時間,震央位置,地震深度,芮氏規模,相對位置) values(%s,%s,%s,%s,%s)"#與資料庫對應資料

now_year=datetime.now().year
now_month=datetime.now().month
for y in range(1995,now_year+1):#地震網站資料從1995年至今
    for m in range(1,13):#一年有12個月
        if y==now_year and m>now_month:break #抓取資料超過現在月份時候停止
        table=getData(y,m)
        data=[]
        for key in table.keys():
            ls=table[key]
            data.append([str(key),ls[1],ls[2],ls[3],ls[4]])#抓取對應資料
        cursor.execute(f"delete from 台灣地震 where 發震時間 like '{y}-{m:02}%'")#當月資料有重複刪除整個月分資料從寫
        conn.commit()
        cursor.executemany(cmd,data)
        conn.commit()

browser.close()#關閉瀏覽器。一定要關閉, 不然會因為重複開啟多個瀏覽器而佔用記憶体
browser.quit()#關閉驅動程式
