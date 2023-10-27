from playwright.sync_api import Playwright, sync_playwright

from bs4 import BeautifulSoup

from canvasapi import Canvas
import pandas as pd

import os
import json
import logging
import time

import sys

logging.basicConfig(level=logging.INFO)  # Set the logging level to INFO

def parse_subaccount_theme(account, page, API_URL, report_df):
    """
    parse html of subaccount theme page
    """
    page.goto(f"{API_URL}/accounts/{account.id}/brand_configs")
    soup = BeautifulSoup(page.content(), features="html.parser")
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
                                    theme_df = pd.DataFrame(data={'account_id': [account.id],
                                                  "account_name": [account.name],
                                                  'current_theme_name': [theme["name"]]})
                                    logging.info(f'{account.id};  {account.name}; {theme["name"]}')
                                    report_df = pd.concat([report_df, theme_df])
    return report_df


def loop_subaccount(account, page, API_URL, report_df):
    """
    iterating through all subaccounts recursively
    """
    logging.info(f"""current account {account} {account.id}""")
    subaccounts = account.get_subaccounts()
    for sa in subaccounts:
        # recursively loop subaccount
        report_df = loop_subaccount(sa, page, API_URL, report_df)

        # get the subaccount theme info
        report_df = parse_subaccount_theme(sa, page, API_URL, report_df)

    return report_df

def get_session_url(canvas):
    response = canvas._Canvas__requester.request(
        'GET', 
        _url = canvas._Canvas__requester.original_url + "/login/session_token"
    )
    # If response.text is json the return the value session_url
    if response.text:
        session_url = response.json().get('session_url')
        return session_url
    else:
        # Log an error that it couldn't get the response_url
        logging.error("Error getting session_url")
        return None

def run(playwright: Playwright) -> None:
    # Set up ENV
    CONFIG_PATH = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), './env.json')
    try:
        with open(CONFIG_PATH) as env_file:
            ENV = json.load(env_file)
    except FileNotFoundError:
        logging.error(
            f'Configuration file could not be found; please add file "{CONFIG_PATH}".')
        ENV = dict()

    # get the API parameters from ENV
    API_URL = ENV["API_URL"]
    API_KEY = ENV["API_KEY"]

    # Initialize a new Canvas object
    canvas = Canvas(API_URL, API_KEY)
    session_url = get_session_url(canvas)

    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto(session_url)
    page.get_by_role("button", name="Admin").click()
    page.get_by_role("link", name="University of Michigan - Ann Arbor").click()
    # create an empty dataframe
    report_df = pd.DataFrame(
    columns=('account_id', "account_name", "current_theme_name"))
    
    accounts = canvas.get_accounts()
    # search for all Canvas accounts
    for account in accounts:
        # get subaccounts
        report_df = loop_subaccount(account, page, API_URL, report_df)
        report_df = parse_subaccount_theme(account, page, API_URL, report_df)

        # output csv
        report_df.to_csv("./theme_report.csv")
        
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)