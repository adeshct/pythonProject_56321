import logging
import time
from datetime import datetime

from models.ProductType import ProductType
from core.Quotes import Quotes
from trademgmt.TradeManager import TradeManager

from utils.Utils import Utils

class BaseStrategy:
  def __init__(self, name):
    # NOTE: All the below properties should be set by the Derived Class (Specific to each strategy)
    self.name = name # strategy name
    self.enabled = True # Strategy will be run only when it is enabled
    self.productType = ProductType.MIS # MIS/NRML/CNC etc
    self.symbols = [] # List of stocks to be traded under this strategy
    self.slPercentage = 0
    self.targetPercentage = 0
    self.startTimestamp = Utils.getMarketStartTime() # When to start the strategy. Default is Market start time
    self.stopTimestamp = None # This is not square off timestamp. This is the timestamp after which no new trades will be placed under this strategy but existing trades continue to be active.
    self.squareOffTimestamp = None # Square off time
    self.capital = 10000 # Capital to trade (This is the margin you allocate from your broker account for this strategy)
    self.leverage = 1 # 2x, 3x Etc
    self.maxTradesPerDay = 100 # Max number of trades per day under this strategy
    self.isFnO = False # Does this strategy trade in FnO or not
    self.capitalPerSet = 0 # Applicable if isFnO is True (Set means 1CE/1PE or 2CE/2PE etc based on your strategy logic)
    # Register strategy with trade manager
    TradeManager.registerStrategy(self)
    # Load all trades of this strategy into self.trades on restart of app
    self.trades = TradeManager.getAllTradesByStrategy(self.name)

  def getName(self):
    return self.name

  def isEnabled(self):
    return self.enabled

  def setDisabled(self):
    self.enabled = False

  def process(self):
    # Implementation is specific to each strategy - To defined in derived class
    logging.info("BaseStrategy process is called.")
    pass

  def calculateCapitalPerTrade(self):
    leverage = self.leverage if self.leverage > 0 else 1
    capitalPerTrade = int(self.capital * leverage / self.maxTradesPerDay)
    return capitalPerTrade

  def calculateLotsPerTrade(self):
    if self.isFnO == False:
      return 0
    # Applicable only for fno
    #return int(self.capital / self.capitalPerSet)
    return 1

  def canTradeToday(self):
    # Derived class should override the logic if the strategy to be traded only on specific days of the week
    return True

  def run(self):
    # NOTE: This should not be overriden in Derived class
    TradeManager.registerStrategy(self)
    if self.enabled == False:
      logging.warning("%s: Not going to run strategy as its not enabled.", self.getName())
      return

    if Utils.isMarketClosedForTheDay():
      message="{}: Not going to run strategy as market is closed.".format(self.getName())
      Utils.sendMessageTelegramBot(message)
      logging.warning(message)
      return

    now = datetime.now()
    if now < Utils.getMarketStartTime():
      Utils.waitTillMarketOpens(self.getName())

    if self.canTradeToday() == False:
      logging.warning("%s: Not going to run strategy as it cannot be traded today.", self.getName())
      return
    
    now = datetime.now()
    if now < self.startTimestamp:
      waitSeconds = Utils.getEpoch(self.startTimestamp) - Utils.getEpoch(now)
      message="{0} Waiting for {1} seconds till strategy start timestamp reaches...".format(self.getName(),waitSeconds)
      Utils.sendMessageTelegramBot(message)
      logging.info(message)
      if waitSeconds > 0:
        time.sleep(waitSeconds)      

    # Run in an loop and keep processing
    while True:
      if Utils.isMarketClosedForTheDay():
        logging.warning("%s: Exiting the strategy as market closed.", self.getName())
        break

      # Derived class- specific implementation will be called when process() is called
      logging.info('The process started=---------------------')
      self.process()

      # Sleep and wake up on every 30th second
      now = datetime.now()
      logging.info('The process ended---------------------')
      waitSeconds = 90  # 30 - (now.second % 30)
      logging.info('The process will wait up to %d seconds---------------------', waitSeconds)
      time.sleep(waitSeconds)
      logging.info("The process woke up-----------------------")

  def shouldPlaceTrade(self, trade, tick):
    # Each strategy should call this function from its own shouldPlaceTrade() method before working on its own logic
    if trade == None:
      return False
    if trade.qty == 0:
      TradeManager.disableTrade(trade, 'InvalidQuantity')
      return False

    now = datetime.now()
    if now > self.stopTimestamp:
      TradeManager.disableTrade(trade, 'NoNewTradesCutOffTimeReached')
      return False

    numOfTradesPlaced = TradeManager.getNumberOfTradesPlacedByStrategy(self.getName())
    if numOfTradesPlaced >= self.maxTradesPerDay:
      TradeManager.disableTrade(trade, 'MaxTradesPerDayReached')
      return False

    return True

  def addTradeToList(self, trade):
    if trade != None:
      self.trades.append(trade)

  def getQuote(self, tradingSymbol):
    return Quotes.getQuote(tradingSymbol, self.isFnO)

  def getTrailingSL(self, trade):
    # if (trade.cmp - trade.stopLoss) >= 40 and (trade.cmp -trade.initialStopLoss) <= 60:
    #   return Utils.roundToNSEPrice(trade.stopLoss +20)
    # elif (trade.cmp -trade.initialStopLoss) >=60:
    #   return Utils.roundToNSEPrice(trade.initialStopLoss+60)
    # else:
      return trade.stopLoss