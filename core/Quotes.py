from core.Controller import Controller
from models.OptionBuying import OptionBuying
from models.Quote import Quote
from utils.Utils import Utils
from datetime import datetime, timedelta, date
import pandas as pd


class Quotes:
  @staticmethod
  def getQuote(tradingSymbol, isFnO = False):
    broker = Controller.getBrokerName()
    brokerHandle = Controller.getBrokerLogin().getBrokerHandle()
    quote = None
    if broker == "zerodha":
      key = ('NFO:' + tradingSymbol) if isFnO == True else ('NSE:' + tradingSymbol)
      bQuoteResp = brokerHandle.quote(key) 
      bQuote = bQuoteResp[key]
      # convert broker quote to our system quote
      quote = Quote(tradingSymbol)
      quote.tradingSymbol = tradingSymbol
      quote.lastTradedPrice = bQuote['last_price']
      #quote.lastTradedQuantity = bQuote['last_quantity']
      quote.avgTradedPrice = bQuote['average_price']
      quote.volume = bQuote['volume']
      quote.totalBuyQuantity = bQuote['buy_quantity']
      quote.totalSellQuantity = bQuote['sell_quantity']
      ohlc = bQuote['ohlc']
      quote.open = ohlc['open']
      quote.high = ohlc['high']
      quote.low = ohlc['low']
      quote.close = ohlc['close']
      quote.change = bQuote['net_change']
      quote.oiDayHigh = bQuote['oi_day_high']
      quote.oiDayLow = bQuote['oi_day_low']
      quote.lowerCiruitLimit = bQuote['lower_circuit_limit']
      quote.upperCircuitLimit = bQuote['upper_circuit_limit']
    else:
      # The logic may be different for other brokers
      quote = None
    return quote

  @staticmethod
  def getCMP(tradingSymbol):
    quote = Quotes.getQuote(tradingSymbol)
    if quote:
      return quote.lastTradedPrice
    else:
      return 0
  
  @staticmethod
  def getStrikePrice(tradingSymbol):
    broker = Controller.getBrokerName()
    brokerHandle = Controller.getBrokerLogin().getBrokerHandle()
    quote = None
    if broker == "zerodha":
      key = 'NSE:' + tradingSymbol
      bQuoteResp = brokerHandle.quote(key) 
      quote = bQuoteResp[key]
      if quote:
        return quote['last_price']
      else:
        return 0
    else:
      # The logic may be different for other brokers
      quote = None
    return quote

  @staticmethod
  def getOptionBuyingQuote(tradingSymbol,isFnO):
    quote = Quotes.getQuote(tradingSymbol,isFnO)
    if quote:
      # convert quote to Option buying details
      optionBuying = OptionBuying(tradingSymbol)
      optionBuying.lastTradedPrice = quote.lastTradedPrice
      optionBuying.high = quote.high
      optionBuying.low = quote.low
      optionBuying.entryPrice= (quote.low*1.8)
      optionBuying.stopLoss=(quote.low*1.8)-20
      optionBuying.target=(quote.low*1.8)+40
      optionBuying.isTradeLive=False
    else:
      optionBuying= None
    return optionBuying 

  @staticmethod
  def getHistData(trade_symbol):
    brokerHandle = Controller.getBrokerLogin().getBrokerHandle()
    previous_day = date.today() - timedelta(days=1)
    # 0 = Monday, 1 = Tuesday, ..., 5 = Saturday, 6 = Sunday
    while Utils.isHoliday(previous_day) == True:
      previous_day = previous_day - timedelta(days=1)

    ohlc_data = brokerHandle.historical_data(instrument_token=trade_symbol,
                                     from_date=previous_day,
                                     to_date=previous_day,
                                     interval="day")
    if ohlc_data:
      data_dict = ohlc_data[0]
      previous_day_ohlc = pd.Series({
        'open': data_dict['open'],
        'high': data_dict['high'],
        'low': data_dict['low'],
        'close': data_dict['close']
      })
      #previous_day_ohlc = pd.DataFrame(ohlc_data).iloc[0][['open', 'high', 'low', 'close']].to_dict()
      #print(f"Previous trading day's OHLC for BANKNIFTY ({previous_trading_day}): {previous_day_ohlc}")
      return previous_day_ohlc
    else:
      print(f"No data found for the previous trading day ({previous_day}) for BANKNIFTY. It might be a holiday or data is not yet available.")
    
