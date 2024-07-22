<!-- markdownlint-disable MD026 MD031 MD033 MD036 MD041 MD046 -->

## 模块pypi包缺失

Q: 出现模块找不到的问题
A: 部分依赖nb子插件需要require，这个是nb规范要求的，偶尔会出现require失败的情况，你可以使用以下代码解决

```sh
nb plugin install nonebot_plugin_saa
nb plugin install nonebot_plugin_htmlrender
```

## winserver2008 无法启用浏览器

这是winserver2008特有的问题，解决办法有以下几种
 - 换用其他浏览器，比如firefox
 - 换winserver2012，或者换其他版本的windows
 - 直接用linux或者虚拟机
