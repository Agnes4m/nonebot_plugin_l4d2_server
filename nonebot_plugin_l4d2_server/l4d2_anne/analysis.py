from .startand import SAVE_MAP,NUMBER_MAP
import pandas as pd

async def df_to_guoguanlv(df:pd.DataFrame):
    """分析救援关过图率"""
    data = df
    all_map = len(data['地图'])
    resen = 0
    last_maps = {}
    for m in SAVE_MAP:
        prefix = m.split('m')[0]
        if prefix in last_maps:
            last_maps[prefix] = max(last_maps[prefix], m)
        else:
            last_maps[prefix] = m

    map_counts = {}

    n = 0
    for key in last_maps:
        count = len(data[data['地图'].str.startswith(key)])
        if count == 0:
            continue
        last_map = last_maps[key]
        map_count = len(data[data['地图'] == last_map])
        map_counts[key] = map_count*NUMBER_MAP[n] / count
        quan = count/all_map
        resen += quan * map_counts[key]
        n += 1

    # result = []
    # for i in range(1, 15):
    #     key = 'c{}'.format(i)
    #     if key in map_counts:
    #         result.append('{}:{}%'.format(key, round(map_counts[key] * 100)))
            
    # print(result)
    # result = '救援图过关率: {:.2%}'.format(resen)
    result = {"救援关":str(resen)}
    return result