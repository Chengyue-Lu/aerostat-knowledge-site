# Aerostat Knowledge Site

## 项目简介

这是一个浮空器知识网站第一版原型仓库，当前采用前后端分离结构：

- backend: FastAPI 服务，提供健康检查、SQLite 文档元数据接口、原始文档上传接口、MinerU PDF 解析队列、文件一致性检查接口与占位问答接口。
- frontend: React + Vite 最小前端，包含首页、知识库页、问答页。

当前已进入“MinerU 解析接入”阶段：文档列表从 SQLite 读取，支持注册 `.txt` / `.md` / `.pdf` 原始文件，PDF 可进入单 worker FIFO 队列调用本机独立 MinerU CLI 解析为 Markdown，并登记解析产物路径。本阶段仍不做 chunk 切分、向量库、LLM / embedding、认证、对象存储或 Celery/Redis/RQ。

## 当前目录结构

```text
.
├── CHANGELOG.md
├── README.md
├── backend/
├── docs/
└── frontend/
```

## Backend 启动方式

```bash
cd backend
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

测试 MinerU 解析时建议不要使用 `--reload`，避免 MinerU 写入
`backend/data/mineru_outputs/` 触发后端重启并中断内存队列：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

默认 SQLite 数据库：

- 未设置 `DATABASE_URL` 时，后端使用 `sqlite:///./data/aerostat_knowledge.db`。
- 从 `backend/` 目录启动时，对应文件为 `backend/data/aerostat_knowledge.db`。
- 可参考 `backend/.env.example` 设置 `DATABASE_URL`。
- 本地持久配置可写入 `backend/.env`，启动时会自动读取；真实环境变量优先级更高。

默认原始文档目录：

- 未设置 `DOCS_RAW_DIR` 时，后端使用 `backend/data/docs_raw/`。
- 每个上传文件会保存到独立 UUID 子目录，避免同名覆盖。

默认 MinerU 输出目录：

- 未设置 `MINERU_OUTPUT_DIR` 时，后端使用 `backend/data/mineru_outputs/`。
- 未设置 `MINERU_BACKEND` 时，后端不会向 MinerU CLI 传 `-b`。
- `MINERU_TIMEOUT_SECONDS` 默认是 `21600` 秒。
- `POST /documents/{document_id}/parse` 是后台慢任务入口，不等待解析结束。

常用接口：

- `GET /health`: 返回后端健康状态。
- `GET /documents`: 从 SQLite 返回文档元数据列表。
- `POST /documents`: 创建一条文档元数据记录，不上传文件。
- `POST /documents/upload`: 上传 `.txt` / `.md` / `.pdf` 原始文件，并创建文档元数据记录。
- `POST /documents/{document_id}/parse`: 将 PDF 文档加入 MinerU 单 worker 解析队列。
- `GET /documents/{document_id}/parse-result`: 读取已解析出的 Markdown 内容。
- `GET /documents/{document_id}`: 读取单条文档元数据记录。
- `DELETE /documents/{document_id}`: 删除文档元数据及本地原始文件、解析输出目录。
- `GET /admin/reconcile/dry-run`: 检查数据库文件引用与本地文件系统是否一致，不自动修复。
- `POST /chat`: 返回占位问答回复和空 sources 列表。

## Frontend 启动方式

```bash
cd frontend
npm install
npm run dev
```

默认开发地址：

- `http://localhost:5173`

## 当前开发状态

- 已完成最小可运行 FastAPI 后端骨架。
- 已完成第一版 SQLite 文档元数据持久化。
- 已完成第一版 `.txt` / `.md` / `.pdf` 原始文档注册与本地存储。
- 已完成第一版 MinerU PDF 后台解析接入和单 worker 排队。
- 已完成第一版解析队列重启恢复、文档删除和前端队列视图。
- 已完成第一版数据库记录与本地文件系统 dry-run 一致性检查。
- 已完成最小 React + Vite 前端骨架与三页面路由。
- 首页保留 Backend Health 卡片，调用 `GET /health`。
- Knowledge 页面调用 `GET /documents` 并展示 SQLite 文档元数据列表，支持上传 `.txt` / `.md` / `.pdf` 文件。
- Chat 页面提交问题到 `POST /chat` 并展示后端返回的 `reply`。
- 前端 API 基地址支持 `VITE_API_BASE_URL` 环境变量，未设置时回退到 `http://localhost:8000`。
- 后端已启用开发期 CORS（仅允许本地开发来源）。
