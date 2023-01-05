<div align="center">
  <img src="https://s2.loli.net/2022/06/16/opBDE8Swad5rU3n.png" width="180" height="180" alt="NoneBotPluginLogo">
  <br>
  <p><img src="https://s2.loli.net/2022/06/16/xsVUGRrkbn1ljTD.png" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot_plugin_l4d2_server
_✨Nonebot & Left 4 Dead 2 server操作✨_

<a href="https://github.com/Umamusume-Agnes-Digital/nonebot_plugin_l4d2_server/stargazers">
    <img alt="GitHub stars" src="https://img.shields.io/github/stars/Umamusume-Agnes-Digital/nonebot_plugin_l4d2_server?color=%09%2300BFFF&style=flat-square">
</a>
<a href="https://github.com/Umamusume-Agnes-Digital/nonebot_plugin_l4d2_server/issues">
    <img alt="GitHub issues" src="https://img.shields.io/github/issues/Umamusume-Agnes-Digital/nonebot_plugin_l4d2_server?color=Emerald%20green&style=flat-square">
</a>

</div>

## 安装
    1、nb plugin install nonebot_plugin_l4d2_server
    2、pip install nonebot_plugin_l4d2_server
    3、Download zip

## 前置操作-创建一个steam求生服务器(预计需要储存14G)

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
        sv_steamgroup "114514"     //Steam组号
        sv_steamgroup_exclusive 1 //将服务器设为Steam组私有
        sv_allow_lobby_connect_only 0
        sm_cvar sv_gametypes "coop"//设置游戏模式为合作
        //设为1可防止玩家加入感染者方，仅战役模式
        sm_cvar director_no_human_zombies "1"
        mp_gamemode "coop"//激活游戏模式为合作
        z_difficulty "Hard"//设置游戏难度为困难
        sm_cvar sb_all_bot_game 1// 防止人数不足而自动关闭
        sv_tags "hidden" //防止DDos攻击
        sm_cvar sv_region 4// 设定服务器区域为亚洲
        sv_visiblemaxplayers 8 //服务器可见最大玩家数
        maxplayers 8 //最大玩家数

:wq回车保存

        cd ~
        sudo vi start.sh

在脚本里写入

        cd /home/ubuntu/l4d2
        sudo ./srcds_run -game left4dead2 +exec server.cfg

- 启动游戏

        cd ~
        sh start.sh

</details>

## env配置
| 配置项 | 必填 | 默认值 | 说明 |
|:-----:|:----:|:----:|:----:|
| "l4_file" | 是 | "/home/ubuntu/l4d2/coop" | 输入求生服务器的绝对路径,该目录下有游戏启动程序srcds_run |

## 功能
（被动）上传地图：私发压缩包zip/vpk文件给机器人，就可以直接上传地图到服务器了

| 指令 | 范围 | 是否需要艾特 | 说明 |
|:-----:|:----:|:----:|:----:|
| 求生地图/查看求生地图 | 所有人 | 否 | 获取当前路径下所有的vpk文件，并输出目录 |
| 删除(求生)地图[number] | 群管/超管 | 否 | 根据求生地图列出的序号，删除地图，[number]可以在第二条消息内输入 |

## 📝 TODO LIST

- [ ] 帮助文件
- [ ] 支持修改下载地图，在服务器端的名称
- [✔️] 支持查询并删除服务器已有地图文件
- [ ] 支持查询服务器状态
- [ ] 支持多服务器切换
- [ ] 在q群里执行服务器指令

## 已知BUG

- [ ] 无法在python3.10版本下解压7z格式压缩包
- [ ] 所有人都可以私聊发送文件

## 效果展示
    -
    ![image](https://github.com/Umamusume-Agnes-Digital/nonebot_plugin_l4d2_server/tree/main/image/list.png)  
    ![image](https://github.com/Umamusume-Agnes-Digital/nonebot_plugin_l4d2_server/tree/main/image/up.png)  


## 📝 更新日志

<details>
<summary>展开/收起</summary>

### 0.1.1

- 新增删除地图

### 0.1.0

- 集中修复了Bug

### 0.0.9

- 新增上传地图后，检测对比回复新地图名字
- 修复中文名乱码问题

### 0.0.8

- 支持vpk格式地图
- 支持查看所有vpk格式文件

### 0.0.6

- 修复了7z压缩包的方式，优化代码

### 0.0.1

- 插件初次发布，可私聊添加地图

</details>

## 已测试环境
win10 python3.9 <br>
ubuntu20.04 python3.10
