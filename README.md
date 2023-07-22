<div align="center">
  <img src="https://raw.githubusercontent.com/Agnes4m/nonebot_plugin_l4d2_server/main/image/logo.png" width="180" height="180"  alt="AgnesDigitalLogo">
  <br>
  <p><img src="https://s2.loli.net/2022/06/16/xsVUGRrkbn1ljTD.png" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot_plugin_l4d2_server 0.6

_✨Nonebot & Left 4 Dead 2 server操作✨_
<div align = "center">
        <a href="https://agnes4m.github.io/l4d2/" target="_blank">文档</a> &nbsp; · &nbsp;
        <a href="https://agnes4m.github.io/l4d2/reader/#%E5%8A%9F%E8%83%BD-%E6%8C%87%E4%BB%A4-%F0%9F%A4%94" target="_blank">指令列表</a> &nbsp; · &nbsp;
        <a href="https://agnes4m.github.io/l4d2/bug/">常见问题</a>
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
    <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="python">
    <img src="https://img.shields.io/badge/nonebot-2.0.0rc3-red.svg" alt="NoneBot">

</div>

## 顶置公告

多适配器版本请查看[分支](https://github.com/Agnes4m/nonebot_plugin_l4d2_server/tree/nb_adapter)

文档暂时没时间更新ozr

网页端管理端 `https://{ip}:{port}/l4d2`
网页用户端 `https://{ip}:{port}/l4d2/user`

## 安装

以下方法任选其一：

        nb plugin install nonebot-plugin-l4d2-server
        pip install nonebot-plugin-l4d2-server
        pipx install nonebot-plugin-l4d2-server
        git clone https://github.com/Agnes4m/nonebot_plugin_l4d2_server.git

## 主要功能

- 求生服务器-本地多路径操作（传地图）
- 批量查询指定ip服务器状态和玩家
- 创意工坊下载和喷漆制作
- web控制台
- [求生电信服anne](https://github.com/fantasylidong/CompetitiveWithAnne)[查询~](https://sb.trygek.com/l4d_stats/ranking/index.php)

## 数据结构

bot所在文件夹下

```txt
举例：
└── data
    └── L4D2
        ├── l4d2.yml         # 配置文件
        ├── l4d2.json        # ip文件
        ├── scheduler.json   # 定时文件
        ├── sql              # 数据库
        │   └── L4D2.db
        ├── image            # 头像缓存
        │   └── players
        │       └── ...
        └── l4d2             # 子ip文件
            ├── 关键词1.json
            ├── 关键词2.json
            └── ...
...
```

新增一个json文件，格式如下,文件名与需要响应的指令一致
`l4d2.json`和`关键词1.json`都可以加载

        {
        "呆呆": [
                {
                "id": 1,
                "version": "战役",
                "ip": "43.248.188.17:27031"
                },
                {
                "id": 2,
                "version": "战役",
                "ip": "43.248.188.17:27032"
                }
        ]
        }

## 🌐 默认服务器

以下仅供参考本人使用的查询服务器

| 指令 | 服务器 | op | 数量 |
|:-----:|:----:|:----:|:----:|
| 数码 | 爱丽数码想要涩涩 | 爱丽数码 | 2
| 云 | anne电信服云服 | 东 | 21
| 呆呆 | 呆呆的小窝 | 提莫大魔王 | 15
| 橘 | 橘希实香的小窝 | 橘希实香 | 21
| 竹 | 竹烨 | 竹烨oО柠檬茶 | 27
| 音理 | 星空列车与白的旅行 | 音理 | 3
| 尤 | 尤尤 | 晓音 | 1
| 鱼 | 飞鱼の小窝 | 飞鱼桑 | 1
| 恋恋 | 恋氏集团雪糕制作研究中心 | 古明地恋 | 3
| Air | Air | Air | 15
| 3ks | 为人民服务 | DK | 14
| 驴头 | 驴头服 | lvt | 4
| 迷茫 | 迷茫 | 迷茫 | 10
| 尸鬼 | 尸鬼狂潮 | ❀几❀ | 13

## To do

- [ ] 帮助图片
- [ ] 网页控制台查看服务器地图
- [ ] 网页控制台启动和关闭服务器
- [ ] 网页控制台管理封禁用户

## 其他

- 本人技术很差，如果您有发现BUG或者更好的建议，欢迎提Issue & Pr
- 如果本插件对你有帮助，不要忘了点个Star~
- 本项目仅供学习使用，请勿用于商业用途
- [GPL-3.0 License](https://github.com/Agnes4m/nonebot_plugin_l4d2_server/blob/main/LICENSE) ©[@Agnes4m](https://github.com/Agnes4m)

## 🌐 感谢

- [nonebot2](https://github.com/nonebot/nonebot2)- 聊天机器人的基础框架
- [修仙](https://github.com/s52047qwas/nonebot_plugin_xiuxian)- 数据库参考
- ~~[自己写的求生之路查询库](https://github.com/Agnes4m/VSQ)~~ (已弃用)
- [@MeetWq](https://github.com/MeetWq)- 非常热心解答nonebot2相关的写法
  - [可爱小Q](https://github.com/MeetWq/mybot)- 服务器图片参考
- [群聊学习](https://github.com/CMHopeSunshine/nonebot-plugin-learning-chat)- web控制台参考
- [日向麻麻](https://github.com/Special-Week)- 配置优化参考
- [gsuid](https://github.com/KimigaiiWuyi/GenshinUID)- readme和wiki的格式参考，以及3.1版本的更新和重启
- 呆呆- 提供三方地图的详细数据
- ArcPav -积极反馈bug，提供改进思路
