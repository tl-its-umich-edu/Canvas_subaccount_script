from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0
from bs4 import BeautifulSoup

from canvasapi import Canvas, file
from canvasapi.account import (
    Account,
    AccountNotification,
    AccountReport,
    Admin,
    Role,
    SSOSettings,
)
import time
import pandas as pd
import io, os, json
import logging

# Set up ENV
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), './env.json')
try:
    with open(CONFIG_PATH) as env_file:
        ENV = json.load(env_file)
except FileNotFoundError:
    logger.error(f'Configuration file could not be found; please add file "{CONFIG_PATH}".')
    ENV = dict()

# get the API parameters from ENV
API_URL = ENV["API_URL"]
API_KEY = ENV["API_KEY"]

# used for login page
CANVAS_USER = ENV["CANVAS_USER"]
CANVAS_PASSWORD = ENV["CANVAS_PASSWORD"]

# Initialize the driver
driver = webdriver.Chrome()

# Open provided link in a browser window using the driver
driver.get(API_URL +"/login/saml")
driver.execute_script(f"document.getElementById('login').value = '{CANVAS_USER}';")
driver.execute_script(f"document.getElementById('password').value = '{CANVAS_PASSWORD}';")
loginSubmit = driver.find_element_by_id('loginSubmit')
loginSubmit.click()

# create an empty dataframe
global_pd= pd.DataFrame(columns=('account_id', "account_name", "current_theme_name"))

def parse_subaccount_theme(account):
    """
        get account theme
    """
    global global_pd

    driver.get(f"{API_URL}/accounts/{account.id}/brand_configs")
    element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "left-side")))
    element = driver.find_element_by_xpath('//*')
    innerHtml = element.get_attribute('innerHTML')
    soup = BeautifulSoup(innerHtml, features="html.parser")

    for script in soup.find_all('script'):
        for content in script.contents:
            if "ENV =" in content:
                parts = content.split(";")
                for part in parts:
                    if "ENV = " in part:
                        env_json = json.loads(part.replace("ENV =", ""))

                        # find the active customized theme
                        if env_json["brandConfigStuff"] != None and env_json["brandConfigStuff"]["activeBrandConfig"] != None:
                            active_theme_md5 = env_json["brandConfigStuff"]["activeBrandConfig"]["md5"]
                            for theme in env_json["brandConfigStuff"]["sharedBrandConfigs"]:
                                if theme["brand_config"] != None and theme["brand_config"]["md5"] != None and theme["brand_config"]["md5"] == active_theme_md5:
                                    # find the current theme, and added to output dataframe
                                    print(theme)
                                    theme_dict = {'account_id': account.id, 
                                            "account_name":account.name, 
                                            'current_theme_name': theme["name"]}
                                    global_pd = global_pd.append(theme_dict, ignore_index=True)


# iterating through all subaccounts recursively
def loop_subaccount(account):
    print(f"""current account {account} {account.id}""")
    subaccounts = account.get_subaccounts()
    for sa in subaccounts:
        loop_subaccount(sa)
        parse_subaccount_theme(sa)

# Initialize a new Canvas object
canvas = Canvas(API_URL, API_KEY)
accounts = canvas.get_accounts()

# search for all Canvas accounts
for account in accounts:
    # get LTI tool in those listed courses
    loop_subaccount(account)
    parse_subaccount_theme(account)

# output csv
global_pd.to_csv("./theme_report.csv")