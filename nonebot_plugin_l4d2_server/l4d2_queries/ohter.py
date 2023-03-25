try:
        import ujson as json
except:
        import json
from pathlib import Path
import os

BOT_DIR = os.path.dirname(os.path.abspath(__file__))
filename = 'data/L4D2/l4d2.json'
global_file = Path(Path(__file__).parent.parent,filename)
def load_josn():
        # 本地模块
        try:
                LOCAL_HOST:dict = json.load(open(
                filename, "r", encoding="utf8"))
        except IOError or FileNotFoundError:
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                data = {}
                with open(filename, "w") as f:
                        json.dump(data, f)
                LOCAL_HOST:dict = {}
        return LOCAL_HOST

ALL_HOST:dict = load_josn()
