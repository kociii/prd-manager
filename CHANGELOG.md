# CHANGELOG

遵循 Keep a Changelog 与语义化版本。

## [0.3.0] - 2026-10-30

### Added
- **版本文档同步纪律**（SKILL.md「版本与状态」节）：实质代码 push 后必须回主仓库同步对应版本 PRD——**一版一条记录**（未完成记过程态、完成更新同一条，禁止一版多行）；README 长表只留当前态摘要，过程叙事下沉版本目录 CHANGELOG.md；**完成度总览一眼表**随状态原地同步；发布基准以线上版本号 ancestry 验证为准；涉 DDL 版本放 checklist.md（表名/列对照 DO 注解核实）。
- `references/incremental-iteration.md`：变更影响表新增「代码 push」行；列版本节加总览表同步要求。

### Changed
- CHANGELOG 落点适配：保留单文件 `docs/prd/CHANGELOG.md` 为默认，**项目约定优先**——LongSky 现行为版本目录内 `CHANGELOG.md`（一版一条追加），沿用项目约定。

## [0.2.0] - 2026-10-30

### Added
- `references/lifecycle.md`：统一状态机（草案→待评审→已确认→开发中→已验收→已发布）、基线与冻结、需求 ID 生命周期、修订记录。
- `references/migration.md`：旧格式文档迁移流程。
- `scripts/check_docs.py`：版本目录/README 一致性、状态枚举、ID 唯一与不消失、链接、引用、冻结清单校验。
- `VERSION` 与本 CHANGELOG；生成文档 front matter 带 `skill_version`。
- `prd_template`：front matter、变更类型列、待决问题表（状态/决定/日期）、修订记录表。
- `evals/files/`：20 个评测夹具；eval 2、8 修正，新增 5 条带 expectations 的生命周期评测。
- `check_docs.py`：跨版本 ID 消失检测。

### Changed
- CHANGELOG 模板改为单文件 `docs/prd/CHANGELOG.md`，Unreleased 置顶，支持 `[YANKED]`，去除项目专属示例。
- 页面 ID 前缀 `P01` 改为 `D01`，避免与优先级 P0/P1 冲突。
