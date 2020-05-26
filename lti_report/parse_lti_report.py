import pandas as pd
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

# get the LTI report csv file for parsing
df_origin = pd.read_csv("./lti_tools_report.csv", header=0)
print(df_origin.shape)
df = df_origin.loc[(
    df_origin["tool_type_id"] != "redirect") 
    & ~df_origin.launch_url.str.contains("https://www.edu-apps.org/", regex= True, na=False) # filter out edu-apps tools
    & ~df_origin.launch_url.str.contains("localhost", regex= True, na=False) # filter out localhost tools
    & ~df_origin["tool_type_name"].isnull()
    & ~df_origin["launch_url"].isnull()
    ]
df["name_url"] = df["tool_type_name"] + "|" + df["launch_url"]
print(df.shape)
df.to_csv("./filtered_lti_tools_report.csv")

df_root = df[df["account_id"] == 1]

# unique value in name_url column
root_name_url_unique = df_root.name_url.unique().astype(str) 
name_url_list = sorted(root_name_url_unique)
df_root.to_csv("./root_account_name_url_list.csv")

# unique value in url column
root_url_unique = df_root.launch_url.unique().astype(str) 
url_list = sorted(root_url_unique)
df_root.to_csv("./root_account_url_list.csv")

print("########")

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

global_pd= pd.DataFrame()

# Initialize a new Canvas object
canvas = Canvas(API_URL, API_KEY)

root_account = canvas.get_account(1)
accounts = root_account.get_subaccounts(recursive=True)
for account in accounts:
    print(account)
    # get the LTI report for current account
    df_account= pd.DataFrame()
    df_account = df[df["account_id"] == account.id]
    print(df_account)
    for index, row in df_account.iterrows():
        print(row['name_url'])

        # if the name_url combination is not shown in parent installation yet
        # add new name_url value
        if row['name_url'] not in name_url_list:
            print("added " + account)
            name_url_list.append(row['name_url'])
        else:
            print("found")

        # if the lauch_url is not in the parent account installation yet
        # add new lauch_url valaue
        if row['launch_url'] not in url_list:
            print("added " + account)
            url_list.append(row['name_url'])
        else:
            print("found")

# output csv for the name_url list
df_name_url_final = pd.DataFrame(data={"LTI": name_url_list})
df_name_url_final.to_csv("./unique_name_url_lti.csv", sep=',',index=False)
print(f"""name_url list length {len(name_url_list)}""")

# output csv for the url list
df_url_final = pd.DataFrame(data={"LTI": url_list})
df_url_final.to_csv("./unique_url_lti.csv", sep=',',index=False)
print (f"""launch url list length {len(url_list)}""")