from datetime import datetime
import json


def pretty_time(timestamp):
    """ Prints out readable date/times """
    if not timestamp:
        return None
    return datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')  # blabla asdfasaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa


def load_config_file(filename='./config.json'):
    """ Loads credentials from config file """
    with open(filename, 'r') as f:
        config = json.load(f)

    return (config[0]['ssh']['username'],
            config[0]['ssh']['password'],
            config[0]['snmp']['community'],
            config[0]['http_api']['host'],
            config[0]['http_api']['port'])
