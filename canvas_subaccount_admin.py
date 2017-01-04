
import logging
import urllib
import utils
import requests
import json



"""
This class makes the api calls to find subaccount admins from Canvas
"""
HTTP_METHOD_POST = 'Post'
HTTP_METHOD_GET = 'Get'
AUTHORIZATION = 'Authorization'
BEARER = 'Bearer '
MIME_TYPE_JSON = 'application/json'
CONTENT_TYPE = 'Content-type'

canvas_token = ""
canvas_url = "https://umich.instructure.com"

def get_admins():
    """
    get Users in a section, In case of exceptions it throws it to calling method
    :param section_id:
    :param next_page_url:
    :type section_id: str
    :type next_page_url: str
    :return: response
    :rtype: requests
    """
    url = canvas_url + '/api/v1/accounts/1/admins?per_page=100'
    try:
        response = make_api_call(url, HTTP_METHOD_GET)
        admins = json.loads(response.content.decode('utf-8'))
        count = 0
        print ('-----------Account Admins-----------------')
        for admin in admins:
            print(admin['user']['name']+ "\t" + admin['role'] + "\t" + admin['user']['login_id'] + "@umich.edu")
    except:
        raise

    return response

def get_subaccount_admin(account_id, level):
    """
    get Users in a section, In case of exceptions it throws it to calling method
    :param section_id:
    :param next_page_url:
    :type section_id: str
    :type next_page_url: str
    :return: response
    :rtype: requests
    """
    indentation = '\t'
    for num in range(0,level):
        indentation += '\t'
    url = canvas_url + '/api/v1/accounts/' + str(account_id) + '/sub_accounts?per_page=100'
    try:
        response = make_api_call(url, HTTP_METHOD_GET)
        subaccounts = json.loads(response.content.decode('utf-8'))
        count = 0
        for subaccount in subaccounts:
            count +=1

            print ('----------------------------')
            """
            print(json.dumps(subaccount, indent=4, sort_keys=True))
            """
            print(indentation + 'subaccount name:\t' + subaccount['name'] + ' \taccount id:\t'  + str(subaccount['id']))
            url = canvas_url + '/api/v1/accounts/' + str(subaccount['id']) + '/admins?per_page=100'
            try:
                admin_response = make_api_call(url, HTTP_METHOD_GET)
                subaccount_admins = json.loads(admin_response.content.decode('utf-8'))
                for subaccount_admin in subaccount_admins:
                    print(indentation + subaccount_admin['user']['name']+ "\t" + subaccount_admin['role'] + "\t" + subaccount_admin['user']['sis_login_id'] + "@umich.edu")
            except:
                continue

            """
            recursively call subaccount
            """
            get_subaccount_admin(subaccount['id'], level+1)
    except:
        raise

    return response

def make_api_call(url, http_method):
    """
    bubbles up the exception to be caught and handled by original calling function
    :param url:
    :param http_method:
    :type url:str
    :type http_method: str
    :return: response
    :rtype: requests
    """
    try:
        response = api_handler(url, http_method)
    except:
        raise

    return response

def api_handler( url, request_type):
    logging.debug(api_handler.__name__ + '() called')
    logging.info('URL: ' + url)
    response = None
    headers = {CONTENT_TYPE: MIME_TYPE_JSON, AUTHORIZATION: BEARER + canvas_token}
    try:
        if request_type == HTTP_METHOD_GET:
            response = requests.get(url, headers=headers)
            """
            print(response.content)
            """
            logging.info('Link headers: ' + str(response.links))
    except (requests.exceptions.RequestException, Exception) as exception:
        raise exception

    return response

def main():
    utils.setup_logging()
    logging.info('Script Started')
    get_admins()
    get_subaccount_admin(1, 0)

if __name__ == '__main__':
    main()