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

**这行本身无害**（htmlkit 内嵌的 fontconfig 会回退到内置默认值，字体照样找得到），
但**不要就这么放着**：缺 `fonts.conf` 时 `sans-serif` / `monospace` 这类通用字族
没有映射规则，fontconfig 会给出一套缺汉字覆盖的字体，litehtml 只能按字形逐个回退，
于是同一行里的中文、英文、数字来自不同字体——大小、字重、基线全对不上（看着「东倒西歪」）。

写一份带字族映射的 `fonts.conf`：

```xml
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">
<fontconfig>
  <dir>C:/Windows/Fonts</dir>
  <cachedir>~/.cache/fontconfig</cachedir>

  <match target="font">
    <edit name="antialias" mode="assign"><bool>true</bool></edit>
    <edit name="hinting" mode="assign"><bool>true</bool></edit>
    <edit name="hintstyle" mode="assign"><const>hintslight</const></edit>
    <edit name="rgba" mode="assign"><const>none</const></edit>
  </match>

  <alias binding="same">
    <family>sans-serif</family>
    <prefer><family>Microsoft YaHei</family><family>Segoe UI</family></prefer>
  </alias>
  <alias binding="same">
    <family>monospace</family>
    <prefer><family>Consolas</family><family>Microsoft YaHei</family></prefer>
  </alias>
</fontconfig>
```

然后在 bot 的 `.env` 里指向它（**键名不要加 `HTMLKIT_` 前缀**，htmlkit 的 `FcConfig`
是按字段名直接从全局配置取的，加前缀反而读不到）：

```dotenv
FONTCONFIG_FILE=E:/path/to/fonts.conf
```

首次生效时会重建一次字体缓存（约 1 秒，之后走缓存）。

> 验证时注意：`init_fontconfig()` 只在 `driver.on_startup` 调用。写脚本单独渲染时
> 如果不手动调一次，走的是 fontconfig 内置默认值，和线上效果不一样。

### 中英数大小不一、同一行字形对不上

两个原因，都要处理：

1. **模板字体栈把西文字体排在前面**。`'Segoe UI', 'Microsoft YaHei'` 意味着西文和
   数字走 Segoe UI、汉字回退雅黑，两套字形的 x-height 不同，混排必然一大一小。
   统一改成 `'Microsoft YaHei', 'Segoe UI', sans-serif`——雅黑自带西文与数字字形，
   整行同源。
2. **`normal_old.html` 没有声明 `font-family`**，litehtml 默认给西文用衬线体，汉字
   再逐字回退，问题更明显。`body` 里必须显式声明字体栈。

同理，`.offline-id` 这类「汉字 + 数字」的内容不要单独设 `Consolas`——Consolas 没有
汉字，数字和汉字又会分成两套字形。
