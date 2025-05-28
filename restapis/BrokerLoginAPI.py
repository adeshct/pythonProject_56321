import logging
from flask.views import MethodView
from flask import request, redirect

from core.Controller import Controller 

class BrokerLoginAPI(MethodView):
  def get(self):
    logging.info("Inside Broker Login API")
    redirectUrl = Controller.handleBrokerLogin(request.args)
    logging.info("Redirect URL : %s", redirectUrl)
    return redirect(redirectUrl, code=302)