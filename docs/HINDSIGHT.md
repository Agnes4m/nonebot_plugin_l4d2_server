# Hindsight 知识库状态

> 计划：把 v1.4.0 关键设计决策（缓存 / Trie / 渲染熔断 / 历史合一）灌给
> Hindsight，让后续会话能直接召回。

## 当前状态

- Hindsight API 当前不可达（`api_token_configured: false`，401 Unauthorized）。
- 见 `hindsight_diagnose` 输出：
  - `bank_id=coding-agent::nb2`
  - `api_url=https://api.hindsight.vectorize.io`
  - **缺 API token**

## 备选路径

在没有 token 的情况下，会话用 `engram_save`（跨会话记忆系统）保存关键事实：

| 主题 | engram placard |
|---|---|
| A2S / Trie 注册时序 | `l4d2 v1.4.0 A2S/Trie 注册时序`（事实厅#1） |
| 渲染熔断防 WS 掉线 | `l4d2 渲染熔断防 WS 掉线`（技法坊#1） |
| 数据目录 cwd 强绑 | `l4d2 数据目录 cwd 强绑`（事实厅#2） |
| L4Error 子类分层 | `l4d2 L4Error 子类分层`（事实厅#3） |
| 测试新旧不兼容 | `l4d2 测试新旧不兼容`（事实厅#4） |

## 启用 Hindsight 的步骤

1. 在 Hindsight 控制台 / 配置面板生成 API token
2. 写入 `~/.hindsight/coding-agent.json` 的 `api_token` 字段
3. 重启 DSH Desktop，下次会话会自动用新 token 鉴权
4. 跑 `hindsight_sync_status` 验证 bank 同步状态

## 待灌入内容（token 恢复后）

按 `docs/update.md` 1.4.0 章节拆 6 个独立记忆：

1. A2S 性能要点（cache + deepcopy + Semaphore）
2. Trie 规则幂等写入
4. 数据路径 cwd-based（path_resolver 决策）
5. 错误体系（L4Error + 边界处理）
6. 测试现状（a2s_cache OK，migrate/registry 待重写）

每个记忆 importance 0.7-0.85，scope=project。