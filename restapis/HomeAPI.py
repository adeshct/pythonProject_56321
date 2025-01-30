from flask.views import MethodView
from flask import render_template, request
import socket
import requests
from utils.Utils import get_server_ip

class HomeAPI(MethodView):
  def get(self):
    server_ip =  get_server_ip()
    
    if 'loggedIn' in request.args and request.args['loggedIn'] == 'true':
      return render_template('index_loggedin.html', server_ip=server_ip)
    elif 'algoStarted' in request.args and request.args['algoStarted'] == 'true':
      return render_template('index_algostarted.html', server_ip=server_ip)
    else:
      return render_template('index.html', server_ip=server_ip)
  
