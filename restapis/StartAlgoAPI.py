from flask.views import MethodView
import json
import logging
import threading
from config.Config import getSystemConfig
from core.Algo import Algo
from utils.Utils import Utils

class StartAlgoAPI(MethodView):
  def post(self):
    # start algo in a separate thread
    server_ip = Utils.get_server_ip()
    x = threading.Thread(target=Algo.startAlgo)
    x.start()
    systemConfig = getSystemConfig()
    homeUrl = 'http://127.0.0.1:8080/?algoStarted=true'
    logging.info('Sending redirect url %s in response', homeUrl)
    respData = { 'redirect': homeUrl }
    return json.dumps(respData)
  
