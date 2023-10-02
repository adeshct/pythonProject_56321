import logging

from config.Config import getBrokerAppConfig
from loginmgmt.ZerodhaLogin import ZerodhaLogin
from models.BrokerAppDetails import BrokerAppDetails


class Controller:
  brokerLogin = None # static variable
  brokerName = None # static variable

  def handleBrokerLogin(args):
    brokerAppConfig = getBrokerAppConfig()

    brokerAppDetails = BrokerAppDetails(brokerAppConfig['broker'])
    brokerAppDetails.setClientID(brokerAppConfig['clientID'])
    brokerAppDetails.setAppKey(brokerAppConfig['appKey'])
    brokerAppDetails.setAppSecret(brokerAppConfig['appSecret'])
    brokerAppDetails.setPassword(brokerAppConfig['password'])
    brokerAppDetails.setTotp(brokerAppConfig['totp'])
    brokerAppDetails.setWebdriverPath(brokerAppConfig['webdriver_path'])

    logging.info('handleBrokerLogin appKey %s', brokerAppDetails.appKey)
    Controller.brokerName = brokerAppDetails.broker
    if Controller.brokerName == 'zerodha':
      Controller.brokerLogin = ZerodhaLogin(brokerAppDetails)
    # Other brokers - not implemented
    #elif Controller.brokerName == 'fyers':
      #Controller.brokerLogin = FyersLogin(brokerAppDetails)

    redirectUrl = Controller.brokerLogin.login(args)
    return redirectUrl

  def getBrokerLogin():
    return Controller.brokerLogin

  def getBrokerName():
    return Controller.brokerName
