import logging.config
import yaml


def setup_logging():
    with open("logging.yaml", "r") as f:
        config = yaml.safe_load(f)
    logging.config.dictConfig(config)
