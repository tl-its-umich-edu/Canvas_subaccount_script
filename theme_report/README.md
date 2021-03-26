## Installation instructions

- install [selenium](https://selenium-python.readthedocs.io/getting-started.html):
  `pip install selenium`

- install beautifulsoup
  `pip install bs4`
- Install chromedrive:
  `brew install chromedriver`

- upgrade chromedrive if needed:
  `brew upgrade chromedriver`

## Run script

- copy env_sample.json to env.json, and add proper values to those env variables:
  `cp env_sample.json env.json`

- execute the script to generate theme_report.csv file:
  `python ./generate_theme_report.py`
