<!-- markdownlint-disable MD026 MD031 MD033 MD036 MD041 MD046 -->

## 模块pypi包缺失

Q: 出现模块找不到的问题
A: 部分依赖nb子插件需要require，这个是nb规范要求的，偶尔会出现require失败的情况，你可以使用以下代码解决

```sh
nb plugin install nonebot_plugin_saa
nb plugin install nonebot_plugin_htmlkit
```

## 出图相关（已改用 htmlkit）

出图已从 `nonebot-plugin-htmlrender` + Chromium 换成 `nonebot-plugin-htmlkit` +
litehtml，本地 C++ 渲染，**不再需要安装浏览器内核**，也不用 `playwright install`。

- 旧版遗留的 `nonebot-plugin-htmlrender`、`playwright` 可以卸载，
  `~/.cache/ms-playwright` 目录也可以删掉（省 300 MB+）。
- litehtml 不支持 `flex` / `grid` / `calc()` / SVG 图标，模板已按此约束重写；
  自定义样式时注意别用这几样。

### 启动时报 `Fontconfig error: Cannot load default config file`

现象：

```
[INFO] nonebot_plugin_htmlkit | Initializing fontconfig...
Fontconfig error: Cannot load default config file: No such file: (null)
[INFO] nonebot_plugin_htmlkit | Fontconfig initialized.
```

**这是无害的**。htmlkit 内嵌 fontconfig，它在 Windows 上找不到默认的 `fonts.conf`
（系统本来就不提供），于是打印这行，然后回退到内置默认配置——默认配置里已包含
`C:/Windows/Fonts`，所以字体照常解析。实测同一页面加不加这份配置，出图内容一致。

想去掉这行，写一份最小的 `fonts.conf`：

```xml
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">
<fontconfig>
  <dir>C:/Windows/Fonts</dir>
  <cachedir>~/.cache/fontconfig</cachedir>
</fontconfig>
```

然后在 bot 的 `.env` 里指向它（**键名不要加 `HTMLKIT_` 前缀**，htmlkit 的 `FcConfig`
是按字段名直接从全局配置取的，加前缀反而读不到）：

```dotenv
FONTCONFIG_FILE=E:/path/to/fonts.conf
```

首次生效时会重建一次字体缓存（约 1 秒，之后走缓存）。
