from flask.views import MethodView
from flask import render_template, request

class HomeAPI(MethodView):
  def get(self):
    def get_server_ip():
      """ Fetch the public IP of the server. """
      try:
        # AWS metadata service for private IP
        private_ip = requests.get("http://169.254.169.254/latest/meta-data/local-ipv4", timeout=2).text
        # Public IP (if required)
        public_ip = requests.get("https://api64.ipify.org?format=json", timeout=2).json().get("ip")
        return public_ip  # Use public_ip if you need an external-facing IP
      except Exception:
        return socket.gethostbyname(socket.gethostname())  # Fallback to local IP
        
    server_ip =  get_server_ip()
    
    if 'loggedIn' in request.args and request.args['loggedIn'] == 'true':
      return render_template('index_loggedin.html', server_ip=server_ip)
    elif 'algoStarted' in request.args and request.args['algoStarted'] == 'true':
      return render_template('index_algostarted.html', server_ip=server_ip)
    else:
      return render_template('index.html', server_ip=server_ip)
  
