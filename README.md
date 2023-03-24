<div align="center">
  <img src="https://raw.githubusercontent.com/Umamusume-Agnes-Digital/nonebot_plugin_l4d2_server/main/image/logo.jpg" width="180" height="180" alt="NoneBotPluginLogo">
  <br>
  <p><img src="https://s2.loli.net/2022/06/16/xsVUGRrkbn1ljTD.png" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot_plugin_l4d2_server
_✨Nonebot & Left 4 Dead 2 server操作✨_

<a href="https://github.com/Umamusume-Agnes-Digital/nonebot_plugin_l4d2_server/stargazers">
        <img alt="GitHub stars" src="https://img.shields.io/github/stars/Umamusume-Agnes-Digital/nonebot_plugin_l4d2_server" alt="stars">
</a>
<a href="https://github.com/Umamusume-Agnes-Digital/nonebot_plugin_l4d2_server/issues">
        <img alt="GitHub issues" src="https://img.shields.io/github/issues/Umamusume-Agnes-Digital/nonebot_plugin_l4d2_server" alt="issues">
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
    <img src="https://img.shields.io/badge/python-3.7+-blue.svg" alt="python">
    <img src="https://img.shields.io/badge/nonebot-2.0.0rc1+-red.svg" alt="NoneBot">
</div>

# 导航

 - [主要功能](#gn)
 - [安装](#az)
 - [env一键设置](#env)
 - [前置操作](#qz)
 - [指令](#zl)
 - [env参数](#cs)
 - [感谢](#ty)
 - [内置的查询ip](#cx)

<h2 id="gn">主要功能</h2>

- 求生服务器-本地多路径操作（传地图）
- 批量查询指定ip服务器状态和玩家
- 创意工坊下载和喷漆制作
- [求生电信服anne](https://github.com/fantasylidong/CompetitiveWithAnne)[查询~](https://sb.trygek.com/l4d_stats/ranking/index.php)


<h2 id="az">安装</h2>

    1、nb plugin install nonebot_plugin_l4d2_server
    2、pip install nonebot_plugin_l4d2_server
    3、Download zip
    4、git clone https://github.com/Umamusume-Agnes-Digital/nonebot_plugin_l4d2_server.git

<h2 id="env">快速使用（env示例）</h2>

        # 复制到env文件里，没有默认就是下列值，如需修改安装下面env设置
        # 所有的多选，用逗号隔开
        l4_master = ['1145149191']
        l4_file = ['/home/ubuntu/l4d2/coop']
        l4_host = ['127.0.0.1']
        l4_port = ['20715']
        l4_rcon = ['1145149191810']
        l4_font = 'simsun.ttc'
        l4_only = True

<h2 id="qz">前置游戏操作 </h2>

- 如果要操作求生服务器文件，机器人与求生服务器处于同一个服务器上

- 如果你按照以下步骤操作，env配置可以不填

- 创建一个steam求生服务器(预计需要储存14G)


<details>
<summary>展开/收起</summary>


### 以ubuntu为例，具体教程建议自行搜索，其中路径可以自行替换

- 安装32位运行库

        sudo apt-get update
        sudo apt-get upgrade
        sudo apt-get install lib32gcc1

- 下载steam

        mkdir ~/steamcmd
        cd ~/steamcmd
        wget https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz
        tar -zxvf steamcmd_linux.tar.gz
        ./steamcmd.sh

- 下载l4d2文件

        Steam> force_install_dir /home/ubuntu/coop
        Steam> login anonymous
        Steam>app_update 222860 validate
出现Success! App ‘222860’ fully installed后，输入quit或者exit

- 创建启动脚本

        sudo vi /home/ubuntu/coop/cfg/server.cfg
写入

        hostname "xxx"     //游戏服务器名(英文)
        rcon_password "114514"  //rcon密码
        sv_steamgroup "114514"     //Steam组号
        sv_steamgroup_exclusive 1 //将服务器设为Steam组私有
        sm_cvar sv_gametypes "coop"//设置游戏模式为合作
        //设为1可防止玩家加入感染者方，仅战役模式
        sm_cvar director_no_human_zombies "1"
        mp_gamemode "coop"//激活游戏模式为合作
        sm_cvar z_difficulty "Hard"//设置游戏难度为困难
        sv_tags "hidden" //防止DDOS
        sm_cvar sv_region 4// 设定服务器区域为亚洲
        sv_visiblemaxplayers 8 //服务器可见最大玩家数
        maxplayers 8 //最大玩家数

:wq回车保存

        cd ~
        sudo vi start.sh

在脚本里写入

        cd /home/ubuntu/l4d2
        sudo ./srcds_run -game left4dead2 -condebug -tickrate 60 +exec server.cfg +map c2m1_highway

- 启动游戏

        cd ~
        sh start.sh

</details>


<h2 id="zl">🤔 功能（指令）</h2>


### 服务器

（被动）上传地图：设置l4_master后，在群内发送压缩包zip/vpk/7z/rar，就可以直接上传地图到服务器了
        如果设置了管理员，那么在群里也响应
        [ip]格式为[127.0.0.1:20715]括号内

求生帮助：获取简单的帮助列表

<details>
<summary>展开/收起</summary>

| 指令 | 范围 | 用途 | 说明 |
|:-----:|:----:|:----:|:----:|
| 求生地图/查看求生地图 | 所有人 | 看图 | 获取当前路径下所有的vpk文件，并输出目录 |
| (求生)地图删除[number] | 群管/超管 | 删图 | 根据求生地图列出的序号，删除地图，[number]可以在第二条消息内输入 |
| 求生地图[number][改/改名][text] | 群管/超管 | 改图名 | [number]同上，text为更改后名称，如果没有.vpk后缀会自动加上 |
| 求生服务器指令[text] | 群管/超管 | 控制台 | rcon连接求生服务器控制台，使用ip和passsword |
| 求生路径 | 群管/超管 | 查看路径 | 查看当前服务器路径 |
| 求生路径切换[number] | 群管/超管 | 切换路径 | 切换本地服务器路径 |

### anne(电信服)

| 指令 | 范围 | 用途 | 说明 |
|:-----:|:----:|:----:|:----:|
| 探监/坐牢/开牢 | 所有人 | 随机抽一个目标云服 | 探监是得分超过160的队伍\n坐牢是缺人队伍\n开牢是空人房间 |
| 求生anne[text]/@/[None] | 所有人 | 查anne成绩 | [text]可以是:空白(则使用绑定信息)、昵称、steamid、@user |
| 求生绑定/steam绑定/anne绑定[text] | 所有人 | 绑定steam信息 | [text]可以是:昵称、steamid |
| 求生解绑/steam解绑/anne解绑 | 所有人 | 解绑steam信息 | 无 |
| 云[number] | 所有人 | 云服信息 | 获取服务器状态和直连ip |


### ip(服务器查询)

| 指令 | 范围 | 用途 | 说明 |
|:-----:|:----:|:----:|:----:|
| 求生ip[ip] | 所有人 | 查指定服务器 | [text]格式为[127.0.0.1:20715]括号内，可以查询服务器玩家名字 |
| 求生订阅[ip] | 所有人 | 查询订阅服务器状态 | 返回一个图片\n显示群所有订阅的服务器名字、状态、地图、玩家名字 |
| 求生加入[number] | 所有人 | 获取进服直链 | [number]为求生订阅所显示的开头序号 |
| 求生添加订阅[ip] | 群管 | 群订阅添加 | 新增订阅ip，在下次订阅的时候可以显示 |
| 求生取消订阅[number] | 所有人 | 群订阅取消 | [number]为求生订阅所显示的开头序号 |
| 求生更新 添加 [tag] [ip] [text] ([number]) | 群管 | 全局订阅添加 | 可以使用tag(+text)(+number)快速索引服务 |
| 求生更新 删除 [tag] [number] | 群管 | 全局订阅添加 | [number]为求生订阅标记的默认序号 |
| 求生更新 | 群管 | 刷新缓存 | 一般用不到，如果卡指令可能有用 |

### 其他功能

| 指令 | 范围 | 用途 | 说明 |
|:-----:|:----:|:----:|:----:|
| 创意工坊下载[text] | 所有人 | 下载创意工坊文件 | [text]为id或者网页url |
| 求生喷漆 | 所有人 | 制作一个喷漆 | 只支持图片暂不支持gif |

</details>

<h2 id="cs">✅ env配置</h2>

<details>
<summary>展开/收起</summary>

### 本地服务器相关
| 配置项 | 必填 | 默认值 | 说明 |
|:-----:|:----:|:----:|:----:|
| l4_master | 是 | ['1145149191'] | list,里面是可以在群里传求生地图的qq号
| l4_file | 否 | ["/home/ubuntu/l4d2/coop"] | 输入求生服务器的绝对路径,该目录下有游戏启动程序srcds_run |
| l4_host | 否 | ['127.0.0.1'] | 服务器ip，如果是本机一般就是默认 |
| l4_port | 否 | ['20715'] | 服务器端口号 |
| l4_rcon | 否 | ['114514'] | 服务器的rcon密码 |

### 可选填写
| 配置项 | 必填 | 默认值 | 说明 |
|:-----:|:----:|:----:|:----:|
| l4_steamid | 否 | False | 布尔值，默认在输出时隐藏steamid，需要则设置为True |
| l4_image | 否 | True | 布尔值，是否显示图片 |
| l4_font | 否 | 'simsun.ttc' | str，确保在开启图片的时候，字体存在 |
| l4_only | 否 | False | 布尔值，如果不想在下载的时候阻碍其他指令可以开启，但是有不能下载超过200m地图的bug |
| l4_style | 否 | '' | str,图片风格，目前可选['balck'] |


</details>

## ✨ 效果展示

订阅:<br>
![ip](https://raw.githubusercontent.com/Umamusume-Agnes-Digital/nonebot_plugin_l4d2_server/main/image/ip_server.png)<br>
anne:<br>
![anne](https://raw.githubusercontent.com/Umamusume-Agnes-Digital/nonebot_plugin_l4d2_server/main/image/anne.png)<br>
群聊：<br>
![list](https://raw.githubusercontent.com/Umamusume-Agnes-Digital/nonebot_plugin_l4d2_server/main/image/list.png)<br>
私聊：<br>
![up](https://raw.githubusercontent.com/Umamusume-Agnes-Digital/nonebot_plugin_l4d2_server/main/image/up.png)<br>

## 🤔 FAQ

        Q:UnicodeDecodeError: 'utf-8' codec can't decode byte 0xd0 in position xxx: invalid continuation byte</b>

        A:说明rcon连接服务器时返回了乱码，有可能读取的信息包含表情包或者其他不明字符，我的方法是找到本地pypi包的rcon，编辑rcon/source/async_rcon.py,找到return response.payload.decode(encoding)并替换为return response.payload.decode(encoding,errors='ignore')


        Q:ModuleNotFoundError: No module named '_lzma'

        A:python3.3版本后常见，解决方法是
        vim /usr/local/lib/python3.10/lzma.py
        #修改前
        from _lzma import *
        from _lzma import _encode_filter_properties, _decode_filter_properties
        #修改后 
        try:
        from _lzma import *
        from _lzma import _encode_filter_properties, _decode_filter_properties
        except ImportError:
        from backports.lzma import *
        from backports.lzma import _encode_filter_properties, _decode_filter_properties

         - 解压功能
 
        # rar压缩包
        # win直接下winRAR软件就可以
        # Ubuntu 和 Debian
        sudo wget https://www.rarlab.com/rar/rarlinux-x64-621b1.tar.gz
        sudo tar -xzpvf rarlinux-x64-621b1.tar.gz
        cd rar
        sudo make


## 📝 TODO LIST

<details>
<summary>展开/收起</summary>

- [ ] 帮助命令
- [x] 创意工坊内容下载并上传q群
- [ ] 求生每日签到/抽签
- [ ] 按照数值自定义绘画信息图片
- [ ] 支持直接修改本地cfg文件
- [ ] ~支持远程连接求生服务器并操作~

</details>

## 🐛  已知BUG

<details>
<summary>展开/收起</summary>

- [ ] 更改地图名称后，排序会错误
- [ ] 求生喷漆可加载但无法输出

</details>

## 🔖 更新日志

<details>
<summary>展开/收起</summary>


### 0.4.0--2022.3

 - 新增web控制台
 - 修复传图超时参数错误

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

## ✨ 开发环境
ubuntu20.04 python3.10

## 📖许可证GPL3.0

        This project is licensed under the GNU General Public License v3.0. See the LICENSE file for more information.


<h2 id="ty">🌐感谢</h2>

- 1、[修仙插件的数据库写法](https://github.com/s52047qwas/nonebot_plugin_xiuxian)
- 2、~[自己写的求生之路查询库](https://github.com/Umamusume-Agnes-Digital/VSQ)~
- 3、[可爱小Q的帮助(太好看了tql)](https://github.com/MeetWq/mybot)
- 4、感谢petpet交流群各位大佬指点nonebot2事件处理api
- 5、ArcPav改的暗♂黑风格菜单
- 6、呆呆整理的三方地图表格和个人网盘

<h2 id="cx">服务器相关 </h2>

目前插件会内置经腐竹同意的服的查询（未来将使用api）

| 指令 | 服务器 | op | 数量 |
|:-----:|:----:|:----:|:----:|
| 云 | ~anne电信服云服~(暂时不提供) | 东 | 22
| 呆呆 | 呆呆的小窝 | 提莫大魔王 | 15
| 橘 | 橘希实香的小窝 | 橘希实香 | 8
| 竹 | 竹烨 | 竹烨oО柠檬茶 | 9

如果需要上传自己的ip可以Pr、iss或者进qq群

[pr修改这个文件](https://github.com/Umamusume-Agnes-Digital/nonebot_plugin_l4d2_server/blob/main/nonebot_plugin_l4d2_server/data/L4D2/l4d2.json)
