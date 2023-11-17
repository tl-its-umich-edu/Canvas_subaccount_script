import logging
import os
import time
import json
import datetime

from bs4 import BeautifulSoup
import pandas as pd
from canvasapi import Canvas
from playwright.sync_api import Playwright, sync_playwright, Page, BrowserContext

# Set the logging level to INFO and add date and time to log messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')  

"""
This script will generate a report of all subaccounts and their current theme.
The report will be output to a CSV file in the same directory as the script.
"""
class ThemeReportGenerator:
    # Wait 4 minutes before checking for a new session_url since it expires after 5 minutes
    session_url_cache_time = 1 * 240
    session_url: str = None
    session_url_time: datetime = None
    canvas: Canvas = None
    page: Page = None

    def __init__(self, api_url: str, api_key: str, root_account: int, disable_resources: bool, headless_browser: bool):
        # Initialize a new Canvas object
        self.api_url = api_url
        self.api_key = api_key
        self.root_account = root_account
        self.disable_resources = disable_resources
        self.headless_browser = headless_browser
        self.canvas = Canvas(self.api_url, self.api_key)

    # parse html of subaccount theme page
    # find the active customized theme
    def parse_subaccount_theme(self, account: Canvas) -> None:
        """
        parse html of subaccount theme page
        """
        self.page.goto(f"{self.api_url}/accounts/{account.id}/brand_configs")
        soup = BeautifulSoup(self.page.content(), features="html.parser")
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
                                        self.report_df = pd.concat([self.report_df, theme_df])
        return

    # recursively loop through all subaccounts
    # get the subaccount theme info
    def loop_subaccount(self, account: any) -> None:
        """
        iterating through all subaccounts recursively
        """
        logging.info(f"""current account {account} {account.id}""")
        self.navigate_to_subaccount()
        subaccounts = account.get_subaccounts()
        for sa in subaccounts:
            # recursively loop subaccount
            self.loop_subaccount(sa)
            # get the subaccount theme info
            self.parse_subaccount_theme(sa)

        return

    # Get the session_url from the Canvas API
    # If the session_url is not expired, it will return None to indicate to do nothing
    # If the session_url is not expired, it will return the session_url
    def get_session_url(self) -> str:
        if self.session_url and (time.time() - self.session_url_time) < self.session_url_cache_time:
            # If session_url is cached, return None to indicate to do nothing
            return None

        response = self.canvas._Canvas__requester.request(
            'GET',
            # Return to the accounts/1 page after getting the session_url
            _url=self.canvas._Canvas__requester.original_url + "/login/session_token?return_to=" +
                 self.canvas._Canvas__requester.original_url + "/accounts/" + self.root_account
        )
        # If response.text is json the return the value session_url
        if response.text:
            session_url = response.json().get('session_url')
            self.session_url = session_url
            self.session_url_time = time.time()
            logging.info(session_url)
            return session_url
        else:
            # Log an error that it couldn't get the response_url
            logging.error("Error getting session_url")
            return None

    # Navigate to a subaccount and click the Admin button
    # Will check if the session_url has expired and clear the cookies to create a new session
    def navigate_to_subaccount(self) -> None:
        # Check to see if we need to get or refresh the session url
        session_url = self.get_session_url()
        # If there's a new session URL to hit
        if session_url is not None:
            self.page=self.page.context.new_page()
            self.page.goto(session_url)
            logging.info("Session URL was not none and was hit.")

    # Run the script
    # Will launch a browser and navigate to the subaccount
    def run(self, playwright: Playwright) -> None:

        browser = playwright.chromium.launch(headless=self.headless_browser)
        context = browser.new_context()
        # Enable request interception.
        context.route('**/*', self.route_handler)
        self.page = context.new_page()

        self.navigate_to_subaccount()
        # create an empty dataframe
        self.report_df = pd.DataFrame(
        columns=('account_id', "account_name", "current_theme_name"))

        accounts = self.canvas.get_accounts()
        # search for all Canvas accounts
        for account in accounts:
            # get subaccounts
            self.loop_subaccount(account)
            self.parse_subaccount_theme(account)

            # output csv
            self.report_df.to_csv("./theme_report.csv")

        context.close()
        browser.close()
    
    # Just some optimizations to avoid loading unnecessary resources.
    def route_handler(self, route, request):
        # If the request is for an image, abort the request.
        if self.disable_resources and request.resource_type in ['image', 'stylesheet', 'font', 'media', 'script']:
            route.abort()
        else:
            route.continue_()

with sync_playwright() as playwright:
    # Set up ENV
    import os
    import json

    CONFIG_PATH = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), './env.json')

    try:
        with open(CONFIG_PATH) as env_file:
            ENV = json.load(env_file)
    except FileNotFoundError:
        logging.error(
            f'Configuration file could not be found; please add file "{CONFIG_PATH}".')
        ENV = dict()

    # Get the API parameters from ENV, use these default that may or may not work if not set
    API_URL = ENV.get("API_URL", "https://canvas.example.com")
    API_KEY = ENV.get("API_KEY", "your_api_key_here")
    ROOT_ACCOUNT = ENV.get("ROOT_ACCOUNT", 1)
    DISABLE_RESOURCES = ENV.get("DISABLE_RESOURCES", True)
    HEADLESS_BROWSER = ENV.get("HEADLESS_BROWSER", False)

    generator = ThemeReportGenerator(API_URL, API_KEY, ROOT_ACCOUNT, DISABLE_RESOURCES, HEADLESS_BROWSER)
    generator.run(playwright)