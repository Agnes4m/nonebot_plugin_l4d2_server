import json
from pathlib import Path
import os
BOT_DIR = os.path.dirname(os.path.abspath(__file__))
def load_josn():
        ANNE_HOST = json.load(open(
        'data/L4D2/l4d2.json', "r", encoding="utf8"))
        return ANNE_HOST
global ANNE_HOST
ANNE_HOST:dict = load_josn()