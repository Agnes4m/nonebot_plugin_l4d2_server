# 插件功能大纲（更新版）

> 本文档梳理「最初需求 → 当前实现状态」，对老条目做了归档。
> 详细历史见 `docs/update.md`；测试见 `tests/`。

## 一、最初功能需求

| 需求 | 状态 | 命令入口 |
|---|---|---|
| 电信服信息查询 | ✅ 已完成 | `l4 云` / `l4 anne` / `l4 云<id>` |
| 全服务器 ip 查询 | ✅ 已完成 | `l4_all` / `l4全服` |
| 本地服务器传图 | ✅ 已完成（zip/7z/rar 解压，GBK 文件名 fallback） | `l4本地地图` / `l4本地上传` |
| 创意工坊批量下载 | ✅ 已完成（流式 + 并发限流 + 进度回调） | `l4创意工坊` |
| 喷漆功能 | ⏳ 未实现 | - |
| 删除定时推送 | 🚫 已弃（旧需求） | - |
| 删除重启功能 | 🚫 已弃（旧需求） | - |
| 删除网页控制台 | 🚫 已弃（旧需求） | - |

## 二、历史痛点（1.x.x 前的「当前问题」）

| 痛点 | 解决状态 |
|---|---|
| 插件结构混乱 | ✅ 已分层：`api/` / `commands/` / `services/` / `store/` / `render/` |
| 图片用浏览器，占用大 | 🟡 htmlrender 仍依赖 Chromium；加了 `l4_render_timeout` 熔断 + `l4_image_max_servers` 跳图 |
| 图片不好看 | 🟡 视觉调优仍在持续，主体走 user_backgrounds 目录自定义 |
| 传图 bug | ✅ `services/local_server.py` 抽 `_unzip` 走 cp437→gbk 修复中文化文件名 |
| 创意工坊+喷漆 bug | 🟡 创意工坊修了（流式下载、并发限流、状态分桶 ok/duplicate/invalid/download_failed），喷漆未做 |

## 三、当前活跃待办（已迁 P3 / P4 跟进）

- [ ] **P0 测试**：重写 `tests/test_migrate.py` 和 `tests/test_registry.py` 以匹配现版包结构
- [ ] **P3 旋钮文档化**：在 `.env.dev` / `.env.prod` 写完整 `L4_*` 旋钮默认值，README 同步说明每条含义
- [ ] **P4 知识库**：把 `docs/update.md` 的关键设计决策（缓存 / 幂等 Trie / 熔断 / 历史合一）灌给 Hindsight
- [ ] **`.gitignore`**：`docs/` 历史方案文件被 git 跟踪但实际是开发期产物，确认是否要 untrack

## 四、未来方向（开放式）

- 黑名单：本地 JSON 黑名单 + 关键词正则（README 「屏蔽与关键词」章节有方案）
- SourceMod HTTP 镜像 / Anne 鉴权接口
- 跨机器人同步收藏