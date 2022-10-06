from canvasapi import Canvas
import pandas as pd
import os
import json
import logging

logger = logging.getLogger(__name__)


def parse_subaccount_theme(account, driver, API_URL, report_df):
    """
    parse html of subaccount theme page
    """
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


def loop_subaccount(account, driver, API_URL, report_df):
    """
    iterating through all subaccounts recursively
    """
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

    # create an empty dataframe
    report_df = pd.DataFrame(
       columns=("date_run", "course_id", "course_name", "account_id", "account_name", "user_id", "user_login_id", "user_name", "errors", "suggestions"))
    
    input_df = pd.read_csv("heroku_udoit_report.csv")
    print(input_df.shape)

    # Initialize a new Canvas object
    canvas = Canvas(API_URL, API_KEY)
    accounts = canvas.get_accounts()

    # search for all Canvas accounts
    for index, row in input_df.iterrows():
        course_id = row['course_id']
        user_id = row['user_id']
        try:
            # course name
            course = canvas.get_course(course_id)
            course_name = course.name

            # course account name
            course_account_id = course.account_id
            account = canvas.get_account(course_account_id)
            account_name = account.name

            # user info
            user = canvas.get_user(user_id)
            user_login_id = user.login_id
            user_name = user.name

            course_dict = {'date_run': row['date_run'],
                        'course_id': course_id,
                        'course_name': course_name,
                        'account_id': course_account_id,
                        'account_name': account_name,
                        'user_id': user_id,
                        'user_login_id': user_login_id,
                        'user_name': user_name,
                        'errors': row['errors'],
                        'suggestions': row['suggestions']
            }
            new_df = pd.DataFrame([course_dict])
            report_df = pd.concat([report_df, new_df], axis=0, ignore_index=True)
        except Exception as e:
            print(f'Exception with {course_id} {user_id} {e.__class__}')
    
    # output csv
    report_df.to_csv("./udoit_report.csv")


if '__main__' == __name__:
    main()
