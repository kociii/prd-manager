# CHANGELOG

遵循 Keep a Changelog 与语义化版本。

## [0.2.0] - 2026-10-30

### Added
- `references/lifecycle.md`：统一状态机（草案→待评审→已确认→开发中→已验收→已发布）、基线与冻结、需求 ID 生命周期、修订记录。
- `references/migration.md`：旧格式文档迁移流程。
- `scripts/check_docs.py`：版本目录/README 一致性、状态枚举、ID 唯一与不消失、链接、引用、冻结清单校验。
- `VERSION` 与本 CHANGELOG；生成文档 front matter 带 `skill_version`。
- `prd_template`：front matter、变更类型列、待决问题表（状态/决定/日期）、修订记录表。

### Changed
- CHANGELOG 模板改为单文件 `docs/prd/CHANGELOG.md`，Unreleased 置顶，支持 `[YANKED]`，去除项目专属示例。
- 页面 ID 前缀 `P01` 改为 `D01`，避免与优先级 P0/P1 冲突。
- `plan_template`/`readme_template` 状态改用统一枚举。
- `SKILL.md`「版本与状态」改为以状态判定“原版本修/开新版本”。

### Notes
- 0.1.0 之后、本版之前的手工迭代（含任务/审查/测试等扩展模板）未单独记录，此版为首次纳入 git 管理的基线整理。
