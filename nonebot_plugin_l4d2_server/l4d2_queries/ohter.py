import json
from pathlib import Path


ANNE_HOST:dict = json.load(open(Path(__file__).parent.parent.joinpath(
        'data/L4D2/l4d2.json'), "r", encoding="utf8"))