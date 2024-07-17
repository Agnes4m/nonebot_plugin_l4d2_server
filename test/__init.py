import httpx
from lxml import etree

response = httpx.get("https://sb.trygek.com/")

# 检查响应状态码
if response.status_code == 200:
    html_content = response.text
    tree: etree._Element = etree.HTML(html_content)
    # print(tree.text)
    # /html/body/main/div[3]/div[5]/div/div/table/tbody/tr[1]
    target_element = tree.xpath("/html/body/main/div[3]/div[5]/div/div/table/tbody/tr")
    server_list = []
    # for tr in target_element:
    for tr in target_element:
        if tr.get("class") != "collapse":
            continue
        for td in tr.xpath("./td"):
            if td.get("id") is not None or td.text == "\n":
                continue
            server_list.append(td.text)
        # result: str = etree.tostring(tr).decode('utf-8')
        # server_list.append(result)
        # 打印目标元素的文本内容
    print(server_list)


else:
    print("Failed to retrieve the page content.")
# print(a2s.info(("gz.trygek.com", 2333)))
