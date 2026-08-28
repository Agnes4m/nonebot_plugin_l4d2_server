<!-- markdownlint-disable MD026 MD031 MD033 MD036 MD041 MD046 -->

## 更新记录

### 1.x.x (重构)

- 移除未使用的直接依赖 `rcon` 与 `rarfile`（rar 解压由 `pyunpack`/`patool` 调用系统 `unrar`/`7z` 处理）
- 服务器组存储扁平化：`data/L4D2/l4d2/<tag>.json` → `data/L4D2/<tag>.json`
  - 旧版布局会在启动时自动迁移；旧单文件 `l4d2.json` 在被识别为服务器数据时会拆分为对应组并重命名为 `.bak` 备份
  - 仍保留对旧版 `l4d2/` 子目录与旧版 `l4d2.json` URL 映射的向后兼容读取

### 1.0.0a1

- 基础服务器查询+图片显示
- connect指令访问服务器
