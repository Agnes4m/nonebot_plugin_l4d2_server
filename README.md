<div align="center">
  <img src="https://raw.githubusercontent.com/Agnes4m/nonebot_plugin_l4d2_server/main/image/logo.png" width="180" height="180"  alt="AgnesDigitalLogo">
  <br>
  <p><img src="https://s2.loli.net/2022/06/16/xsVUGRrkbn1ljTD.png" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot_plugin_l4d2_server
_✨Nonebot & Left 4 Dead 2 server操作✨_
<div align = "center">
        <a href="https://github.com/Agnes4m/nonebot_plugin_l4d2_server/wiki/%E6%96%87%E6%A1%A3" target="_blank">文档</a> &nbsp; · &nbsp;
        <a href="https://github.com/Agnes4m/nonebot_plugin_l4d2_server/wiki/%E6%96%87%E6%A1%A3#zl" target="_blank">指令列表</a> &nbsp; · &nbsp;
        <a href="https://github.com/Agnes4m/nonebot_plugin_l4d2_server/wiki/BUG%E5%8F%8D%E9%A6%88">常见问题</a>
</div><br>
<a href="https://github.com/Agnes4m/nonebot_plugin_l4d2_server/stargazers">
        <img alt="GitHub stars" src="https://img.shields.io/github/stars/Agnes4m/nonebot_plugin_l4d2_server" alt="stars">
</a>
<a href="https://github.com/Agnes4m/nonebot_plugin_l4d2_server/issues">
        <img alt="GitHub issues" src="https://img.shields.io/github/issues/Agnes4m/nonebot_plugin_l4d2_server" alt="issues">
</a>
<a href="https://jq.qq.com/?_wv=1027&k=HdjoCcAe">
        <img src="https://img.shields.io/badge/QQ%E7%BE%A4-399365126-orange?style=flat-square" alt="QQ Chat Group">
</a>
<a href="https://pypi.python.org/pypi/nonebot_plugin_l4d2_server">
        <img src="https://img.shields.io/pypi/v/nonebot_plugin_l4d2_server.svg" alt="pypi">
</a>
<a href="https://pypi.python.org/pypi/nonebot_plugin_l4d2_server">
    <img src="https://img.shields.io/pypi/dm/nonebot_plugin_l4d2_server" alt="pypi download">
</a>
    <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="python">
    <img src="https://img.shields.io/badge/nonebot-2.0.0rc3-red.svg" alt="NoneBot">
</div>


## 快速使用（env示例）
    # 复制到env文件里，没有默认就是下列值，如需修改安装下面env设置
    # 所有的多选，用逗号隔开
    l4_master = ['1145149191']            # 允许上传地图的qq号
    l4_file = ['/home/ubuntu/l4d2/coop']  # 本地服务器路径
    l4_host = ['127.0.0.1']               # 服务器ip（建议内网，公网也可以）
    l4_port = ['20715']                   # 服务器端口
    l4_rcon = ['1145149191810']           # 服务器rcon密码，如果没有可以列空str对象元素
    l4_font = 'simsun.ttc'                # 服务器字体


## 新文档（暂未完成）

[点击这里](https://Agnes4m.github.io/l4d2)

<h2 id="gn">主要功能</h2>

- 求生服务器-本地多路径操作（传地图）
- 批量查询指定ip服务器状态和玩家
- 创意工坊下载和喷漆制作
- [求生电信服anne](https://github.com/fantasylidong/CompetitiveWithAnne)[查询~](https://sb.trygek.com/l4d_stats/ranking/index.php)


<h2 id="gn">如何获取key</h2>

为了使得ip不被滥用，我采取这种方式管理。

这并不影响正常使用，如果不需要可以忽略

[点击这里加群](https://jq.qq.com/?_wv=1027&k=HdjoCcAe)并在群内发送“申请求生key”
如果你只查询自己的服务器ip则可以忽略如下，并且更改env设置：

        l4_tag = ['呆呆','橘']      # 这里是内置可以查询的服的list对象
        l4_key = 'qwertyuiopasdfg'  # 这里是获取的key，是13个字符组成的字符串



## 🚑  提交自己的服务器？

**本项目原旨在方便自己查询管理服务器，如果你希望提供了ip**

**那么我只能尽可能保证您的ip不会泄漏，如果无法承担风险则请勿提供ip**


新增一个json文件，格式如下,文件名与需要响应的指令一致

        {
        "呆呆": [
                {
                "id": 1,
                "version": "战役",
                "ip": "43.248.188.17:27031"
                }
        ]
        }

<h2 id="ty">🌐 默认服务器</h2>
目前 **已授权** 的服务器查询，如果需要加入自己的ip可以进qq群私聊群主

| 指令 | 服务器 | op | 数量 |
|:-----:|:----:|:----:|:----:|
| 数码 | 爱丽数码想要涩涩 | 爱丽数码 | 3
| 云 | anne电信服云服 | 东 | 27
| 呆呆 | 呆呆的小窝 | 提莫大魔王 | 14
| 橘 | 橘希实香的小窝 | 橘希实香 | 14
| 竹 | 竹烨 | 竹烨oО柠檬茶 | 6
| 音理 | 星空列车与白的旅行 | 音理 | 3
| 尤 | 尤尤 | 晓音 | 3
| 鱼 | 飞鱼の小窝 | 飞鱼桑 | 3
| 恋恋 | 恋氏集团雪糕制作研究中心 | 古明地恋 | 1
| Air | Air | Air | 15
| 3ks | 为人民服务 | DK | 14


## 🔖 更新日志

<details>
<summary>展开/收起</summary>

### 0.4.6--2022.4.9

 - 显示无效服
 - 优化服务器排序算法（list.sort()天下第一）
 - 默认关闭web端

### 0.4.5--2022.4.9

- 修bug（恼）

### 0.4.2--2022.4.9

 - 修复响应开头匹配出现的重大bug
 - 启用web端
 - web使用yaml管理，未来可能删除env配置

### 0.4.1--2022.3

 - 修复rar压缩包命名错误
 - 更新了tag的参数读取方式
 - 确定了传文件私聊比群聊快速
 - 修复了电信服计算错误

### 0.4.0--2022.3.27

 - 新增web控制台
 - 修复传图超时参数错误
 - 重写求生ip获取方法 ~ 数据库苦手 ~
 - 重写文档
 - 不再内置ip（毕竟ipv4都暴露太危险了）

### 0.3.7--2022.3

 - 新增三方下载网盘
 - 修复windows上传临时文件错误
 - 优化查服流程
 - 优化anne服随机功能

### 0.3.6--2022.3.10

 - 暂时关闭web端，后续修改
 - 优化图片显示
 - 修复了海量bug
 - 新增三方图查询

### 0.3.5--2022.3.6

 - 新增ping查询（在ip里包括）
 - 新增api查询（未完成）
 - 修复了电信服查询绑定名字无法查询的错误
 - 新增了救援率的显示
 - 新增web端（未完成）

### 0.3.4--2022.3.1

 - 新增本地插件smx查询
 - 增加了三个内置群服
 - 修改了图片的UI,变好看了
 - 删减了部分图片和字体，使得轻量化
 - 修复了海量bug
 - 修复了python3.8中typing错误

### 0.3.3--2022.2.26

 - 重写协议，使用a2s库，同时解决win端不同报错无法输出
 - 重~抄~写服务器查询UI,解决了不好看的问题
 - 从win测试，解决了一些win特有的bug
 - 重写服务器查询~还得是json~
 - 内置服务器查询系统，可以通过[服务器简称]+[number]/[模式]来访问
 - 新增批量查询服务器，不带参数则返回图片

### 0.3.1--2022.2.22

 - 修复了路径识别为str对象的错误
 - 修复了初始化找不到文件的错误
 - 修复了路径拼接错误
 - 在win端成功测试，修复压缩包bug
 - 新增开关协程异步env设置
 - 测试rcon建立通讯
 - 实现切换路径查看地图和使用rcon指令

### 0.3.0--2022.2.18

 - 修改了新的env配置，使得支持本地多服务器操作
 - 彻底解决了压缩包解压linux端的问题
 - 解决了win端默认gbk解码的错误
 - 解决rcon指令字体报错

### 0.2.5--2022.2.10

 - 修复了依赖不足的bug
 - 更新了电信服战绩个人图片UI
 - 更新了批量服务器查看的UI
 - 修改了传文件为协程异步
 - 优化了部分rcon指令
 - ~tnd7z怎么不去死啊~使用pyunpack库解压7z

### 0.2.4--2022.2.8

 - 使用poetry修复了pip安装文件缺失的bug

### 0.2.3--2022.2.7

 - 新增坐牢和开牢
 - 修改了获取资源为异步协程却阻碍其他指令的bug
 - 新增json统计部分已知服务器（未来应该独立成库持续更新，如果把您的非公开服记录请联系我删除）
 - 喷剂制作开摆了，推测需要c/c++环境
 - 修改抽取文案
 - 新增查询服务器状态时返回connect ip
 - 修复了服务器查询无响应的时候，因为报错无回复信息的bug
 - 个人信息重置测试代码，下个版本更新
 - 新增求生更新添加和删除

### 0.2.2--2022.2.1

 - 新增探监
 - 新增喷漆制作
 - 修复了魔改服务器导致解包错误的bug（就是直接忽略了）
 - 修改了部分对话响应

### 0.2.1--2022.1.25

 - 新增电信服获取（东哥的肯定）
 - 优化图片UI 
 - 新增云服快捷查询
 - 修复了因为没用玩家，导致的服务器状态查询错误
 - 新增电信服ip爬取（仅仅作为单次更新ip列表）

### 0.2.0--2022.1.21

 - 新增创意工坊查询
 - 优化查询图片UI
 - 新增创意工坊文件下载
 - 修复了因为电信服官网前端修改导致查询失败的BUG

### 0.1.7--2022.1.19

 - 新增群ip订阅，批量查询
 - 新增图片显示ip状态
 - 修复了因为玩家名字特殊字符导致的utf-8解码错误
 - 更新自己的第三方库VSQ==0.0.6

### 0.1.6--2022.1.15

 - 新增ip查询服务器提供玩家数量和名字
 - 增加协程函数修复因为加载顺序导致的错误
 - 更新自己的第三方库VSQ==0.0.4

### 0.1.5--2022.1.15

- 新增服务器控制台指令，新增依赖rcon
- 重新了数据库，不再使用json而是使用sql3
- 改写了求生anne信息显示方式：如果单个数据以图片显示，如果多个数据以文字显示

### 0.1.4--2022.1.9

- 新增求生anne详情（看排名）
- 所有的请求改为httpx
- 更新了anne信息图片
- 可选使用模拟谷歌浏览器来获取anne更多数据（~有点屎了，希望大佬救救~)

### 0.1.3--2022.1.7

- 新增绑定昵称和steamid
- 新增可以艾特人查询anne成绩
- 新增解绑信息

### 0.1.2--2022.1.6

- 新增支持图片输出
- 新增查询anne服数据

### 0.1.1--2022.1.5

- 新增删除地图
- 新增地图改名
- 新增支持图片输出

### 0.1.0--2022.1.4

- 集中修复了Bug

### 0.0.9--2022.1.4

- 新增上传地图后，检测对比回复新地图名字
- 修复中文名乱码问题

### 0.0.8--2022.1.4

- 支持vpk格式地图
- 支持查看所有vpk格式文件

### 0.0.6--2022.1.3

- 修复了7z压缩包的方式，优化代码

### 0.0.1--2022.1.3

- 插件初次发布，可私聊添加地图

</details>

## 🙈 其他

+ 本人技术很差，如果您有发现BUG或者更好的建议，欢迎提Issue & Pr
+ 如果本插件对你有帮助，不要忘了点个Star~
+ 本项目仅供学习使用，请勿用于商业用途
+ [GPL-3.0 License](https://github.com/Agnes4m/nonebot_plugin_l4d2_server/blob/main/LICENSE) ©[@Agnes4m](https://github.com/Agnes4m)
        

<h2 id="ty">🌐 感谢</h2>

- [修仙](https://github.com/s52047qwas/nonebot_plugin_xiuxian) - 数据库的写法来自于他
- [自己写的求生之路查询库](https://github.com/Agnes4m/VSQ)(已弃用)
- [@MeetWq](https://github.com/MeetWq) - 非常热心解答nonebot2相关的写法
  - [可爱小Q](https://github.com/MeetWq/mybot) - 服务器图片写法参考小Q帮助
- [群聊学习](https://github.com/CMHopeSunshine/nonebot-plugin-learning-chat) - web控制台的写法来自于他
- [gsuid](https://github.com/KimigaiiWuyi/GenshinUID) - readme和wiki的格式参考
- 呆呆 - 提供三方地图的详细数据
