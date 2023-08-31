<!-- markdownlint-disable MD026 MD031 MD033 MD036 MD041 MD046 MD051 -->
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
    <img src="https://img.shields.io/badge/nonebot-2.0.0-red.svg" alt="NoneBot">

</div>

## 顶置公告

- 文档暂时没时间更新ozr

- 如果你只是一个游戏玩家，你可以在[这里](#🌐-感谢)找一个游戏群加入游玩

- 网页端管理端 `https://{ip}:{port}/l4d2`

- 网页用户端 `https://{ip}:{port}/l4d2/user`

## 安装

以下提到的方法 任选**其一** 即可

<details open>
<summary>[个人推荐] 使用 nb-cli 安装</summary>
在 nonebot2 项目插件文件夹中，输入以下指令克隆项目，并安装相关依赖(如果有虚拟环境，pip安装依赖需要进虚拟环境再安装，或者参考下方包管理器安装方法)

```bash
https://github.com/Agnes4m/nonebot_plugin_l4d2_server
pip install --no-install nonebot_plugin_l4d2_server 
```

</details>

<details open>
<summary>[新手推荐] 使用 nb-cli 安装</summary>
在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

```bash
nb plugin install nonebot-plugin-l4d2-server
```

</details>

<details>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令

<details>
<summary>pip</summary>

```bash
pip install nonebot-plugin-l4d2-server
```

</details>
<details>
<summary>pdm</summary>

```bash
pdm add nonebot-plugin-l4d2-server
```

</details>
<details>
<summary>poetry</summary>

```bash
poetry add nonebot-plugin-l4d2-server
```

</details>
<details>
<summary>conda</summary>

```bash
conda install nonebot-plugin-l4d2-server
```

</details>
</details>

## 主要功能

- 求生服务器-本地多路径操作（传地图）
- 批量查询指定ip服务器状态和玩家
- 创意工坊下载和喷漆制作
- web控制台
- [求生电信服anne](https://github.com/fantasylidong/CompetitiveWithAnne)[查询~](https://sb.trygek.com/l4d_stats/ranking/index.php)

## [数据结构](./docs/standand.md)

## 🌐 默认服务器

适配公益服刷服器适配ip

## To do

- [ ] 帮助图片
- [ ] 网页控制台查看服务器地图
- [ ] 网页控制台启动和关闭服务器
- [ ] 网页控制台管理封禁用户

## 其他

- 本人技术很差，如果您有发现BUG或者更好的建议，欢迎提Issue & Pr
- 如果本插件对你有帮助，不要忘了点个Star~
- 本项目仅供学习使用，请勿用于商业用途
- [更新日志](./docs/update.md)
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
- 公益服刷服器 - 虽然不知道哪里来的，不过已经添加ip了
- 感谢以下服主大力支持
  - Michaela's | 机器人功能测试反馈 | [橘组多模式游戏群](http://qm.qq.com/cgi-bin/qm/qr?_wv=1027&k=pUKFe4sSUMgLn0N84IhBtTzrdVzFxRLd&authKey=v8tdd3yys6VnK2WI%2F76fN85yfmHpdv%2Bfttj37n4DqnZMdyv9N6nUsyNyuk2QKoOR&noverify=0&group_code=578503081)
  - 东 | 提供docker部署方法等建议 | [电信服anne游戏群](http://qm.qq.com/cgi-bin/qm/qr?_wv=1027&k=6i7r5aJ7Jyg0ejby4rt9GWmFRF53nV1K&authKey=ekMsWepBZPL26%2BfJAG%2F95JD0fhvH39%2BIGVyKOvNlXVDbpIclJlly4kXqukL7JhWR&noverify=0&group_code=883237206)
  - 呆呆 | 提供三方地图的详细数据 | [呆呆组游戏群](http://qm.qq.com/cgi-bin/qm/qr?_wv=1027&k=M5Ei0tYBgi3nwkh-8jfvo3gN5BMhPQGr&authKey=tb2Qa7ykUf5RAe3TBvOIA%2FWdlHAx6tqYXhyV95WqbZXoUx7lU2MRbod7nubiFw16&noverify=0&group_code=592944622)
  - 柠檬茶 | win端部署测试 | [竹服⭐纯净服游戏群](http://qm.qq.com/cgi-bin/qm/qr?_wv=1027&k=G8AkutNEmN9niNCjNJV8YE-vLv4h_EBz&authKey=wG%2BI6Cks4%2FcRGYYLjRNK0Kg4rMUy3BB7H9SKGjU465ktqKcb%2F6m7WxrSTJiX5bvk&noverify=0&group_code=283150432)
  - 迷茫 | 催命更新byd
  - ArcPav | 积极反馈bug，提供改进思路
