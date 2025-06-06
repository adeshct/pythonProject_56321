import logging
from datetime import datetime

from instruments.Instruments import Instruments
from models.Direction import Direction
from models.ProductType import ProductType
from strategies.BaseStrategy import BaseStrategy
from utils.Utils import Utils
from trademgmt.Trade import Trade
from trademgmt.TradeManager import TradeManager
from core.Quotes import Quotes

# Each strategy has to be derived from BaseStrategy
class ShortStraddleBNF(BaseStrategy):
  __instance = None

  @staticmethod
  def getInstance(): # singleton class
    if ShortStraddleBNF.__instance == None:
      ShortStraddleBNF()
    return ShortStraddleBNF.__instance

  def __init__(self):
    if ShortStraddleBNF.__instance != None:
      raise Exception("This class is a singleton!")
    else:
      ShortStraddleBNF.__instance = self
    # Call Base class constructor
    super().__init__("ShortStraddleBNF")
    # Initialize all the properties specific to this strategy
    self.productType = ProductType.MIS
    self.symbols = []
    self.slPercentage = 25
    self.targetPercentage = 0
    self.startTimestamp = Utils.getTimeOfToDay(9, 21, 0) # When to start the strategy. Default is Market start time
    self.stopTimestamp = Utils.getTimeOfToDay(13, 30, 0) # This is not square off timestamp. This is the timestamp after which no new trades will be placed under this strategy but existing trades continue to be active.
    self.squareOffTimestamp = Utils.getTimeOfToDay(15, 12, 0) # Square off time
    self.capital = 100000 # Capital to trade (This is the margin you allocate from your broker account for this strategy)
    self.leverage = 0
    self.maxTradesPerDay = 10 # (1 CE + 1 PE) Max number of trades per day under this strategy
    self.isFnO = True # Does this strategy trade in FnO or not
    self.capitalPerSet = 100000 # Applicable if isFnO is True (1 set means 1CE/1PE or 2CE/2PE etc based on your strategy logic)

  def canTradeToday(self):
    # Even if you remove this function canTradeToday() completely its same as allowing trade every day
    return True

  def process(self):
    now = datetime.now()
    if now < self.startTimestamp:
      return
    if len(self.trades) >= self.maxTradesPerDay:
      return

    # Get current market price of Nifty Future
    #futureSymbol = Utils.prepareMonthlyExpiryFuturesSymbol('BANKNIFTY')
    futureSymbol='NIFTY BANK'
    quote = Quotes.getStrikePrice(futureSymbol) 
    if quote == None:
      logging.error('%s: Could not get quote for %s', self.getName(), futureSymbol)
      return

    ATMStrike = Utils.getNearestStrikePrice(quote, 100)
    logging.info('%s: %s = %f, ATMStrike = %d', self.getName(),futureSymbol,quote, ATMStrike)

    ATMCESymbol = Utils.prepareWeeklyOptionsSymbol("BANKNIFTY", ATMStrike, 'CE')
    ATMPESymbol = Utils.prepareWeeklyOptionsSymbol("BANKNIFTY", ATMStrike, 'PE')
    logging.info('%s: ATMCESymbol = %s, ATMPESymbol = %s', self.getName(), ATMCESymbol, ATMPESymbol)
    # create trades
    self.generateTrades(ATMCESymbol, ATMPESymbol)

  def generateTrades(self, ATMCESymbol, ATMPESymbol):
    numLots = self.calculateLotsPerTrade()
    quoteATMCESymbol = self.getQuote(ATMCESymbol)
    quoteATMPESymbol = self.getQuote(ATMPESymbol)
    if quoteATMCESymbol == None or quoteATMPESymbol == None:
      logging.error('%s: Could not get quotes for option symbols', self.getName())
      return

    self.generateTrade(ATMCESymbol, numLots, quoteATMCESymbol.lastTradedPrice,ATMPESymbol)
    self.generateTrade(ATMPESymbol, numLots, quoteATMPESymbol.lastTradedPrice,ATMCESymbol)
    logging.info('%s: Trades generated.', self.getName())

  def generateTrade(self, optionSymbol, numLots, lastTradedPrice,counterPosition):
    trade = Trade(optionSymbol)
    trade.strategy = self.getName()
    trade.isOptions = True
    trade.direction = Direction.SHORT # Always short here as option selling only
    trade.productType = self.productType
    trade.placeMarketOrder = True
    trade.requestedEntry = lastTradedPrice
    trade.timestamp = Utils.getEpoch(self.startTimestamp) # setting this to strategy timestamp
    trade.slPercentage = 25
    trade.moveToCost=True
    trade.counterPosition=counterPosition
    
    isd = Instruments.getInstrumentDataBySymbol(optionSymbol) # Get instrument data to know qty per lot
    trade.qty = isd['lot_size'] * numLots
    
    trade.stopLoss = Utils.roundToNSEPrice(trade.requestedEntry + trade.requestedEntry * self.slPercentage / 100)
    trade.target = 0 # setting to 0 as no target is applicable for this trade

    trade.intradaySquareOffTimestamp = Utils.getEpoch(self.squareOffTimestamp)
    # Hand over the trade to TradeManager
    TradeManager.addNewTrade(trade)

  def shouldPlaceTrade(self, trade, tick):
    # First call base class implementation and if it returns True then only proceed
    if super().shouldPlaceTrade(trade, tick) == False:
      return False
    # We dont have any condition to be checked here for this strategy just return True
    return True

