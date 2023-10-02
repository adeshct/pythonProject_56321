import logging
from datetime import datetime, timedelta
import time
from instruments.Instruments import Instruments
from models.Direction import Direction
from models.ProductType import ProductType
from strategies.BaseStrategy import BaseStrategy
from utils.Utils import Utils
from trademgmt.Trade import Trade
from trademgmt.TradeManager import TradeManager
from core.Quotes import Quotes
from utils.Cpr import Cpr_compute
import numpy as np


# Each strategy has to be derived from BaseStrategy
class PPStrategy(BaseStrategy):
    __instance = None

    @staticmethod
    def getInstance():  # singleton class
        if PPStrategy.__instance == None:
            PPStrategy()
        return PPStrategy.__instance

    def __init__(self):
        if PPStrategy.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            PPStrategy.__instance = self
        # Call Base class constructor
        super().__init__("PPStrategy")
        # Initialize all the properties specific to this strategy
        self.productType = ProductType.MIS
        self.symbols = []
        self.ltp = []
        self.slPercentage = 6
        self.targetPercentage = 0
        self.startTimestamp = Utils.getTimeOfToDay(9, 15, 0)  # When to start the strategy. Default is Market start time
        self.startTimestamp2 = Utils.getTimeOfToDay(9, 20, 0)  # When to start the strategy. Default is Market start time
        self.stopTimestamp = Utils.getTimeOfToDay(15, 15,0)  # This is not square off timestamp. This is the timestamp after which no new trades will be placed under this strategy but existing trades continue to be active.
        self.squareOffTimestamp = Utils.getTimeOfToDay(15, 29, 0)  # Square off time
        self.capital = 10000  # Capital to trade (This is the margin you allocate from your broker account for this strategy)
        self.leverage = 0
        self.maxTradesPerDay = 200  # (1 CE + 1 PE) Max number of trades per day under this strategy
        self.isFnO = True  # Does this strategy trade in FnO or not
        self.capitalPerSet = 10000  # Applicable if isFnO is True (1 set means 1CE/1PE or 2CE/2PE etc based on your strategy logic)
        self.atm_add = 300

    def canTradeToday(self):
        # Even if you remove this function canTradeToday() completely its same as allowing trade every day
        return True

    def process(self):
        now = datetime.now()
        futureSymbol = 'NIFTY BANK'
        if now < self.startTimestamp:
            return
        if len(self.trades) >= self.maxTradesPerDay:
            return
        if self.startTimestamp <= now <=self.startTimestamp2:
            quote = Quotes.getStrikePrice(futureSymbol)
            if quote == None:
                logging.error('%s: Could not get quote for %s', self.getName(), futureSymbol)
                return
            self.ltp.append(quote)
            now = datetime.now()
            time.sleep(timedelta.total_seconds(startTimestamp2 - now))

        # Get current market price of Nifty Future
        # futureSymbol = Utils.prepareMonthlyExpiryFuturesSymbol('BANKNIFTY')
        now = datetime.now()
        if now.minute % 5 != 0:
            mins_to_wait = 5 - now.minute % 5
            logging.info("Sleeping for %d minutes", mins_to_wait)
            time.sleep(timedelta.total_seconds(Utils.getTimeOfToDay(hours=int(now.hour+1 if int(now.minute+mins_to_wait)==60 else now.hour), minutes=int(0 if int(now.minute+mins_to_wait)==60 else int(now.minute+mins_to_wait)),seconds=0) - now))
            self.check_condition(futureSymbol)
        else:
            self.check_condition(futureSymbol)
        return

    def check_condition(self,futureSymbol):
        logging.info("Entering Check condition")
        central_pivot, top_cpr, bottom_cpr, R1, R2, R3,R4, S1, S2, S3,S4 = Cpr_compute.compute_cpr()
        quote = Quotes.getStrikePrice(futureSymbol)
        if quote == None:
            logging.error('%s: Could not get quote for %s', self.getName(), futureSymbol)
            return
        self.ltp.append(quote)
        self.ltp.append(quote+100)
        ltp = self.ltp
        print("LTP ---------------------",ltp)
        #[-2] is used to fetch 5mins open and [-1] to fetch 5mins close
        if (ltp[-2] < top_cpr < ltp[-1]) or (ltp[-2] < R1 < ltp[-1]) or (ltp[-2] < R2 < ltp[-1]) or (ltp[-2] < R3 < ltp[-1]) or (ltp[-2] < R4 < ltp[-1]):
            ATMStrike = Utils.getNearestStrikePrice(quote, 100)
            logging.info('%s: %s = %f, ATMStrike = %d', self.getName(), futureSymbol, quote, ATMStrike)
            ATMCESymbol = Utils.prepareWeeklyOptionsSymbol("BANKNIFTY", ATMStrike + self.atm_add, 'CE')
            logging.info('%s: ATMCESymbol = %s', self.getName(), ATMCESymbol)
            self.generateTrades(ATMCESymbol)

        elif (ltp[-2] < S1 < ltp[-1]) or (ltp[-2] < S2 < ltp[-1]) or (ltp[-2] < S3 < ltp[-1]) or (ltp[-2] < S4 < ltp[-1]):
            ATMStrike = Utils.getNearestStrikePrice(quote, 100)
            logging.info('%s: %s = %f, ATMStrike = %d', self.getName(), futureSymbol, quote, ATMStrike)
            ATMCESymbol = Utils.prepareWeeklyOptionsSymbol("BANKNIFTY", ATMStrike+strike + self.atm_add, 'CE')
            logging.info('%s: ATMCESymbol = %s', self.getName(), ATMCESymbol)
            self.generateTrades(ATMCESymbol)

        elif (ltp[-2] > bottom_cpr > ltp[-1]) or (ltp[-2] > S1 > ltp[-1]) or (ltp[-2] > S2 > ltp[-1]) or (ltp[-2] > S3 > ltp[-1]) or (ltp[-2] > S4 > ltp[-1]):
            ATMStrike = Utils.getNearestStrikePrice(quote, 100)
            logging.info('%s: %s = %f, ATMStrike = %d', self.getName(), futureSymbol, quote, ATMStrike)
            ATMPESymbol = Utils.prepareWeeklyOptionsSymbol("BANKNIFTY", ATMStrike - self.atm_add, 'PE')
            logging.info('%s: ATMCESymbol = %s', self.getName(), ATMPESymbol)
            self.generateTrades(ATMPESymbol)

        elif (ltp[-2] > R1 > ltp[-1]) or (ltp[-2] > R2 > ltp[-1]) or (ltp[-2] > R3 > ltp[-1]) or (ltp[-2] > R4 > ltp[-1]):
            ATMStrike = Utils.getNearestStrikePrice(quote, 100)
            logging.info('%s: %s = %f, ATMStrike = %d', self.getName(), futureSymbol, quote, ATMStrike)
            ATMPESymbol = Utils.prepareWeeklyOptionsSymbol("BANKNIFTY", ATMStrike - self.atm_add, 'PE')
            logging.info('%s: ATMCESymbol = %s', self.getName(), ATMPESymbol)
            self.generateTrades(ATMPESymbol)

        else:
            logging.info('No favourable trade found')
            return

    def generateTrades(self, ATMSymbol):
        numLots = self.calculateLotsPerTrade()
        quoteATMSymbol = self.getQuote(ATMSymbol)
        if quoteATMSymbol == None:
            logging.error('%s: Could not get quotes for option symbols', self.getName())
            return

        self.generateTrade(ATMSymbol, numLots, quoteATMSymbol.lastTradedPrice)
        logging.info('%s: Trades generated.', self.getName())

    def generateTrade(self, optionSymbol, numLots, lastTradedPrice):
        trade = Trade(optionSymbol)
        trade.strategy = self.getName()
        trade.isOptions = True
        trade.direction = Direction.LONG  # Always BUY here as option buying only
        trade.productType = self.productType
        trade.placeMarketOrder = True
        trade.requestedEntry = lastTradedPrice
        trade.timestamp = Utils.getEpoch(self.startTimestamp)  # setting this to strategy timestamp
        trade.slPercentage = 6
        trade.moveToCost = True


        isd = Instruments.getInstrumentDataBySymbol(optionSymbol)  # Get instrument data to know qty per lot
        trade.qty = isd['lot_size'] * numLots

        trade.stopLoss = Utils.roundToNSEPrice(trade.requestedEntry - trade.requestedEntry * self.slPercentage / 100)
        trade.target = 0  # setting to 0 as no target is applicable for this trade

        trade.intradaySquareOffTimestamp = Utils.getEpoch(self.squareOffTimestamp)
        # Hand over the trade to TradeManager
        TradeManager.addNewTrade(trade)

    def shouldPlaceTrade(self, trade, tick):
        # First call base class implementation and if it returns True then only proceed
        if super().shouldPlaceTrade(trade, tick) == False:
            return False
        # We dont have any condition to be checked here for this strategy just return True
        return True

