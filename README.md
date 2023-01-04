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


## env配置
| 配置项 | 必填 | 默认值 | 说明 |
|:-----:|:----:|:----:|:----:|
| "l4_file" | 是 | "/home/ubuntu/l4d2/coop" | 输入求生服务器的绝对路径,该目录下有文件夹left4dead2 |

## 功能
（被动）上传地图：私发压缩包zip/vpk文件给机器人，就可以直接上传地图到服务器了

| 指令 | 范围 | 是否需要艾特 | 说明 |
|:-----:|:----:|:----:|:----:|
| 求生地图/求生2地图 | 所有人 | 否 | 获取当前路径下所有的vpk文件，并输出目录 |

## 📝 TODO LIST

- [ ] 帮助文件
- [ ] 支持修改下载地图，在服务器端的名称
- [ ] 支持查询并删除服务器已有地图文件
- [ ] 支持查询服务器状态
- [ ] 支持多服务器切换

## 已知BUG

- [ ] 无法在python3.10版本下解压7z格式压缩包
- [ ] 所有人都可以私聊发送文件


## 📝 更新日志

<details>
<summary>展开/收起</summary>

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
