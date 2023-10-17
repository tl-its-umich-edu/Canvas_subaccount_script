from playwright.sync_api import Playwright, sync_playwright

from bs4 import BeautifulSoup

from canvasapi import Canvas
import pandas as pd
import os
import json
import logging
import time

logger = logging.getLogger(__name__)


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
                                    print(f'{account.id};  {account.name}; {theme["name"]}')
                                    report_df = pd.concat([report_df, theme_df])
    return report_df


def loop_subaccount(account, page, API_URL, report_df):
    """
    iterating through all subaccounts recursively
    """
    print(f"""current account {account} {account.id}""")
    subaccounts = account.get_subaccounts()
    for sa in subaccounts:
        # recursively loop subaccount
        report_df = loop_subaccount(sa, page, API_URL, report_df)

        # get the subaccount theme info
        report_df = parse_subaccount_theme(sa, page, API_URL, report_df)

    return report_df

def run(playwright: Playwright) -> None:
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
    print(CANVAS_USER)
    print(CANVAS_PASSWORD)

    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://canvas.it.umich.edu/")
    page.get_by_role("link", name="U-M Login U-M Weblogin U-M Faculty, Staff, Students and Friends Use your U-M login credentials or Friend account email address and password").click()
    page.get_by_placeholder("Uniqname or Friend ID").click()
    page.get_by_placeholder("Uniqname or Friend ID").fill(CANVAS_USER)
    page.get_by_placeholder("Uniqname or Friend ID").press("Tab")
    page.get_by_placeholder("Password").fill(CANVAS_PASSWORD)
    page.get_by_role("button", name="Log In").click()
    page.frame_locator("#duo_iframe").get_by_role("button", name="Send Me a Push").click()
    time.sleep(10)
    page.goto("https://weblogin.umich.edu/idp/profile/SAML2/POST/SSO?execution=e1s2")
    page.goto("https://shibboleth.umich.edu/idp/profile/SAML2/Redirect/SSO?execution=e1s1&_eventId_proceed=1")
    page.goto("https://umich.instructure.com/")
    page.get_by_role("button", name="Admin").click()
    page.get_by_role("link", name="University of Michigan - Ann Arbor").click()

    # Initialize a new Canvas object
    canvas = Canvas(API_URL, API_KEY)
    accounts = canvas.get_accounts()
    print(accounts)

    # create an empty dataframe
    report_df = pd.DataFrame(
    columns=('account_id', "account_name", "current_theme_name"))
    
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