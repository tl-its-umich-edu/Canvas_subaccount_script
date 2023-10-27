## Installation instructions

- install required libraries
  `pip install --no-cache-dir -r requirements.txt`

- Install the required browsers:
  `playwright install`

- copy env_sample.json to env.json, and add proper values to those env variables:
  `cp env_sample.json env.json`

- execute the script to generate theme_report.csv file:
  `python3 ./generate_theme_report.py`
