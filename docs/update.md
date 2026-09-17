<!-- markdownlint-disable MD026 MD031 MD033 MD036 MD041 MD046 -->

## 更新记录

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
