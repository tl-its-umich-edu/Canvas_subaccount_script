## Installation instructions

- install [Playwright for Python](https://playwright.dev/python/docs/intro):
  Install the Pytest plugin:
  `pip install pytest-playwright`

  Install the required browsers:
  `playwright install`

- install beautifulsoup
  `pip install bs4`

## Run script

- copy env_sample.json to env.json, and add proper values to those env variables:
  `cp env_sample.json env.json`

- install canvasapi library 
`python3 -m pip install canvasapi`


- execute the script to generate theme_report.csv file:
  `python3 ./generate_theme_report.py`
