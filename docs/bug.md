<!-- markdownlint-disable MD026 MD031 MD033 MD036 MD041 MD046 -->

## 模块pypi包缺失

Q: 出现模块找不到的问题
A: 部分依赖nb子插件需要require，这个是nb规范要求的，因此这些子插件必须也使用nb导入，你可以使用以下代码解决

```sh
nb plugin install nonebot_plugin_apscheduler
nb plugin install nonebot_plugin_saa
nb plugin install nonebot_plugin_htmlrender
nb plugin install nonebot_plugin_txt2img
```
