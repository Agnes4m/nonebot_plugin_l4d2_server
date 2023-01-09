try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
except:
    pass
url = 'https://server.trygek.com/index.php'


def get_anne_server():
    chrome_options = Options()  
    chrome_options.add_argument('--no-sandbox') #“–no-sandbox”参数是让Chrome在root权限下跑
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('-ignore-certificate-errors')
    chrome_options.add_argument('--headless') #“–headless”参数是不用打开图形界面  
    driver = webdriver.Chrome(chrome_options=chrome_options) 
    print('启动成功')
    # browser.get(url)
    # browser.add_cookie({'name':'token','value':token_value})
    driver.get(url)
    print('网页已打开，正在浏览')
    i = 0
    n = 1
    msg = ''
    while i <= 40:
        try:
            i += 1
            mes =''
            xpath1 = '//*[@id="host_{}"]'.format(i)
            xpath2 = '/html/body/main/div[3]/div[5]/div/div/table/tbody/tr[{}]/td[5]'.format(n)
            xpath3 = '//*[@id="players_{}"]'.format(i)
            xpath4 = '//*[@id="map_{}"]'.format(i)
            xpath = [xpath1,xpath2,xpath3,xpath4]
            names = ['服务器名称','服务器ip','玩家','地图']
            for x in range(5):
                name:str = driver.find_element(By.XPATH,xpath[x-1]).text
                mes += names[x-1] + '' + name + '\n'
            msg += mes
            msg += '--------------------\n'
            n += 2
        except :
            continue
    return msg
  