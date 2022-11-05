import logging
import datetime
import statistics
from time import sleep
from alice_blue import *
from pprint import pprint
from datetime import datetime, timedelta
from time import sleep
import dateutil.parser
import requests, json
import pandas as pd

# Config
username = '######'
password = 'aliceblue456'
api_secret = '############################'
twoFA = '1994'
app_id='########'
SCRIP = 'Nifty 50'
logging.basicConfig(level=logging.DEBUG)        # Optional for getting debug messages.

ltp = ""
print("ltp is zero")
socket_opened = False
alice = None
def event_handler_quote_update(message):
    global ltp
    ltp = message['ltp']

def open_callback():
    global socket_opened
    socket_opened = True

def buy_signal(ins_scrip):
    global alice
    alice.place_order(transaction_type = TransactionType.Buy,
                         instrument = ins_scrip,
                         quantity = 50000,
                         order_type = OrderType.Market,
                         product_type = ProductType.Intraday,
                         price = 0.0,
                         trigger_price = None,
                         stop_loss = None,
                         square_off = None,
                         trailing_sl = None,
                         is_amo = False)

def sell_signal(ins_scrip):
    global alice
    alice.place_order(transaction_type = TransactionType.Sell,
                         instrument = ins_scrip,
                         quantity = 50000,
                         order_type = OrderType.Market,
                         product_type = ProductType.Intraday,
                         price = 0.0,
                         trigger_price = None,
                         stop_loss = None,
                         square_off = None,
                         trailing_sl = None,
                         is_amo = False)

def get_historical(instrument, from_datetime, to_datetime, interval, indices=False):
    params = {"token": instrument.token,
              "exchange": instrument.exchange if not indices else "NSE_INDICES",
              "starttime": str(int(from_datetime.timestamp())),
              "endtime": str(int(to_datetime.timestamp())),
              "candletype": 3 if interval.upper() == "DAY" else (2 if interval.upper().split("_")[1] == "HR" else 1),
              "data_duration": None if interval.upper() == "DAY" else interval.split("_")[0]}
    lst = requests.get(
        f" https://ant.aliceblueonline.com/api/v1/charts/tdv?", params=params).json()["data"]["candles"]
    records = []
    for i in lst:
        record = {"date": dateutil.parser.parse(i[0]), "open": i[1], "high": i[2], "low": i[3], "close": i[4], "volume": i[5]}
        records.append(record)
    return records

def main():
    global socket_opened
    global alice
    global username
    global password
    global twoFA
    global api_secret
#    global SCRIP
    from datetime import datetime, timedelta
    now = datetime.now().strftime("%I:%M %p")
    if not (((datetime.now().second >= 00) and (datetime.now().second <= 2)) and ( datetime.now().minute % 5 == 0 )):
            print ('Market has not started', now)
            sleep(1)
            main()
    access_token = AliceBlue.login_and_get_access_token(username='######', password='aliceblue456', twoFA='1994', app_id='#######', api_secret='####################')
    alice = AliceBlue(username='######', password='aliceblue456', access_token=access_token, master_contracts_to_download=['NSE','NFO'])
    
    ins_scrip = alice.get_instrument_by_symbol('NSE', SCRIP)
    firsttime = 'yes'

#    socket_opened = False
    print("websocket")
    alice.start_websocket(subscribe_callback=event_handler_quote_update,
                          socket_open_callback=open_callback,
                          run_in_background=True)
    while(socket_opened==False):    # wait till socket open & then subscribe
        pass
    alice.subscribe(ins_scrip, LiveFeedType.MARKET_DATA)
    print("hi0",ltp)
    current_order = ''
    buysignal = ''
    sellsignal = ''
    while True:
        print("while")
        ins_scrip = alice.get_instrument_by_symbol('NSE', SCRIP)
        from datetime import datetime, timedelta
        from_datetime = datetime.now() - timedelta(days=5)
        to_datetime = datetime.now()
        interval = "5_MIN"   # ["DAY", "1_HR", "3_HR", "1_MIN", "5_MIN", "15_MIN", "60_MIN"]
        indices = True
        print(datetime.now())
        print(datetime.now().minute)
        print(datetime.now().second)
        if (firsttime == 'yes') or (((datetime.now().second >= 00) and (datetime.now().second <= 2)) and ( datetime.now().minute % 5 == 0 )):
            print("yes")
            df2 = pd.DataFrame(get_historical(ins_scrip, from_datetime, to_datetime, interval, indices))
            df2.index = df2["date"]
            df2 = df2.drop("date", axis=1)
            df2 = df2.drop("volume", axis=1)
            df2 = df2.drop("open", axis=1)
            df2["5EMAL"] = df2["low"].ewm(span=5, adjust=False).mean()
            df2["5EMAH"] = df2["high"].ewm(span=5, adjust=False).mean()
            df2["5EMAL"] = df2["5EMAL"].round(decimals=2)
            df2["5EMAH"] = df2["5EMAH"].round(decimals=2)
            df2["5EMAC1"] = df2["close"].ewm(span=3, adjust=False).mean()
            df2["5EMAC2"] = df2["5EMAC1"].ewm(span=3, adjust=False).mean()
            df2["5EMAC3"] = df2["5EMAC2"].ewm(span=3, adjust=False).mean()
            df2["TEMA"] = ((df2["5EMAC1"]-df2["5EMAC2"])*3) + df2["5EMAC3"]
            df2["TEMA"] = df2["TEMA"].round(decimals=2)
            df2 = df2.drop("5EMAC1", axis=1)
            df2 = df2.drop("5EMAC2", axis=1)
            df2 = df2.drop("5EMAC3", axis=1)
            df2 = df2.drop("close", axis=1)
            lastcandlehigh = df2.iloc[-2,0]
            lastcandlelow = df2.iloc[-2,1]
            lastemalow = df2.iloc[-2,2]
            lastemahigh = df2.iloc[-2,3]
            lasttema = df2.iloc[-2,4]
            candlehigh = df2.iloc[-1,0]
            candlelow = df2.iloc[-1,1]
            emalow = df2.iloc[-1,2]
            emahigh = df2.iloc[-1,3]
            tema = df2.iloc[-1,4]
            print(lasttema)
            print(tema)
            print(df2.shape)                      
            firsttime = ' '
        print(df2)
        print("hi1", ltp)
        print("candlelow", candlelow, "candlehigh", candlehigh)    
        print("emalow", emalow, "emahigh", emahigh, "tema", tema)
        print("lastemalow", lastemalow, "lastemahigh", lastemahigh, "lasttema", lasttema)
        import datetime
        atm_val = int(round(ltp/50)*50)
        ins_scrip_call = alice.get_instrument_for_fno(symbol = 'NIFTY', expiry_date=datetime.date(2022, 1, 6), is_fut=False, strike=atm_val, is_CE = True)
        ins_scrip_put = alice.get_instrument_for_fno(symbol = 'NIFTY', expiry_date=datetime.date(2022, 1, 6), is_fut=False, strike=atm_val, is_CE = False)
        if ((tema > emalow) and (lasttema < lastemalow)) or ((tema > emahigh) and (lasttema < lastemahigh)):            
            print("buy")
            if (current_order == 'sell'):            
                ins_scrip = ins_scrip_put_hold
                print("sell trailing stoploss is placed")
                current_order = ' '
                sell_signal(ins_scrip)
                tema,lasttema = 1,1
            if (current_order != 'buy'):            
                ins_scrip = ins_scrip_call
                ins_scrip_call_hold = ins_scrip_call
                print("buy order will be placed ")
                buy_signal(ins_scrip)
                current_order = 'buy'
                stoplosslow = candlelow - 3 
                print("buy stoploss",stoplosslow)
        if ((tema < emalow) and (lasttema > lastemalow)) or ((tema < emahigh) and (lasttema > lastemahigh)):
            print("sell")
            if (current_order == 'buy'):            
                ins_scrip = ins_scrip_call_hold
                print("buy trailing stoploss is placed")
                current_order = ' '
                sell_signal(ins_scrip)
                tema,lasttema = 1,1
            if (current_order != 'sell'):
                ins_scrip = ins_scrip_put
                ins_scrip_put_hold = ins_scrip_put
                print("sell order will be placed ")
                buy_signal(ins_scrip)
                current_order = 'sell'
                stoplosshigh = candlehigh + 3
                print("sell stoploss",stoplosshigh)
        if (current_order == 'buy'):            
            if (ltp < stoplosslow):
                ins_scrip = ins_scrip_call_hold
                print("buy stoploss is placed")
                current_order = ' '
                sell_signal(ins_scrip)
                tema,lasttema = 1,1
        if current_order == 'sell':
            if (ltp > stoplosshigh):
                ins_scrip = ins_scrip_put_hold
                print("sell stoploss is placed")
                current_order = ' '
                sell_signal(ins_scrip)
                tema,lasttema = 1,1
        sleep(1)
if(__name__ == '__main__'):
    print("Algo started")
    main()