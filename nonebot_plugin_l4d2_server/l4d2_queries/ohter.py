import json
from pathlib import Path
import os
BOT_DIR = os.path.dirname(os.path.abspath(__file__))
def load_josn():
        try:
                ANNE_HOST = json.load(open(
                'data/L4D2/l4d2.json', "r", encoding="utf8"))
                return ANNE_HOST
        except IOError:
                with open('data/L4D2/l4d2.json','w',encoding='utf-8') as f:
                        f.write('{}')
global ANNE_HOST
ANNE_HOST:dict = load_josn()