import json
from pathlib import Path

def load_josn():
        ANNE_HOST = json.load(open(Path(__file__).parent.parent.joinpath(
        'data/L4D2/l4d2.json'), "r", encoding="utf8"))
        return ANNE_HOST
global ANNE_HOST
ANNE_HOST:dict = load_josn()