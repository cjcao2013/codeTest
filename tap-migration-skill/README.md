# 使用 GitHub Copilot CLI 进行 TAP 迁移评估

## 这个 skill 做什么

将 `.github/instructions/` 复制到任意自动化测试项目，GitHub Copilot 就能读懂这两个 skill：

| Skill | 文件 | 用途 |
|-------|------|------|
| `tap-migration-assessment` | `tap-migration-assessment.instructions.md` | 评估项目是否适合迁移到 TAP，输出 Go / Pending / No-go |
| `tap-data-migration` | `tap-data-migration.instructions.md` | 将 test data / test case 从本地迁移到 TAP |

两个 skill 顺序使用：先评估，通过后再迁移。

---

## 前置准备

将 `.github/` 复制到目标项目：

```bash
cp -r /path/to/tap_migration_skill/.github /path/to/target-project/
```

目录结构：

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

评估一个项目是否适合迁移到 TAP，给出结构化报告和明确结论。

### 触发方式

```
#file:.github/instructions/tap-migration-assessment.instructions.md
扫描这个项目，完成 TAP 迁移评估，结果写入 ASSESSMENT.md
```

### Copilot 会做什么

1. 确认前置条件（有自动化测试 + CI/CD pipeline）
2. 自动运行 `assess.py` 获取 framework、test count、data format
3. 填写 pipeline 和测试资产清单
4. 给出明确结论：

```
Recommendation: Go — pytest project with GitHub Actions already configured; Step 1 can start immediately.
```

### 输出结构

```
ASSESSMENT.md
├── Prerequisites          ← 前置条件是否满足
├── Phase 1: Inventory     ← pipeline 配置 + 测试资产清单
├── Step 1: Pipeline       ← 迁移 checklist + 风险项
├── Step 2: Data/Cases     ← 数据迁移 checklist（可选）
├── Recommendation         ← Go / Pending / No-go + 理由
└── Open Questions         ← 需要 TAP 团队确认的问题
```

---

## Skill 2：tap-data-migration（数据迁移）

在 Step 1（pipeline 迁移）稳定后，将 test data / test case 迁入 TAP。

### 触发方式

```
#file:.github/instructions/tap-data-migration.instructions.md
评估并执行 test data 迁移
```

### 迁移流程

**Phase 1 — 评估**

```bash
cd tap-migration
uv run assess.py --project-dir ../target-project
# 输出：tap-assessment-report.md（Go / Pending / No-go）
```

**Phase 2 — 执行**（评估为 Go 后）

```bash
# 先填 .env（从 TAP 团队获取）
cp .env.example .env

# 测试运行（不上传）
uv run migrate.py --project-dir ../target-project --dry-run

# 正式迁移
uv run migrate.py --project-dir ../target-project --env .env

# 带进度延迟（demo 演示用）
uv run migrate.py --project-dir ../target-project --env .env --upload-delay 0.5
```

---

## 本地 Demo 演示

使用内置的 demo 项目 + mock TAP 服务器，无需真实 TAP 环境。

**启动 mock TAP 服务：**

```bash
cd mock-tap
uv run uvicorn main:app --reload --port 8001
```

**启动前端：**

```bash
cd frontend && npm install && npm run dev   # http://localhost:5173
cd api && uv run uvicorn main:app --reload  # http://localhost:8000
```

**跑 demo 项目评估：**

```bash
cd tap-migration
uv run assess.py --project-dir ../demo-project
```

**跑 demo 项目迁移：**

```bash
cp .env.example .env  # 填入 mock-tap 地址 http://localhost:8001
uv run migrate.py --project-dir ../demo-project --env .env --upload-delay 0.5
```

---

## .env 配置说明

```bash
TAP_API_BASE_URL=http://localhost:8001   # demo 用 mock-tap；正式用 TAP 团队提供的地址
TAP_API_TOKEN=demo-token
TAP_PROJECT_ID=demo-project
```

---

## 注意事项

- Step 2 数据迁移必须在 Step 1 pipeline 迁移**稳定**后才开始
- TAP 支持的数据格式以 TAP 团队确认为准，不要自行假设
- 迁移完成验证通过前，保留本地 test data 备份
- `demo-project/` 包含 42 个 pytest 测试用例 + CSV/JSON 测试数据，可直接用于演示
