<!-- markdownlint-disable MD026 MD031 MD033 MD036 MD041 MD046 -->

## 更新记录

### 未发布

#### 关键词屏蔽（README「屏蔽与关键词」方案 4）

- 新增配置 `l4_block_keywords`（正则列表，不区分大小写）：服务器名命中则整台隐藏（组查询、`l4全服`、`l4查找`、`l4查人`、tj/zl/kl），单服 / `connect` 查询回「该服务器已被屏蔽」；玩家名命中只隐藏该玩家，人数仍按 A2S 上报，tj/zl/kl 的判断仍按真实玩家列表。
- 过滤逻辑在 `services/blocklist.py`，接在 A2S 结果和输出之间；非法正则记警告后跳过。收藏推送、历史记录不受影响。
- `connect` 查询改为复用单服查询逻辑（`get_ip_server` → `_render_single`）。
- 测试：`tests/test_a2s_cache.py` 加载模块时复用已加载的模块，测试文件之间不再依赖执行顺序。

#### 组查询默认只看有人的服务器 + `云全` + 去掉 `Anne云服#N` 前缀

- `云`（任意组名）默认只列有人的服务器，标题显示「有人的服务器 N 台（在线 x/y 台）」并提示发送 `云全` 查看全部；一台有人的都没有时回一句文字提示，不出空图。
- `云全`（组名 + 「全」）列出全部在线服（含没人的），不在线列表放最后一页；两种模式都按 `l4_image_page_size` 拆成多张图，文字模式（`l4图片 关闭`）同样过滤。
- 列表里的服务器名去掉 `l4_name_strip_pattern` 匹配的前缀（默认 `^Anne云服#\d+`，只匹配 Anne 云服，其他服务器名不受影响）：`Anne云服#57[普通药役][8特20秒]` 显示为 `云57:[普通药役][8特20秒]`；只有前缀的名字保留原样；单服卡片（`云57`）仍显示完整服务器名。
- `l4_image_max_servers` 改为按本次要显示的服务器数判断。
- `tj` 从服务器名的任意一个方括号里解析「N特」：此前只看第一个方括号，`Anne云服#57[普通药役][缺人][无MOD][8特20秒]` 解析失败，`tj` 永远找不到服。

#### 大组分页出图 + 出图兜底 + 刷新指令即时生效

- 组查询（`/云` 等）按 `l4_image_page_size`（默认 30）把在线服分成多张图逐条发送，标题带「第 N/M 页」，不在线列表放最后一页。原来一张图装全组：100 台约 7500px 高，超过 16384px（约 230 台）后 Chromium 截图直接丢内容。
- 出图改 JPEG（体积约为 PNG 的 1/3），同一时刻只开一个 Chromium 页面；浏览器崩溃重试一次，超时不重试；失败的页及同次查询后续各页改用纯 PIL 简易图，不再回复误导性的「服务器无响应」。
- 背景图直接以 `file://` 引用原文件，不再复制进包目录（插件装在只读位置时会导致每次出图失败）。
- `l4图片 关闭` 现在对组查询 / 单服查询都生效（此前被忽略；文字模式下的组查询原本会输出 Python 对象）。
- `l4查看组` / `l4列组` / `l4导出组` / `l4导出全部组` / `l4全服` 超长时按 2000 字一条切分发送；导出 JSON 一台服一行，多条拼起来仍是合法 JSON。
- 刷新指令即时刷新内存：
  - `registry.load_all` 建好新表后一次性替换并加锁，重载途中的查询不会拿到空组；`anne` 等别名重载后不再丢失（此前 l4reload / l4reloadsb 之后 `anne` 失效）。
  - `l4reloadsb` 全部组写完盘后只重载一次；重载时清空 A2S 缓存；SourceBans 抓到 0 台时报错并保留原列表（此前会把整组写空）。
  - `l4删除组` 同步移出内存；运行中新增「云」组后 tj / zl / kl 立即可用。
  - `<组名>.json` 优先于其它文件里的同名组；`favorites.json` / `notify_state.json` 等不再被当成服务器组（此前 `host:port` 会被注册成指令）。
- A2S 缓存：`want_players=False` 的结果不再冒充「没人」给要玩家列表的查询；缓存存独立拷贝，出图改写玩家名不再污染缓存（TTL 内二次查询时长后缀重复）。
- 新增配置 `l4_image_page_size`（1~200，默认 30）。

### 1.4.1

#### A2S 历史 + 跨服模糊查人 + 收藏阈值/Wipe 推送

借鉴 `rust-stats` / `7dtd-watch` / `SzDiscordBot` / `left-for-bot` / `kitasoda_server_bot` 的设计，一次提供三个能力。

- 新增 `services/history.py`（SQLite，Python 3.12+ 自带 `sqlite3`，零新依赖）：
  - `record()` 落 `<data_dir>/history.db`，主键 `(host, port, timestamp)`。
  - `heatmap(host, port, days=7)` 返回 `[(weekday, hour, avg, sample_count)]`；样本 < 3 的格子 `avg` 置 0 避免误导。
  - `detect_wipe(host, port, current_map)` 与上次记录的 `map_name` 对比，变化时返回 `"old → new"`，配合收藏推送给订阅者。
  - `purge_older_than(days)` 启动时清过期记录。
- 新增 `commands/history.py`：
  - `l4热力图 <组> <id或ip> [天数]` — 输出 7×24 ASCII 条形热力图。
- 新增 `commands/fuzzy_search.py`：
  - `l4查人 <玩家名>` — 跨所有组并发查 A2S，用 `difflib` 模糊匹配（容忍空格 / 全角符号 / tag），命中 ≤ 4 直接列，> 4 给精简菜单。
- `services/favorite.py` `run_favorite_check` 升级：
  - 每条 A2S 结果顺带 `history.record()`。
  - **Wipe / 章节切换检测**：`map_name` 与 `notify_state[host:port].last_map` 不一致时推 `🔄 标签N 名称 地图变化 old → new`。
  - **阈值智能通知**：每条 favorite 可独立挂 `thresholds: [int]`，向上跨过阈值才推 `📈 标签N 名称 已达 N 人`，掉回去后再次跨过才重推（避免横跳刷屏）；`notify_state` 加 `last_map` + `fired_thresholds` 字段。
- `__init__.py` `_on_startup` 注册 apscheduler interval 任务 `l4_history_record`（周期 `config.l4_history_interval`，默认 300s），覆盖未被收藏的服；启动时 `purge_older_than(config.l4_history_retention_days)`。
- 新增 config：
  - `l4_history_interval`（int, ge=60, default 300）。
  - `l4_history_retention_days`（int, ge=1, default 30）。

### 1.4.0

#### 数据路径

- 数据根目录固定为 `nonebot_plugin_localstore` 管理的目录（`<cwd>/data/nonebot_plugin_l4d2_server/`），不再支持 `l4_path` / `l4_use_localstore` 自定义。
- 首次启动时若 localstore 空、且插件根自带 `data/L4D2/` 有内容，会自动迁移过去（`services/path_resolver.migrate_legacy`）。原插件根 `data/L4D2/` 保留供用户手动确认后删除。

#### 性能

- A2S 批量查询并发：**默认不限**（`l4_a2s_concurrency=0`，等同于旧版 `asyncio.gather`）。如需在轻量服务器上加节流，把 `.env` 的 `L4_A2S_CONCURRENCY=N` 设成 `>0` 即可。
- A2S 结果按 `(host, port)` TTL 缓存 15 秒（`l4_a2s_cache_ttl`），命中返回 `deepcopy` 防下游 mutate 污染。
- A2S 单服超时 `l4_a2s_timeout=2.5s`（旧版硬编码 3s）。
- 图片渲染加 `asyncio.wait_for(timeout=l4_render_timeout=15)` 硬上限：超过时间 / 异常 / 空字节一律返回 `None`，上层自动 fallback 到纯文字汇总，避免 OneBot WS 心跳丢失后被踢。
- SourceBans 整组刷新 `refresh_all_pages` 改成 `asyncio.Semaphore + gather`，复用 A2S 并发上限。
- 创意工坊批量 `download_many` 用 `Semaphore + gather`（默认 3，`l4_workshop_concurrency`）；新增 `http_helpers.stream_download`（1MB 流式 + total=3600 / connect=30 / sock_read=60 超时），大文件不再 `await resp.read()` 全缓冲。

#### 收藏 / 订阅

- 新增 `services/favorite.py`：每组收藏 `{tag, server_id, host, port, target_group_id, server_name_snapshot, created_at}`，存在 `<data_dir>/favorites.json`；通知状态 `{host:port: {online, player_count, last_check_at, last_alert_at}}` 在 `notify_state.json`。
- 通过 `nonebot_plugin_apscheduler` 注册 interval 任务（`l4_favorite_check_interval=300`），比对 `|Δplayer_count| ≥ l4_favorite_player_delta` 才推，按 `target_group_id` 分群推送避免重复。
- 新指令：`l4收藏 <组> <id>` / `l4取关 <组> <id>` / `l4收藏列表` / `l4通知目标 <组> <id> <群号>` (SUPERUSER)。

#### 单服 CRUD

- 新增 `store/groups.py` 四个异步函数：`add_server` / `remove_server` / `update_server` / `list_servers`。`tag` 不存在时自动建空组。
- `registry._normalize_server_entry` 不再强制重编号 1..N，保留已有 `id`（避免 `云1` 这类后缀指令断号），新增条目按 `max(existing_ids) + 1` 续号。
- `ServerRegistry` 增加 `add_server` / `remove_server` / `update_server` / `get_server` 内存接口，底层走 `store/groups.py` 持久化再回灌 `load_all`。
- 新指令（SUPERUSER）：`l4添加服务器 <组> host:port` / `l4删除服务器 <组> <id或ip>` / `l4修改服务器 <组> <id> <新ip>` / `l4查看组 <组>`。

#### 错误体系

- 新增 `services/errors.py`：`L4Error` 基类 + `L4ServerUnreachableError` / `L4TimeoutError` / `L4InvalidInputError` / `L4NotFoundError` / `L4HTTPError(status=)`。handler 统一 `except L4Error as e: await UniMessage.text(str(e)).finish()`，渐进式替换。

#### 渲染

- 不在线服务器在图片底部以「不在线 (N 台)：云22, 云25, …」文字区块展示，替代原来的红色 🟢 卡片占位。
- `registry._iter_server_files` 跳过空文件（size == 0），容错 `data_dir` 不存在（首次启动前）。

#### 文档 / 黑名单

- README 「屏蔽与关键词 — 实现思路」章节记录四类方案（SourceBans 自动同步 / 本地 JSON 黑名单 / SourceMod HTTP 镜像 / 关键词正则），本期未实现代码。

### 1.x.x (重构)

- 移除未使用的直接依赖 `rcon` 与 `rarfile`（rar 解压由 `pyunpack`/`patool` 调用系统 `unrar`/`7z` 处理）
- 服务器组存储扁平化：`data/L4D2/l4d2/<tag>.json` → `data/L4D2/<tag>.json`
  - 旧版布局会在启动时自动迁移；旧单文件 `l4d2.json` 在被识别为服务器数据时会拆分为对应组并重命名为 `.bak` 备份
  - 仍保留对旧版 `l4d2/` 子目录与旧版 `l4d2.json` URL 映射的向后兼容读取

### 1.0.0a1

- 基础服务器查询+图片显示
- connect指令访问服务器
