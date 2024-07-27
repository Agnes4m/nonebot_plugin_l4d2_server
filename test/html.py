from typing import List

import requests
from bs4 import BeautifulSoup

url = "https://sb.trygek.com/l4d_stats/ranking/search.php"
response = requests.post(
    url,
    # headers={
    #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
    #     "Content-Type": "application/x-www-form-urlencoded",
    # },
    data={"search": "小可学"},
)
response.raise_for_status()  # 如果响应状态码不是 200，将抛出 HTTPError 异常
soup = BeautifulSoup(response.content.decode("utf-8"), "html.parser")

table_elements: List[BeautifulSoup] = soup.find_all("table")

for table in table_elements:
    # 遍历<table>下的所有<tr>
    print(type(table))
    print(table.text)
    for tr in table.xpath("./tr"):
        # 遍历<tr>下的所有<td>
        for td in tr.xpath("./td"):
            # 提取<td>的文本内容
            text = td.text.strip() if td.text else ""
            print(text)  # 或者做其他处理
