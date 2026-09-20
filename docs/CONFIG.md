# L4D2 插件配置旋钮参考

> 适用版本：`nonebot-plugin-l4d2-server` ≥ 1.4.0
> 字段定义在 `nonebot_plugin_l4d2_server/config.py` 的 `ConfigModel`，运行时通过 `.env` / `.env.dev` / `.env.prod` 覆盖。

每个旋钮的命名规则：`L4_<功能域>_<具体项>`。下表按域分组，按"作用 / 默认值 / 推荐范围 / 注意点"展开。

---

## 一、全局开关（5 项）

### `L4_ENABLE` — 是否全局启用求生功能

| | |
|---|---|
| 默认 | `true` |
| 类型 | bool |
| 范围 | - |
| 作用 | 总开关；`false` 时所有命令都不注册 |
| 注意点 | 仅在重启 bot 后生效 |

### `L4_IMAGE` — 是否启用图片模式

| | |
|---|---|
| 默认 | `true` |
| 类型 | bool |
| 作用 | 关闭后 `l4_help` / `l4 <组>` / `l4 <组><id>` 全部走 `messages.Sm` 纯文字汇总 |
| 何时关 | 服务器实在带不动 Chromium；或灰度做对照测试 |

### `L4_CONNECT` — 是否在查服命令后加入 `connect ip:port`

| | |
|---|---|
| 默认 | `true` |
| 类型 | bool |
| 作用 | 单服 / 单组查询的回复末尾追加一行 `connect host:port`，方便玩家一键直连 |
| 何时关 | 群规禁止直连 / 一键指令刷屏 |

### `L4_PLAYERS` — 单服务器卡片展示的玩家数

| | |
|---|---|
| 默认 | `4` |
| 类型 | int (`>=1`) |
| 作用 | 按 score 倒序选 top-N 玩家画进单服卡 |
| 调高影响 | 卡片更高，群友错过的 PVP 大佬上墙更多 |
| 调低影响 | 卡片更矮，超出 N 人部分不显示 |

### `L4_STYLE` — 图片风格

| | |
|---|---|
| 默认 | `"default"` |
| 类型 | str |
| 取值 | `"default"` / `"old"`（其它值会在 `commands/admin.py l4_switch_style` 切换时被忽略，落到 `default`） |
| 作用 | 选择 `render/templates/normal.html` 或 `normal_old.html` 作为整组卡片模板 |
| 注意点 | 单服务器卡（`render_server_card`）不依赖模板，所以 `L4_STYLE` 不影响单服卡 |

### `L4_FONT` — 自定义字体路径

| | |
|---|---|
| 默认 | `""`（走包内 `render/fonts/loli.ttf`） |
| 类型 | str |
| 作用 | 覆盖 PIL 字体；用绝对路径填一个 `.ttf` 或 `.ttc` 文件 |
| 注意点 | 找不到字体时 PIL 会抛 `OSError`；建议包内已带 `loli.ttf` |

### `L4_SHOW_IP` — 单服卡片是否显示 IP

| | |
|---|---|
| 默认 | `true` |
| 类型 | bool |
| 作用 | 单服卡底部是否画 `host:port` 直连行 |
| 何时关 | 同 `L4_CONNECT` 的关停场景 |

### `L4_LOCAL` — 本地 L4D2 服务器路径列表

| | |
|---|---|
| 默认 | `[]` |
| 类型 | `list[str]` |
| 作用 | 给 `l4本地地图` / `l4本地上传` / `l4本地改名` / `l4本地删除` 用 |
| 格式 | JSON 数组，例如 `L4_LOCAL=["D:\\steamcmd\\l4d2"]` |
| 注意点 | 每条路径下必须有 `steam_appid.txt`（`ConfigModel.validate_local_paths` 会跳过缺文件的条目并打 warning） |

### `L4_PERMISSION` — 上传本地地图权限位

| | |
|---|---|
| 默认 | `1` |
| 类型 | int (`1..4`) |
| 取值 | `1=SUPERUSER` / `2=SUPERUSER\|群主` / `3=SUPERUSER\|群主\|群管` / `4=SUPERUSER\|群主\|群管\|群员` |
| 作用 | 控制 `l4本地上传` / `l4本地改名` / `l4本地删除` / `l4创意工坊` 的最低触发权限 |

---

## 二、A2S 性能（3 项）

### `L4_A2S_CONCURRENCY` — A2S 并发上限

| | |
|---|---|
| 默认 | `8`（注意：`config.py` 实际默认 `0`，dev 环境覆写到 `8`） |
| 类型 | int (`0..64`) |
| 作用 | `L4API._a2s_one` 入口 `asyncio.Semaphore` 容量；>0 走节流，`0` 不限并发（一次性 `asyncio.gather`，旧版行为） |
| 推荐 | 2C2G 服务器 `8-16`；本地调试 `0`；公网 8 服以上组 `4-8` |
| 注意点 | 过低（如 `1`）会阻塞；过高容易 UDP 丢包 |

### `L4_A2S_TIMEOUT` — 单次 A2S UDP 超时秒

| | |
|---|---|
| 默认 | `2.5` |
| 类型 | float (`>0`) |
| 作用 | `a2s.ainfo` / `a2s.aplayers` 的超时 |
| 推荐 | 公网 ≥ 2.0；同机房 1.0-1.5 |

### `L4_A2S_CACHE_TTL` — A2S 结果缓存秒

| | |
|---|---|
| 默认 | `15` |
| 类型 | int (`>=0`) |
| 作用 | 同一 `(host, port)` 在 TTL 内直接返回缓存，避免群里 `/云` 触发的 N 次重复 UDP |
| 推荐 | 群场景 10-30 秒；独服 0（不缓存，每次最新） |
| 注意点 | 命中时 `deepcopy` 返回，下游 mutate 不会污染缓存条目 |

---

## 三、收藏 / 订阅（2 项）

### `L4_FAVORITE_CHECK_INTERVAL` — 收藏巡检周期秒

| | |
|---|---|
| 默认 | `300` |
| 类型 | int (`>=30`) |
| 作用 | `nonebot_plugin_apscheduler` 注册的 interval 任务 `l4_favorite_check` 的间隔 |
| 推荐 | 30-600；调低增加推送频率但提高 UDP 压力 |
| 注意点 | 第一轮在 `next_run_time=None` 下不会立即触发，避免抢 `on_startup` 资源 |

### `L4_FAVORITE_PLAYER_DELTA` — 玩家数变化阈值

| | |
|---|---|
| 默认 | `5` |
| 类型 | int (`>=1`) |
| 作用 | `|Δplayer_count|` ≥ 此值才向订阅群推送在线人数变化 |
| 推荐 | 普通群 5-10；游戏厅群 10-20 |

---

## 四、创意工坊（1 项）

### `L4_WORKSHOP_CONCURRENCY` — 工坊并发下载数

| | |
|---|---|
| 默认 | `3` |
| 类型 | int (`1..8`) |
| 作用 | `download_many` 用 `asyncio.Semaphore` 限制并发 |
| 推荐 | 3（默认）；Steam CDN 偶尔限速可降到 2；本机带宽大可上 5 |
| 注意点 | 超过 8 触发 pydantic `le=8` 校验失败，配置加载就报错 |

---

## 五、渲染 / 图片（2 项）

### `L4_RENDER_TIMEOUT` — 单次出图硬上限秒

| | |
|---|---|
| 默认 | `15.0` |
| 类型 | float (`>0`) |
| 作用 | `asyncio.wait_for(html_to_pic(...), timeout=L4_RENDER_TIMEOUT)` |
| 注意点 | 超时 / 异常 / 空字节一律 `None`，上层 fallback 到文字或简短"超时"提示；这是防 OneBot WS 心跳丢失的关键开关 |

### `L4_IMAGE_MAX_SERVERS` — 大组跳图阈值

| | |
|---|---|
| 默认 | `0`（不限；按 commit `51313b5` 把早期 20 改回 0） |
| 类型 | int (`>=0`) |
| 作用 | 当组内服务器数 > 此值时跳过 Chromium 出图，直接发简短提示文本 |
| 推荐 | 2C2G 服务器设 `15-20`；本地测试 `0`；7 服以下小群 `0` 即可 |
| 注意点 | 仅 `l4 <组>` 整组查询时判断；单服 / 单 ip 查询不受影响 |

---

## 六、A2S 历史（SQLite，2 项）

### `L4_HISTORY_INTERVAL` — A2S 历史记录周期秒

| | |
|---|---|
| 默认 | `300` |
| 类型 | int (`>=60`) |
| 作用 | `_start_history_recorder` 注册的 interval 任务 `l4_history_record` 周期 |
| 推荐 | 同 `L4_FAVORITE_CHECK_INTERVAL`（300 秒），避免两者抢资源 |
| 注意点 | 收藏巡检已经会写历史，本任务专门覆盖**未被收藏**的服，保证"查而不收藏"的服也有历史曲线 |

### `L4_HISTORY_RETENTION_DAYS` — 历史保留天数

| | |
|---|---|
| 默认 | `30` |
| 类型 | int (`>=1`) |
| 作用 | 启动时调用 `purge_older_than(days)` 清理过期记录 |
| 注意点 | 热力图 `l4热力图` 最多看 30 天（命令参数限制 `1-30`），保留期再长也用不到 |

---

## 速查表

| 旋钮 | 默认 | 域 |
|---|---|---|
| `L4_ENABLE` | `true` | 全局 |
| `L4_IMAGE` | `true` | 全局 |
| `L4_CONNECT` | `true` | 全局 |
| `L4_PLAYERS` | `4` | 全局 |
| `L4_STYLE` | `"default"` | 全局 |
| `L4_FONT` | `""` | 全局 |
| `L4_SHOW_IP` | `true` | 全局 |
| `L4_LOCAL` | `[]` | 全局 |
| `L4_PERMISSION` | `1` | 权限 |
| `L4_A2S_CONCURRENCY` | `0`（不限）→ dev 覆 `8` | A2S |
| `L4_A2S_TIMEOUT` | `2.5` | A2S |
| `L4_A2S_CACHE_TTL` | `15` | A2S |
| `L4_FAVORITE_CHECK_INTERVAL` | `300` | 收藏 |
| `L4_FAVORITE_PLAYER_DELTA` | `5` | 收藏 |
| `L4_WORKSHOP_CONCURRENCY` | `3` | 工坊 |
| `L4_RENDER_TIMEOUT` | `15.0` | 渲染 |
| `L4_IMAGE_MAX_SERVERS` | `0`（不限） | 渲染 |
| `L4_HISTORY_INTERVAL` | `300` | 历史 |
| `L4_HISTORY_RETENTION_DAYS` | `30` | 历史 |

---

## 修改历史

- 1.4.0：新增 `L4_A2S_*` / `L4_FAVORITE_*` / `L4_WORKSHOP_*` / `L4_RENDER_TIMEOUT` / `L4_LOCAL` / `L4_PERMISSION`
- 1.4.0：新增 `L4_IMAGE_MAX_SERVERS`（commit `2af33d1`，早期默认 20，commit `51313b5` 改回 0 不限）
- 1.4.1（草案，未发布）：新增 `L4_HISTORY_INTERVAL` / `L4_HISTORY_RETENTION_DAYS`，回退版本号后保留