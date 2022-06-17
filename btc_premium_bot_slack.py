#CEX api
import ccxt
import pandas as pd
import pyupbit 
import coinbasepro as cbp
from datetime import datetime
import schedule
import time
#import matplotlib.pyplot as plt

#slack setup
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


#slack_bot
def slack_bot():
    slack_token=input("slack_token: ")
    channel_id=input("channel_id: ")
    client_slack=WebClient(token=slack_token)


    #오늘 날짜 설정
    today=datetime.today().strftime("%Y-%m-%d %H:%M")

    #FX
    import investpy

    #Data for Binance

    data=pd.DataFrame({
        'crypto':["BTC/USDT","BTC/TRY","BTC/AUD","BTC/BRL","BTC/EUR","BTC/GBP","BTC/RUB","BTC/UAH"],
        'symbol':["USDT/USD","TRY/USD","AUD/USD","BRL/USD","EUR/USD","GBP/USD","RUB/USD","UAH/USD"],
        'title':["Binance_USD","TRY","AUD","BRL","EUR","GBP","RUB","UAH"]
    })

    #Binance

    def fetch_price(ticker):
        binance=ccxt.binance()
        price=binance.fetch_ticker(ticker)
        return price['last']

    data['local_price']=data.apply(lambda x : fetch_price(x['crypto']),axis=1)

    #Upbit

    data2=pd.DataFrame({
        'crypto':["KRW-BTC"],
        'symbol':["KRW/USD"],
        'title':['KIMCHI']
    })

    data2['local_price']=float(pyupbit.get_current_price(data2.loc[0,'crypto']))

    #Coinbase
    data3=pd.DataFrame({
        'crypto':["BTC-USD"],
        'symbol':["USD/USD"],
        'title':["Coinbase_USD"]
    })
    client=cbp.PublicClient()
    data3['local_price']=float(client.get_product_ticker(data3.loc[0,'crypto'])['price'])

    #Merge
    data=pd.concat([data,data2,data3],ignore_index=True)


    #FX
    fx=investpy.currency_crosses.get_currency_crosses_overview('USD', as_json=False, n_results=1000)
    data=data.join(fx.set_index('symbol')['bid'],on='symbol')
    data.loc[0,'bid']=1
    data.loc[9,'bid']=1

    #calculating premium

    data['usd_price']=data['local_price']*data['bid']
    p0=data.loc[0,'usd_price']
    data['premium']=data.apply(lambda x : x['usd_price']/p0-1,axis=1)
    data=data.sort_values(by=data.columns[5],ascending=False)
    data=data.reset_index(drop=True)

    table=data[['title','premium']]
    table['premium']=(table['premium']*100).round(1)

    #Slack에 보낼 Text 병합
    text='<{} Bitcoin premium>'.format(today)
    for i in range(len(data)):
        text+='\n'
        df='{}.{} Premium: {:.1f}%'.format(i+1,data.loc[i,'title'],100*data.loc[i,'premium'])
        text+=df


    #slack에 메세지 보내기
    try:

        response=client_slack.chat_postMessage(channel=channel_id,
                                               text=text)
        print(text)
    except SlackApiError as e:
        assert e.response["error"]

#실행 주기 설정
schedule.every().day.at("06:00").do(slack_bot)

#스케줄 시작
while True:
    schedule.run_pending()
    time.sleep(1)

