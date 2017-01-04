import logging.config
import os
import yaml


def setup_logging(path='logging.yaml',
                  level=logging.INFO,
                  env_key='LOG_CFG'):

    log_file_path = os.getenv(env_key, path)
    if log_file_path and os.path.exists(log_file_path):
        with open(log_file_path, 'rt') as f:
            config = yaml.load(f.read())
            """
            logging.config.dictConfig(config)
            """
    else:
        logging.basicConfig(level=level)
