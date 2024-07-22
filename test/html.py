import httpx
from lxml import etree

url = "https://sb.trygek.com/l4d_stats/"
msg = httpx.get(
    url,
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
    },
)
tree = etree.HTML(msg.text, parser=etree.HTMLParser(encoding="utf-8"))
all_msg = tree.xpath("/html/body/div[6]/div/div[4]/div/h5/text()")

for tr in all_msg:
    print(type(str(tr)))
    print(tr)
