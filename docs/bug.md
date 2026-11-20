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

### Linux：`nonebot-plugin-htmlkit` 装不上 / 编译很久

htmlkit 的预编译 wheel 只有 `manylinux_2_34` 和 `musllinux_1_2` 两套 tag，
**`manylinux_2_34` 要求 glibc ≥ 2.34**：

| 发行版 | glibc | 能直接用 wheel |
| --- | --- | --- |
| Ubuntu 22.04 / 24.04 | 2.35 / 2.39 | ✅ |
| Debian 12 / 13 | 2.36 / 2.41 | ✅ |
| RHEL / Alma / Rocky 9+ | 2.34 | ✅ |
| Alpine（musl） | — | ✅（musllinux_1_2） |
| Ubuntu 20.04 | 2.31 | ❌ |
| Debian 11 | 2.31 | ❌ |
| CentOS 7 | 2.17 | ❌ |
| RHEL / Alma 8 | 2.28 | ❌ |

在不满足的机器上 `pip install` 会退到 sdist 编译，需要 **xmake + C++ 工具链 +
litehtml 子模块**，很慢且容易失败。可行的做法：

1. 直接用 glibc ≥ 2.34 的基础镜像 / 系统（最省事）；
2. 或者在旧系统上用容器跑 bot，宿主只做端口转发；
3. 或者按 htmlkit 的[构建说明](https://github.com/nonebot/plugin-htmlkit)
   自建 wheel 后内网分发。

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

写一份带字族映射的 `fonts.conf`。

**这份配置插件已经自带了**：`render/fonts/fonts.conf`，由
`fontconfig_env.ensure_fontconfig_env()` 在插件 import 时（早于 htmlkit 的
`driver.on_startup`）写进 `FONTCONFIG_FILE`。Windows / Linux 都不需要在 `.env`
里配绝对路径。

想换成自己的配置，再在 bot 的 `.env` 里指过去即可（**键名不要加 `HTMLKIT_`
前缀**，htmlkit 的 `FcConfig` 是按字段名直接从全局配置取的，加前缀反而读不到）：

```dotenv
FONTCONFIG_FILE=/path/to/fonts.conf
```

> 优先级：你设了 `FONTCONFIG_FILE` 就以你的为准——htmlkit 在 startup 时会把
> `os.environ` 覆盖回它的值；没设时用包内那份。

首次生效时会重建一次字体缓存（约 1 秒，之后走缓存）。

> 验证时注意：`init_fontconfig()` 只在 `driver.on_startup` 调用。写脚本单独渲染时
> 如果不手动调一次，走的是 fontconfig 内置默认值，和线上效果不一样
> （仓库根目录的 `tools/render_preview.py` 已经处理了这一点）。

### Linux 上的字体

包内 `fonts.conf` 把 Linux 字体目录（`/usr/share/fonts`、`/usr/local/share/fonts`、
`~/.local/share/fonts`、`~/.fonts`）都列进去了，`sans-serif` 的 prefer 列表依次是
`Microsoft YaHei` → `Noto Sans CJK SC` → `Noto Sans SC` → `Source Han Sans SC` →
`WenQuanYi Micro Hei` → `Segoe UI` → `DejaVu Sans`。

**但系统必须有 CJK 字体，否则汉字是豆腐块**（`DejaVu Sans` 不含汉字）：

```sh
# Debian / Ubuntu
apt-get install -y fonts-noto-cjk      # 或 fonts-wqy-microhei（更小）
# RHEL 系
dnf install -y google-noto-sans-cjk-fonts
```

装完可以用 `fc-list :lang=zh | head` 确认；`fc-match sans-serif:lang=zh` 应当
命中带汉字的字体。

### 中英数大小不一、同一行字形对不上

两个原因，都要处理：

1. **模板字体栈把西文字体排在前面**。`'Segoe UI', 'Microsoft YaHei'` 意味着西文和
   数字走 Segoe UI、汉字回退雅黑，两套字形的 x-height 不同，混排必然一大一小。
   统一改成 `'Microsoft YaHei', 'Segoe UI', sans-serif`——雅黑自带西文与数字字形，
   整行同源。Linux 上没有雅黑，靠 `fonts.conf` 把 `sans-serif` 映射到 CJK 字体。
2. **`normal_old.html` 没有声明 `font-family`**，litehtml 默认给西文用衬线体，汉字
   再逐字回退，问题更明显。`body` 里必须显式声明字体栈。

同理，`.offline-id` 这类「汉字 + 数字」的内容不要单独设 `Consolas`——Consolas 没有
汉字，数字和汉字又会分成两套字形。
