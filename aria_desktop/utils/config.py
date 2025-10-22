import configparser
from pathlib import Path

def load_config():
    config = configparser.ConfigParser()
    config_path = Path(__file__).parent.parent.parent / 'config.ini'
    config.read(config_path)
    return config

config = load_config()