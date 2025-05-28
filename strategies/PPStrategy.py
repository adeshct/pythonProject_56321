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
        self.productType = ProductType.NRML
        self.symbols = []
        self.ltp = []
        self.slPercentage = 0
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
        self.atm_add = 200
        self.bnf_stoploss = 0
        self.bnf_target = 0
        self.bnf_order_strategy = ""
        self.option_type = ""

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
            time.sleep(timedelta.total_seconds(self.startTimestamp2 - now))

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
        print(central_pivot)
        quote = Quotes.getStrikePrice(futureSymbol)
        logging.info('quote is %d-',quote)
        if quote == None:
            logging.error('%s: Could not get quote for %s', self.getName(), futureSymbol)
            return
        self.ltp.append(quote)
        if len(self.ltp) <=1:
            self.ltp.append(quote)

        ltp = self.ltp
        # print("ltp is - ")
        # print(ltp[-1])
        # logging.info("LTP ---------------------",ltp)
        #[-2] is used to fetch 5mins open and [-1] to fetch 5mins close


        if ltp[-2] < top_cpr + 15 and (top_cpr + (R1 - top_cpr) * 0.5) >= ltp[-1] > top_cpr and ltp[-2] < ltp[-1]:
            # print(str(datetime.datetime.now())+"I'm entering the topcpr logic processing")
            self.option_type = "CE"
            self.bnf_order_strategy = "CE_CPR"
            self.bnf_stoploss = bottom_cpr
            self.bnf_target = top_cpr + (R1 - top_cpr) * 0.8

        elif ltp[-2] < R1 + 15 and R1 + (R2 - R1) * 0.5 >= ltp[-1] > R1 and ltp[-2] < \
                ltp[-1]:
            self.option_type = "CE"
            self.bnf_order_strategy = "CE_R1"
            self.bnf_stoploss = R1 - (R1 - top_cpr) * 0.2
            self.bnf_target = R1 + (R2 - R1) * 0.8
            success = 1

        elif ltp[-2] < R2 + 15 and R2 + (R3 - R2) * 0.5 >= ltp[-1] > R2 and ltp[-2] < \
                ltp[-1]:
            self.option_type = "CE"
            self.bnf_order_strategy = "CE_R2"
            self.bnf_stoploss = R2 - (R2 - R1) * 0.2
            self.bnf_target = R2 + (R3 - R2) * 0.8
            success = 1

        elif ltp[-2] < R3 + 15 and R3 + (R4 - R3) * 0.5 >= ltp[-1] > R3 and ltp[-2] < \
                ltp[-1]:
            self.option_type = "CE"
            self.bnf_order_strategy = "CE_R3"
            self.bnf_stoploss = R3 - (R3 - R2) * 0.2
            self.bnf_target = R3 + (R4 - R3) * 0.8
            success = 1

        elif ltp[-2] < R4 + 15 and R4 + (R4 - R3) * 0.5 >= ltp[-1] > R4 and ltp[-2] < \
                ltp[-1]:
            self.option_type = "CE"
            self.bnf_order_strategy = "CE_R4"
            self.bnf_stoploss = R4 - (R4 - R3) * 0.2
            self.bnf_target = R4 + (R4 - R3) * 0.8
            success = 1

        elif ltp[-2] < S1 + 15 and S1 + (bottom_cpr - S1) * 0.5 >= ltp[-1] > S1 and ltp[-2] < ltp[-1]:
            self.option_type = "CE"
            self.bnf_order_strategy = "CE_S1"
            self.bnf_stoploss = S1 - (S1 - S2) * 0.2
            self.bnf_target = S1 + (bottom_cpr - S1) * 0.8
            success = 1

        elif ltp[-2] < S2 + 15 and S2 + (S1 - S2) * 0.5 >= ltp[-1] > S2 and ltp[-2] < \
                ltp[-1]:
            self.option_type = "CE"
            self.bnf_order_strategy = "CE_S2"
            self.bnf_stoploss = S2 - (S2 - S3) * 0.2
            self.bnf_target = S2 + (S1 - S2) * 0.8
            success = 1

        elif ltp[-2] < S3 + 15 and S3 + (S2 - S3) * 0.5 >= ltp[-1] > S3 and ltp[-2] < \
                ltp[-1]:
            self.option_type = "CE"
            self.bnf_order_strategy = "CE_S3"
            self.bnf_stoploss = S3 - (S3 - S4) * 0.2
            self.bnf_target = S3 + (S2 - S3) * 0.8
            success = 1

        elif ltp[-2] < S4 + 15 and S4 + (S3 - S4) * 0.5 >= ltp[-1] > S4 and ltp[-2] < \
                ltp[-1]:
            self.option_type = "CE"
            self.bnf_order_strategy = "CE_S4"
            self.bnf_stoploss = S4 - (S3 - S4) * 0.2
            self.bnf_target = S2 + (S3 - S4) * 0.8
            success = 1

        # FOR PUT OPTION TRADING ONLY
        elif ltp[-2] > bottom_cpr - 15 and (bottom_cpr - (bottom_cpr - S1) * 0.50) <= ltp[-1] < bottom_cpr and ltp[-2] > ltp[-1]:
            self.option_type = "PE"
            self.bnf_order_strategy = "PE_CPR"
            self.bnf_stoploss = top_cpr
            self.bnf_target = bottom_cpr - (bottom_cpr - S1) * 0.8
            success = 1

        elif ltp[-2] > S1 - 15 and S1 - (S1 - S2) * 0.5 <= ltp[-1] < S1 and ltp[-2] > \
                ltp[-1]:
            self.option_type = "PE"
            self.bnf_order_strategy = "PE_S1"
            self.bnf_stoploss = S1 + (bottom_cpr - S1) * 0.2
            self.bnf_target = S1 - (S1 - S2) * 0.8
            success = 1

        elif ltp[-2] > S2 - 15 and S2 - (S2 - S3) * 0.5 <= ltp[-1] < S2 and ltp[-2] > \
                ltp[-1]:
            self.option_type = "PE"
            self.bnf_order_strategy = "PE_S2"
            self.bnf_stoploss = S2 + (S1 - S2) * 0.2
            self.bnf_target = S2 - (S2 - S3) * 0.8
            success = 1

        elif ltp[-2] > S3 - 15 and S3 - (S3 - S4) * 0.5 <= ltp[-1] < S3 and ltp[-2] > \
                ltp[-1]:
            self.option_type = "PE"
            self.bnf_order_strategy = "PE_S3"
            self.bnf_stoploss = S3 + (S2 - S3) * 0.2
            self.bnf_target = S3 - (S3 - S4) * 0.8
            success = 1

        elif ltp[-2] > S4 - 15 and S4 - (S3 - S4) * 0.5 <= ltp[-1] < S4 and ltp[-2] > \
                ltp[-1]:
            self.option_type = "PE"
            self.bnf_order_strategy = "PE_S4"
            self.bnf_stoploss = S4 + (S3 - S4) * 0.2
            self.bnf_target = S4 - (S3 - S4) * 0.8
            success = 1

        elif ltp[-2] > R1 - 15 and R1 - (R1 - top_cpr) * 0.5 <= ltp[-1] < R1 and ltp[-2] > ltp[-1]:
            self.option_type = "PE"
            self.bnf_order_strategy = "PE_R1"
            self.bnf_stoploss = R1 + (R2 - R1) * 0.2
            self.bnf_target = R1 - (R1 - top_cpr) * 0.8
            success = 1

        elif ltp[-2] > R2 - 15 and R2 - (R2 - R1) * 0.5 <= ltp[-1] < R2 and ltp[-2] > \
                ltp[-1]:
            self.option_type = "PE"
            self.bnf_order_strategy = "PE_R2"
            self.bnf_stoploss = R2 + (R3 - R2) * 0.2
            self.bnf_target = R2 - (R2 - R1) * 0.8
            success = 1

        elif ltp[-2] > R3 - 15 and R3 - (R3 - R2) * 0.5 <= ltp[-1] < R3 and ltp[-2] > \
                ltp[-1]:
            self.option_type = "PE"
            self.bnf_order_strategy = "PE_R3"
            self.bnf_stoploss = R3 + (R4 - R3) * 0.2
            self.bnf_target = R3 - (R3 - R2) * 0.8
            success = 1

        elif ltp[-2] > R4 - 15 and R4 - (R4 - R3) * 0.5 <= ltp[-1] < R4 and ltp[-2] > \
                ltp[-1]:
            self.option_type = "PE"
            self.bnf_order_strategy = "PE_R4"
            self.bnf_stoploss = R4 + (R4 - R3) * 0.2
            self.bnf_target = R4 - (R4 - R3) * 0.8
            success = 1

        else:
            logging.info('No favourable trade found')
            logging.info("%d - Open: %d - Close", ltp[-2], ltp[-1] )
            return

        ATMStrike = Utils.getNearestStrikePrice(quote, 100)
        logging.info('%s: %s = %f, ATMStrike = %d', self.getName(), futureSymbol, quote, ATMStrike)
        ATMSymbol = Utils.prepareWeeklyOptionsSymbol("BANKNIFTY", ATMStrike + self.atm_add, self.option_type,1)
        logging.info('%s: ATMSymbol = %s', self.getName(), ATMSymbol)

        # If the candle is smaler one, waiting for next
        if abs(ltp[-2] - ltp[-1]) <=20:
            logging.info("The candle length is very less. Waiting for next 5 minutes")
            time.sleep(299)
            quote = Quotes.getStrikePrice(futureSymbol)
            if self.option_type == "CE" and ltp[-1] < quote:
                self.ltp.append(quote)
                logging.info("The difference between the Open is %d and Close is %d. Executed CE", ltp[-1], quote)
                self.generateTrades(ATMSymbol)

            elif self.option_type == "PE" and ltp[-1] > quote:
                self.ltp.append(quote)
                logging.info("The difference between the Open is %d and Close is %d. Executed PE", ltp[-1], quote)
                self.generateTrades(ATMSymbol)

            else:
                return
        else:
            self.generateTrades(ATMSymbol)
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
        trade.exchange = "NFO"
        trade.strategy = self.getName()
        trade.isOptions = True
        trade.direction = Direction.LONG  # Always BUY here as option buying only
        trade.productType = self.productType
        trade.placeMarketOrder = True
        trade.requestedEntry = lastTradedPrice
        trade.timestamp = Utils.getEpoch(self.startTimestamp)  # setting this to strategy timestamp
        trade.slPercentage = self.slPercentage
        trade.bnf_stoploss = self.bnf_stoploss
        trade.bnf_target = self.bnf_target
        trade.bnf_order_strategy = self.bnf_order_strategy
        trade.stopLoss = 0
        trade.moveToCost = True
        trade.optionType = self.option_type


        isd = Instruments.getInstrumentDataBySymbol(optionSymbol)  # Get instrument data to know qty per lot
        trade.qty = isd['lot_size'] * numLots


        #trade.stopLoss = Utils.roundToNSEPrice(trade.requestedEntry - trade.requestedEntry * self.slPercentage / 100)
        # trade.target = Utils.roundToNSEPrice(trade.requestedEntry - trade.requestedEntry * self.targetPercentage / 100)
        # setting to 0 as no target is applicable for this trade

        trade.intradaySquareOffTimestamp = Utils.getEpoch(self.squareOffTimestamp)
        # Hand over the trade to TradeManager
        TradeManager.addNewTrade(trade)

    def shouldPlaceTrade(self, trade, tick):
        # First call base class implementation and if it returns True then only proceed
        if super().shouldPlaceTrade(trade, tick) == False:
            return False
        # We dont have any condition to be checked here for this strategy just return True
        return True

