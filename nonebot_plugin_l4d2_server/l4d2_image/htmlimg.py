

class DATA_PANDS:
    async def __init__(
        self,
        data_dict:dict
        ) -> None:
        self.new_data = {[]}
        self.data_dict = data_dict
        for key,value in data_dict.items():
            self.dict_pan(key)
        
    
    
    async def dict_pan(self,key):
        """dict转化为图像所需要的dict量化"""
        # 删除不必要是数据
        if key in ['刷特模式']:
            for item in self.data_dict[key]:
                if item == '固定刷特':
                    self.data_dict.pop(item)
        elif key in ['游戏模式']:
            for item in self.data_dict[key]:
                if item in self.new_data:
                    self.new_data[item] += 1
                else:
                    self.new_data[item] = 1
        elif key in ['特感数量','刷新间隔']:
            for item in self.data_dict[key]:
                if item in self.new_data:
                    self.new_data[item] += 1
                else:
                    self.new_data[item] = 1