<!-- markdownlint-disable MD026 MD031 MD033 MD036 MD041 MD046 MD051 -->
<div align="center">
  <img src="https://raw.githubusercontent.com/Agnes4m/nonebot_plugin_l4d2_server/main/image/logo.png" width="180" height="180"  alt="AgnesDigitalLogo">
  <br>
  <p><img src="https://s2.loli.net/2022/06/16/xsVUGRrkbn1ljTD.png" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot_plugin_l4d2_server 1.3.0

_✨Nonebot & Left 4 Dead 2 server 操作 ✨_

<div align = "center">
        <a href="https://agnes4m.github.io/l4d2/" target="_blank">文档</a> &nbsp; · &nbsp;
        <a href="https://agnes4m.github.io/l4d2/reader/#%E5%8A%9F%E8%83%BD-%E6%8C%87%E4%BB%A4-%F0%9F%A4%94" target="_blank">指令列表</a> &nbsp; · &nbsp;
        <a href="https://agnes4m.github.io/l4d2/bug/">常见问题</a>
</div><br>

<img src="https://img.shields.io/badge/python-3.9+-blue?logo=python&logoColor=edb641" alt="python">
<a href ="LICENSE">
<img src="https://img.shields.io/github/license/Agnes4m/nonebot_plugin_l4d2_server" alt="l4logo">
</a>
<img src="https://img.shields.io/badge/nonebot-2.1.0+-red.svg" alt="NoneBot">
<a href="https://pypi.python.org/pypi/nonebot_plugin_l4d2_server">
<img src="https://img.shields.io/pypi/v/nonebot_plugin_l4d2_server?logo=python&logoColor=edb641" alt="python">
</a>
</br>
<a href="https://github.com/astral-sh/ruff">
<img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json" alt="ruff">
</a>
<a href="https://github.com/psf/black">
<img src="https://img.shields.io/badge/code%20style-black-000000.svg?logo=python&logoColor=edb641" alt="black">
</a>

<img src="https://img.shields.io/badge/alconna-0.58.3+-red.svg" alt="NoneBot">

<a href="https://github.com/Agnes4m/nonebot_plugin_l4d2_server/issues">
        <img alt="GitHub issues" src="https://img.shields.io/github/issues/Agnes4m/nonebot_plugin_l4d2_server" alt="issues">
</a>

<a href="https://pypi.python.org/pypi/nonebot_plugin_l4d2_server">
    <img src="https://img.shields.io/pypi/dm/nonebot_plugin_l4d2_server" alt="pypi download">
</a>
</br>
<a href="https://jq.qq.com/?_wv=1027&k=HdjoCcAe">
        <img src="https://img.shields.io/badge/QQ%E7%BE%A4-399365126-orange?style=flat-square" alt="QQ Chat Group">
</a>
</div>

## 功能

- `l4d2帮助` 帮助指令

### 自定义服务器

- 在 json 文件设置的前缀指令，例如设置"云"，则指令 云 输出组服务器，云 1 输出 1 号服务器

### SourceBans++

- 通过 [SourceBans++](https://sbpp.github.io/) 获取服务器的 ban 信息，自动导入ip

### 配置管理

- l4 图片开启/关闭 超管指令 可以修改输出单图是否为图片输出
- l4 查找用户 在已知服务器中查找
- l4 工坊下载 提供创意工坊 id 下载到服务器和群聊

### 自定义查服背景图片

插件支持自定义图片背景，在 `data/L4D2/custom_backgrounds/` 目录下放入 PNG/JPG/JPEG 格式图片即可，插件会自动随机选择使用。

具体位置参考 [数据结构](./docs/standand.md)

- 目录不存在时插件会自动创建
- 放入图片无需重启立即生效
- 未放置图片时默认使用纯白色背景

## 安装

以下提到的方法 任选**其一** 即可

<details open>
<summary>[推荐] 使用 nb-cli 安装</summary>
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

- [x] 求生服务器-本地多路径操作（传地图等）
- [x] 批量查询指定 ip 服务器状态和玩家
- [x] connect 指令直接呼出服务器信息
- [x] 根据用户名，在已知服务器搜索玩家信息

## [数据结构](./docs/standand.md)

> 服务器组文件存放位置：`data/L4D2/<组名>.json`（旧版 `data/L4D2/l4d2/` 子目录会在启动时自动迁移）。

## env 设置

```bash
    l4_enable = True
    """是否全局启用求生功能"""
    l4_image = False
    """是否启用图片"""
    l4_connect = True
    """是否在查服命令后加入connect ip"""
    l4_path = "data/L4D2"
    """插件数据路径"""
    l4_players = 4
    """查询总图的时候展示的用户数量"""
    l4_style = "default"
    """图片风格，可选包括以下
    - 简洁
```

## 和 0.x.x 更改部分

## 其他

- anne 部分，已移植到[这里](https://github.com/Agnes4m/L4D2UID),通过 core 插件调用
- 如果您有发现 BUG 或者更好的建议，欢迎提 Issue & Pr
- 如果本插件对你有帮助，不要忘了点个 Star~
- 本项目仅供学习使用，请勿用于商业用途
- [更新日志](./docs/update.md)
- [GPL-3.0 License](https://github.com/Agnes4m/nonebot_plugin_l4d2_server/blob/main/LICENSE) ©[@Agnes4m](https://github.com/Agnes4m)

## 🌐 感谢

- [nonebot2](https://github.com/nonebot/nonebot2)- 聊天机器人的基础框架
- [饼干](https://github.com/lgc2333) - 指导 nonebot2 框架的函数使用
- [wuyi](https://github.com/KimigaiiWuyi/) - 指导 pil 作图

- 感谢以下服主大力支持
  - Michaela's | 机器人功能测试反馈
  - 东 | 提供 docker 部署方法等建议 | [电信服 anne 游戏群](http://qm.qq.com/cgi-bin/qm/qr?_wv=1027&k=6i7r5aJ7Jyg0ejby4rt9GWmFRF53nV1K&authKey=ekMsWepBZPL26%2BfJAG%2F95JD0fhvH39%2BIGVyKOvNlXVDbpIclJlly4kXqukL7JhWR&noverify=0&group_code=883237206)
  - 迷茫 | 催命更新 byd
  - ArcPav | 积极反馈 bug，提供改进思路
