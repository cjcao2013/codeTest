# 使用 GitHub Copilot CLI 触发 TAP 迁移评估

## 前置准备

将 `.github/` 文件夹复制到目标项目仓库：

```bash
cp -r /path/to/tap_migration_skill/.github /path/to/target-project/
```

目录结构确认：

```
target-project/
└── .github/
    ├── copilot-instructions.md                          # TAP 背景 + 角色定义（自动加载）
    └── instructions/
        └── tap-migration-assessment.instructions.md     # 六阶段评估方法论（按需加载）
```

---

## 启动 Copilot CLI

```bash
cd /path/to/target-project
copilot   # 启动 Copilot CLI（公司内部命令可能不同）
```

如需切换模型：

```
/model claude-sonnet-4-5
```

---

## 三种触发方式

### 方式一：直接提问（最简单）

适用于快速了解评估方向，`copilot-instructions.md` 会自动加载。

```
帮我评估这个项目迁移到 TAP 的可行性
```

---

### 方式二：创建评估文件触发（推荐）

创建文件名匹配 `applyTo` 模式的输出文件，完整六阶段方法论自动加载。

```bash
touch ASSESSMENT.md
```

在 Copilot CLI 中：

```
扫描这个项目的测试代码和 CI 配置，按照六阶段 TAP 迁移评估方法完成评估，结果写入 ASSESSMENT.md
```

`applyTo` 匹配规则：`**/*migration*`、`**/*assessment*`、`**/*tap*`、`**/ASSESSMENT*.md`、`**/MIGRATION*.md`

---

### 方式三：`#file` 显式引用（最可靠）

无论文件名如何，强制加载完整评估方法论。

```
#file:.github/instructions/tap-migration-assessment.instructions.md 扫描项目测试文件，完成 TAP 迁移可行性评估，输出到 ASSESSMENT.md
```

---

## 推荐完整流程

```bash
# Step 1: 复制指令文件到目标项目
cp -r /path/to/tap_migration_skill/.github /path/to/target-project/

# Step 2: 进入目标项目，创建评估输出文件
cd /path/to/target-project
touch ASSESSMENT.md

# Step 3: 启动 Copilot CLI
copilot
```

在 Copilot CLI 中执行：

```
#file:.github/instructions/tap-migration-assessment.instructions.md
扫描项目的测试文件、CI 配置和技术栈，按六阶段方法完成 TAP 迁移可行性评估，结果写入 ASSESSMENT.md
```

---

## 评估输出结构

Copilot CLI 会将结果写入 `ASSESSMENT.md`，包含以下章节：

```
# TAP Migration Assessment: [项目名]

## 1. Project Profile
## 2. Capability Mapping
## 3. Risk Score
## 4. Gap Analysis
## 5. Recommendation      ← GO / PHASED GO / NO-GO
## 6. Migration Plan
## 7. Open Questions for TAP Team
```

---

## 注意事项

- Phase 2 中标注为 **Unknown** 的 TAP 能力，必须找 TAP 团队确认后才能给出最终 GO 建议
- 如项目没有现有测试代码，不适用本评估流程，应先讨论测试策略
- 评估完成后，将 `ASSESSMENT.md` 连同 `Open Questions` 一并发给 TAP 团队确认
