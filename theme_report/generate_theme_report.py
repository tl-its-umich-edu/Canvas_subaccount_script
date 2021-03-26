from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait  # available since 2.4.0
# available since 2.26.0
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

from canvasapi import Canvas
import pandas as pd
import os
import json
import logging

logger = logging.getLogger(__name__)

# parse html of subaccount theme page


def parse_subaccount_theme(account, driver, API_URL, report_df):
    print(f"parse subaccount {account}")
    driver.get(f"{API_URL}/accounts/{account.id}/brand_configs")
    element = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.ID, "left-side")))
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
                        if (env_json["brandConfigStuff"] is not None and env_json["brandConfigStuff"]["activeBrandConfig"] is not None):
                            active_theme_md5 = env_json["brandConfigStuff"]["activeBrandConfig"]["md5"]
                            for theme in env_json["brandConfigStuff"]["sharedBrandConfigs"]:
                                if (theme["brand_config"] is not None and theme["brand_config"]["md5"] is not None and theme["brand_config"]["md5"] == active_theme_md5):
                                    # find the current theme, and added to output dataframe
                                    print(theme)
                                    theme_dict = {'account_id': account.id,
                                                  "account_name": account.name,
                                                  'current_theme_name': theme["name"]}
                                    report_df = report_df.append(
                                        theme_dict, ignore_index=True)
    return report_df


# iterating through all subaccounts recursively
def loop_subaccount(account, driver, API_URL, report_df):
    print(f"""current account {account} {account.id}""")
    subaccounts = account.get_subaccounts()
    for sa in subaccounts:
        report_df = loop_subaccount(sa, driver, API_URL, report_df)
        report_df = parse_subaccount_theme(sa, driver, API_URL, report_df)
        print(f"{report_df.shape}")

    return report_df


def main():
    # Set up ENV
    CONFIG_PATH = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), './env.json')
    try:
        with open(CONFIG_PATH) as env_file:
            ENV = json.load(env_file)
    except FileNotFoundError:
        logger.error(
            f'Configuration file could not be found; please add file "{CONFIG_PATH}".')
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
    driver.get(API_URL + "/login/saml")
    driver.execute_script(
        f"document.getElementById('login').value = '{CANVAS_USER}';")
    driver.execute_script(
        f"document.getElementById('password').value = '{CANVAS_PASSWORD}';")
    loginSubmit = driver.find_element_by_id('loginSubmit')
    loginSubmit.click()

    # create an empty dataframe
    report_df = pd.DataFrame(
        columns=('account_id', "account_name", "current_theme_name"))

    # Initialize a new Canvas object
    canvas = Canvas(API_URL, API_KEY)
    accounts = canvas.get_accounts()

    # search for all Canvas accounts
    for account in accounts:
        # get subaccounts
        report_df = loop_subaccount(account, driver, API_URL, report_df)
        report_df = parse_subaccount_theme(account, driver, API_URL, report_df)

    # output csv
    report_df.to_csv("./theme_report.csv")


if '__main__' == __name__:
    main()
