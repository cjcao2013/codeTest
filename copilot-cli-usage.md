# 使用 GitHub Copilot CLI 触发 TAP 迁移

本文档说明如何通过 GitHub Copilot CLI 使用两个 TAP 迁移 skill。

---

## Skill 一览

| Skill | 文件 | 用途 |
|-------|------|------|
| `tap-migration-assessment` | `.github/instructions/tap-migration-assessment.instructions.md` | 评估项目是否适合迁移到 TAP（pipeline 为主） |
| `tap-data-migration` | `.github/instructions/tap-data-migration.instructions.md` | 迁移 test data / test case 到 TAP |

---

## 前置准备

将 `.github/` 文件夹复制到目标项目仓库：

```bash
cp -r /path/to/tap_migration_skill/.github /path/to/target-project/
```

目录结构确认：

```
target-project/
└── .github/
    ├── copilot-instructions.md
    └── instructions/
        ├── tap-migration-assessment.instructions.md
        └── tap-data-migration.instructions.md
```

---

## Skill 1：tap-migration-assessment（迁移评估）

适用场景：项目有自动化测试 + CI/CD pipeline，想评估是否适合迁移到 TAP。

### 方式一：直接提问

```
帮我评估这个项目迁移到 TAP 的可行性
```

### 方式二：创建评估文件触发（推荐）

```bash
touch ASSESSMENT.md
```

在 Copilot CLI 中：

```
扫描这个项目的测试代码和 CI 配置，按照 TAP 迁移评估方法完成评估，结果写入 ASSESSMENT.md
```

### 方式三：`#file` 显式引用（最可靠）

```
#file:.github/instructions/tap-migration-assessment.instructions.md
扫描项目测试文件，完成 TAP 迁移可行性评估，输出到 ASSESSMENT.md
```

### 评估输出结构

```
# TAP Migration Assessment: [项目名]

## Prerequisites        ← 前置条件确认
## Phase 1: Inventory   ← 当前状态盘点
## Step 1: Pipeline Migration     ← Pipeline 迁移 checklist
## Step 2: Data/Case Migration    ← 数据迁移 checklist（可选）
## Open Questions for TAP Team
```

---

## Skill 2：tap-data-migration（数据迁移）

适用场景：已确认迁移可行，需要把 test data / test case 从本地迁移到 TAP。

### 方式一：直接提问

```
帮我把这个项目的 test data 和 test case 迁移到 TAP
```

### 方式二：`#file` 显式引用（推荐）

```
#file:.github/instructions/tap-data-migration.instructions.md
评估这个项目的 test data 迁移可行性，生成迁移报告
```

### 方式三：创建文件触发

`applyTo` 匹配规则：`**/*migration*`、`**/*tap*`、`**/assess*`、`**/migrate*`

```bash
touch tap-migration-plan.md
```

### 迁移流程

Skill 会引导你完成两个阶段：

**Phase 1 — 评估（assess.py）**
```bash
uv run assess.py --project-dir ./your-tests
# 输出：tap-assessment-report.md
# 结论：Go / Pending / No-go
```

**Phase 2 — 执行（migrate.py）**
```bash
# 先填好 .env（从 TAP 团队获取）
uv run migrate.py --project-dir ./your-tests --env .env
# 输出：tap-migration-report.md
```

---

## 推荐完整流程

```bash
# Step 1: 复制指令文件到目标项目
cp -r /path/to/tap_migration_skill/.github /path/to/target-project/

# Step 2: 进入目标项目
cd /path/to/target-project

# Step 3: 启动 Copilot CLI
copilot
```

**先跑评估：**
```
#file:.github/instructions/tap-migration-assessment.instructions.md
扫描项目的测试文件和 CI 配置，完成 TAP 迁移评估，结果写入 ASSESSMENT.md
```

**评估 Go 后，跑数据迁移评估：**
```
#file:.github/instructions/tap-data-migration.instructions.md
评估 test data 和 test case 的迁移可行性
```

---

## 注意事项

- TAP API 端点和格式需找 TAP 团队确认，skill 中标注为 `[TBD]` 的部分不要假设
- Phase 2 数据迁移必须在 Phase 1 pipeline 迁移稳定后才开始
- 迁移完成前不要删除本地 test data / test case 备份
- `tap-migration-assessment` 的前置条件：项目必须已有自动化测试 + CI/CD pipeline
