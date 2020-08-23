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
import logging

logger = logging.getLogger(__name__)

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
# LTI tool name
LTI_TOOL_NAME = ENV["LTI_TOOL_NAME"]
# set term ids
enrollment_term_ids = ENV["ENROLLMENT_TERM_IDS"] # 127: Fall 2019; 164: Winter 2020; 167: Spring 2020

# create an empty dataframe
global_pd= pd.DataFrame(columns=('course_name', "course_id", "teachers", "term_id", "account_id", "account_name", 'tab_name'))

def get_course_lti_tab(account, enrollment_term_ids):
    """
        get all courses with LTI tool installation for the given term range
    """
    global global_pd

    print(f"""current account {account}""")

    print(account.id)
    # get all courses in the account
    courses: List[canvasapi.course.Course] = []
    for enrollment_term_id in enrollment_term_ids:
        print(f"term id = {enrollment_term_id}")
        logger.info(f'Fetching published course data for term {enrollment_term_id}')
        logger.info(f'account = {account}')
        courses_list = list(
            account.get_courses(
                enrollment_term_id=enrollment_term_id,
                published=True
            )
        )
        print(f'length of courses = {len(courses_list)}')
        # get LTI tool in those sites
        for course in courses_list:
            if not course.id in global_pd.course_id.values:
                # new course id
                #print(f"course {course}")
                for tab in course.get_tabs():
                    tab_label = ""
                    try:
                        if not hasattr(tab, "hidden"):
                            tab_label = tab.label.lower()
                            if tab_label in LTI_TOOL_NAME:
                                print(f"term id={enrollment_term_id} course={course} tab={tab_label}")
                                # get teachers
                                teacher_str = ""
                                teachers = course.get_users(enrollment_type=['teacher'])
                                for teacher in teachers:
                                    teacher_name = getattr(teacher,'name', "")
                                    teacher_id = getattr(teacher,'login_id', "")
                                    teacher_str = teacher_str + teacher_name + "(" + teacher_id + "),"
                                    print(teacher_str)

                                course_dict = {'course_name': course.name, 
                                            "course_id":course.id, 
                                            'term_id': enrollment_term_id,
                                            'teachers': teacher_str,
                                            'account_id': account.id,
                                            'account_name': account.name,
                                            'tab_name': tab_label}
                                # added to output dataframe
                                global_pd = global_pd.append(course_dict, ignore_index=True)
                                global_pd.to_csv("./lti_tools_report.csv")
                    except ValueError as e:
                        print ("not valid json")

def get_sub_account_recursively(account, enrollment_term_ids):
    print(f"""current account {account} {account.id}""")
    subaccounts = account.get_subaccounts()
    for sa in subaccounts:
        get_sub_account_recursively(sa, enrollment_term_ids)
        get_course_lti_tab(sa, enrollment_term_ids)

# Initialize a new Canvas object
canvas = Canvas(API_URL, API_KEY)
accounts = canvas.get_accounts()

# search for all Canvas accounts
for account in accounts:
    # get LTI tool in those listed courses
    get_sub_account_recursively(account, enrollment_term_ids)
    get_course_lti_tab(account, enrollment_term_ids)

# output csv
global_pd.to_csv(f"./lti_tools_report.csv")

