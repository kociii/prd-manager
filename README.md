# prd-manager

让 AI 按"需求 → 设计 → 技术方案 → 计划 → 验收"的顺序，把一个版本的文档写清楚、管得住。

当前版本 **0.2.0**，更新记录见 [CHANGELOG.md](./CHANGELOG.md)。

## 它解决什么问题

- **AI 编码容易跑偏**：需求、页面、技术方案混在一起，模型只能猜。这里每份文档只回答一个问题，AI 读哪份、改哪份都有边界。
- **文档写完就乱**：版本一多，状态、编号、变更记录各写各的。这里用统一的状态和 ID 规则，并提供脚本检查。
- **验收没有依据**：每条需求带"操作 + 可观察结果"的验收标准，并能追到页面、任务和测试。

## 一个版本里有什么

文档放在 `docs/prd/<version>/`，按请求范围生成，不会默认铺满全套。

| 文档 | 回答的问题 |
|------|-----------|
| `prd.md` | 做什么、为什么：原话、分析、范围、流程、验收标准 |
| `design.md` | 长什么样：多页面 ASCII 线框、布局层级、交互与状态 |
| `dev.md` | 怎么实现：架构、契约、不变量、接口与文件影响 |
| `database.md` | 数据怎么存：字段、枚举、约束、迁移依据 |
| `plan.md` / `tasks/` | 先做什么：顺序、依赖、可验证的任务 |
| `test.md` | 怎么验证：需求映射、边界、证据、业务验收 |
| `review.md` | 实现可信吗：偏差、缺陷、修复证据 |
| `ops.md` | 怎么上线与回滚 |
| `incidents/` | 事故的根因、影响与防护 |

跨版本的两份放在 `docs/prd/` 根部：`README.md`（版本索引，倒序）和 `CHANGELOG.md`（所有版本合一，Unreleased 置顶）。

默认推进顺序：`prd.md` 确认 → `design.md` / `dev.md` 确认 → `plan.md` → 更新索引。写错的边界要拦住：PRD 不放接口和字段，plan 不重复架构，dev 引用需求 ID 而不是复制需求。

## 版本怎么管（0.2.0 新增）

**状态只有一套**

```text
草案 → 待评审 → 已确认 → 开发中 → 已验收 → 已发布
                 (基线)                        (冻结)
```

旁支终态：已取代、已取消、已归档。

- 已确认之后改需求，必须在 `prd.md` 的修订记录里追加一行。
- 是否"已发布"以 `CHANGELOG.md` 里带日期的版本条目为准。
- 原版本修还是开新版本，只看状态：没到已发布就在原版本修；已发布后只允许勘误，其余开新版本。

**编号只增不复用**

- 需求用 `S`、功能点用 `F`、待决问题用 `Q`、页面用 `D`、任务用 `T`。`P0`–`P3` 只表示优先级。
- 移除的编号保留并标"已移除"；拆分、合并要写明去向。
- 新版本只写增量，用 `based_on` 指向上一版，需求表用"变更类型"列区分新增、变更、沿用、移除。

**生成的文档带头部**

```yaml
---
version: v0.2.0
status: 已确认
based_on: v0.1.0
skill_version: 0.2.0
updated: 2026-10-30
---
```

遇到没有这些字段的旧文档，skill 会先列出差异、征得同意，再增量补齐，不覆盖已有内容。流程见 [references/migration.md](./references/migration.md)。

## 一致性检查

```bash
python3 scripts/check_docs.py docs/prd                 # 检查
python3 scripts/check_docs.py docs/prd --freeze v1.0.0 # 为已发布版本写冻结清单
python3 scripts/validate_ascii.py docs/prd/v1.0.0/design.md  # 线框图排版
```

`check_docs.py` 只用标准库，按 ERROR / WARNING 分级，有 ERROR 时退出码为 1。检查项：

- 版本目录与 README 索引是否一致、是否倒序
- 状态是否在枚举内，"已发布"是否有 CHANGELOG 依据
- ID 是否重复、已移除的 ID 是否被复用、上一版的 ID 是否无故消失
- 链接和锚点是否存在，每个功能点是否被下游文档引用
- 已冻结的文件是否被改动

## 安装

```bash
git clone https://github.com/kociii/prd-manager ~/.claude/skills/prd-manager
```

## 怎么用

直接描述想做的事，范围说得越清楚，产出越贴合。例如：

- `/prd-manager 做一个 v0.3.0 用户认证版本，先整理成 PRD。后台系统，角色分员工和管理员；要有账号登录、短信登录、找回密码、首次改密；P0 先保证登录注册闭环。`
- `用 prd-manager 给 v0.2.4 加一个视频播放器需求，只输出 prd.md，再告诉我要不要补 design.md 和 dev.md。`
- `帮我看看所有 PRD 版本的状态，哪些文档还缺。`
- `对比 v0.2.0 和 v0.3.0：业务上新增了什么、移除了什么、优先级怎么变。`
- `v0.1.0 已发布，S2 的验收文案写错了，帮我勘误。`（只会做勘误并记入 CHANGELOG）
- `这个项目的 docs/prd 是旧格式，帮我升级到新规范。`
- `检查 docs/prd 的文档是否一致。`

## 仓库结构

```text
.
├── SKILL.md           # 入口：路由与核心规则
├── VERSION
├── CHANGELOG.md       # skill 自身的版本记录
├── assets/            # 各类文档模板
├── references/        # 场景指南；生命周期见 lifecycle.md，迁移见 migration.md
├── scripts/           # check_docs.py、validate_ascii.py
├── agents/
└── evals/             # evals.json 与 files/ 夹具
```

## 评测

`evals/evals.json` 覆盖：新建与初始化版本、冲突处理、按需单文档、状态查看、扩展、对比、搜索、归档，以及 0.2.0 加入的已发布勘误、基线后改需求、ID 拆分与移除、旧格式迁移、一致性检查。`evals/files/` 是配套夹具，复制到临时项目后再运行对应 prompt，内容为示例，不代表真实项目。

## 许可证

MIT，详见 [LICENSE](./LICENSE)。
