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

        # launch chrome and open zerodha website
        service = webdriver.chrome.service.Service(f'{webdriver_path}')
        service.start()
        options = webdriver.ChromeOptions()
        driver = webdriver.Chrome(options=options)  # , desired_capabilities=capabilities)
        driver.get(url)
        driver.maximize_window()



        # input password
        pwd = WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.XPATH, "//input[@type='password']")))
        pwd.send_keys(password)

        # input username
        user = WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.XPATH, "//input[@id = 'userid']")))
        user.send_keys(username)

        # click on login
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        sleep(1)

        # input totp
        ztotp = driver.find_element(By.XPATH, "//input[@type = 'number']")
        totp_token = TOTP(totp)
        token = totp_token.now()
        ztotp.send_keys(token)

        # click on continue
        driver.find_element(By.XPATH, "//button[@type = 'submit']").click()
        driver.minimize_window()
        sleep(5)
        url = driver.current_url

        status = url.split('status=')[1]
        status = status.split('&')[0]
        logging.info('status is = %s', status)

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

            # redirect to home page with query param loggedIn=true
            homeUrl = systemConfig['homeUrl'] + '?loggedIn=true'
            logging.info('Zerodha Redirecting to home page %s', homeUrl)
            redirectUrl = homeUrl
        else:
            loginUrl = brokerHandle.login_url()
            logging.info('Redirecting to zerodha login url = %s', loginUrl)
            redirectUrl = loginUrl

        return redirectUrl

