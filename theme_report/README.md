## Installation instructions

- install required libraries
  `pip install --no-cache-dir -r requirements.txt`

- Install the required browsers:
  `playwright install`

- copy env_sample.json to env.json, and add proper values to those env variables:
  `cp env_sample.json env.json`

- execute the script to generate theme_report.csv file:
  `python3 ./generate_theme_report.py`

## Variables used in env.json

* `API_URL` (str): Full API URL of the instance where API_KEY was generated starting with https://
* `API_KEY` (str): API Key generated from Canvas settings for an admin account
* `ROOT_ACCOUNT` (int): Root account number
* `DISABLE_RESOURCES` (bool): Set or disable resources retrieval to improve speed
* `HEADLESS_BROWSER` (bool): Set or disable headless browsing 