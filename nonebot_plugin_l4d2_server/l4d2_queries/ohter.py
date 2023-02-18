try:
        import ujson as json
except:
        import json
from pathlib import Path
import os
BOT_DIR = os.path.dirname(os.path.abspath(__file__))
filename = 'data/L4D2/l4d2.json'
def load_josn():
        try:
                ANNE_HOST:dict = json.load(open(
                filename, "r", encoding="utf8"))
                return ANNE_HOST
        except IOError or FileNotFoundError:
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                data = {}
                with open(filename, "w") as f:
                        json.dump(data, f)
                ANNE_HOST:dict = {}
global ANNE_HOST
ANNE_HOST:dict = load_josn()