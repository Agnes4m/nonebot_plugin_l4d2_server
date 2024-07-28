import json
from pathlib import Path
from typing import Dict, List

filename = Path("data/L4D2/l4d2.json")
global_file = Path(Path(__file__).parent.parent, filename)


def load_ip_json():
    # 本地模块
    local_host: Dict[str, List[Dict[str, str]]] = {}
    try:
        # 获取所有json文件的路径
        json_files = Path("data/L4D2/l4d2").glob("*.json")

        # 将所有json文件中的字典对象合并为一个字典
        for file_path in json_files:
            try:
                with file_path.open("r", encoding="utf-8") as f:
                    local_host.update(json.load(f))
            except Exception:
                print("导入错误", file_path)
    except Exception:
        pass
    return local_host


def load_group_json():
    try:
        group_host: Dict[str, List[str]] = json.load(
            filename.open("r", encoding="utf8"),
        )
    except (IOError, FileNotFoundError):
        filename.parent.mkdir(parents=True, exist_ok=True)
        data: Dict[str, List[str]] = {"anne": ["云"]}
        with filename.open("w") as f:
            json.dump(data, f)
        group_host: Dict[str, List[str]] = {}
    return group_host


ALL_HOST: Dict[str, List[Dict[str, str]]] = load_ip_json()
Group_All_HOST: Dict[str, List[str]] = load_group_json()
