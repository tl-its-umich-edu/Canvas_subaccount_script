# Import the Canvas class
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

# Set up ENV
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'env.json')
try:
    with open(CONFIG_PATH) as env_file:
        ENV = json.load(env_file)
except FileNotFoundError:
    logger.error(f'Configuration file could not be found; please add file "{CONFIG_PATH}".')
    ENV = dict()

# get the API parameters from ENV
API_URL = ENV["API_URL"]
API_KEY = ENV["API_KEY"]

# create an empty dataframe
global_pd= pd.DataFrame()

def get_account_lti_report(account):
    global global_pd

    report_template = {
        "title": "LTI Report",
        "parameters": {
        },
        "report": "lti_report_csv",
        "last_run": "null",
    }

    report = account.create_report(
        "lti_report_csv", parameters=report_template
    )
    # the status will change from "created", to "running", and finally "complete"
    status ='created'
    while(status != 'complete'):
        time.sleep(5)
        report_json = account.get_report(report.report, report.id)
        print(str(report) + report_json.status)
        status = report_json.status

    # now the report process finished
    # get the file download url
    file_url = report_json.file_url
    print(file_url)
    file_urls = file_url.split('/')
    file_id = file_urls[6]
    print(file_id)
    file = canvas.get_file(file_id)
    data = io.StringIO(file.get_contents())
    df = pd.read_csv(data, sep=",")
    df = df.assign(account_name = account.name)
    df = df.assign(account_id = account.id)
    global_pd = global_pd.append(df, ignore_index=True)

def get_sub_account_recursively(account):
    print(f"""current account {account}""")
    subaccounts = account.get_subaccounts()
    for sa in subaccounts:
        get_account_lti_report(sa)
        get_sub_account_recursively(sa)


# Initialize a new Canvas object
canvas = Canvas(API_URL, API_KEY)

accounts = canvas.get_accounts()

for a in accounts:
    print(a)
    get_account_lti_report(a)
    get_sub_account_recursively(a)

# output csv
global_pd.to_csv("./lti_tools_report.csv")

