import json

with open('./key/keys.json') as f:
    keys = json.load(f)

API_KEY: list = keys['API_KEY']


def auth(key: str):
    if key in API_KEY:
        return True
    else:
        return False
