"""Module to read config file."""

import json
import os

from maintainability import log

SCRIPT_DIR = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(SCRIPT_DIR, './config.json')

def get(property):
    """Get value of a configuration property."""
    with open(CONFIG_PATH) as config_file:
        config = json.load(config_file)
        value = config.get(property)
        if not value:
            log.warning("No config value found for {}.".format(property))
        return value
