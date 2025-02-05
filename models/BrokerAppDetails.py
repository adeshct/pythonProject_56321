

class BrokerAppDetails:
  def __init__(self, broker):
    self.broker = broker
    self.appKey = None
    self.appSecret = None


  def setClientID(self, clientID):
    self.clientID = clientID

  def setAppKey(self, appKey):
    self.appKey = appKey

  def setAppSecret(self, appSecret):
    self.appSecret = appSecret

  def setPassword(self, password):
    self.password = password

  def setTotp(self, totp):
    self.totp = totp

  def setWebdriverPath(self, webdriver_path):
    self.webdriver_path = webdriver_path