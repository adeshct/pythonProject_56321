import logging
from kiteconnect import KiteConnect
from datetime import timedelta, datetime, time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from time import sleep
from config.Config import getSystemConfig
from loginmgmt.BaseLogin import BaseLogin
from pyotp import TOTP
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from utils.Utils import get_server_ip

class ZerodhaLogin(BaseLogin):
    def __init__(self, brokerAppDetails):
        BaseLogin.__init__(self, brokerAppDetails)

    def login(self, args):
        logging.info('==> ZerodhaLogin .args => %s', args);
        systemConfig = getSystemConfig()
        username = self.brokerAppDetails.clientID
        password = self.brokerAppDetails.password
        totp = self.brokerAppDetails.totp
        webdriver_path = self.brokerAppDetails.webdriver_path  # path of your chromedriver

        brokerHandle = KiteConnect(api_key=self.brokerAppDetails.appKey)

        url = brokerHandle.login_url()

        print(url)

        # launch chrome and open zerodha website
        service = Service(webdriver_path)
        service.start()
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920x1080")
        options.add_argument("--remote-debugging-port=9222")
        print("Options Done")
        driver = webdriver.Chrome(service = service, options=options)  # , desired_capabilities=capabilities)
        driver.get(url)
        #driver.get("https://kite.zerodha.com/")
        driver.maximize_window()
        print("Driver Done")
        # input password
        pwd = WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.ID, 'password')))
        pwd.send_keys(password)

        # input username
        user = WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.ID, 'userid')))
        user.send_keys(username)
        print("login done")

        # click on login
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        sleep(1)

        # input totp
        ztotp = driver.find_element(By.ID, 'userid')
        totp_token = TOTP(totp)
        token = totp_token.now()
        ztotp.send_keys(token)

        print("OTP Done")

        # click on continue
        #driver.find_element(By.XPATH, "//button[@class = 'button-orange wide']").click()
        #driver.minimize_window()
        sleep(5)
        url = driver.current_url

        print(url)

        status = url.split('status=')[1]
        status = status.split('&')[0]
        logging.info('status is = %s', status)

        print('status is =%s', status)

        if status == "success":
            initial_token = url.split('request_token=')[1]
            request_token = initial_token.split('&')[0]
            logging.info('Zerodha requestToken = %s', request_token)
            driver.close()

            session = brokerHandle.generate_session(request_token, api_secret=self.brokerAppDetails.appSecret)

            accessToken = session['access_token']
            #accessToken = accessToken
            logging.info('Zerodha accessToken = %s', accessToken)
            brokerHandle.set_access_token(accessToken)

            logging.info('Zerodha Login successful. accessToken = %s', accessToken)

            # set broker handle and access token to the instance
            self.setBrokerHandle(brokerHandle)
            self.setAccessToken(accessToken)

            serverIP = get_server_ip()
            # redirect to home page with query param loggedIn=true
            homeUrl = "http://" + serverIP + ":8080/?loggedIn=true"
            logging.info('Zerodha Redirecting to home page %s', homeUrl)
            redirectUrl = homeUrl
        else:
            loginUrl = brokerHandle.login_url()
            logging.info('Redirecting to zerodha login url = %s', loginUrl)
            redirectUrl = loginUrl

        return redirectUrl

