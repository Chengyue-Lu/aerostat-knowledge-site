# Aerostat Knowledge Site

## 项目简介

这是一个浮空器知识网站第一版原型仓库，当前采用前后端分离结构：

- backend: FastAPI 服务，提供健康检查、SQLite 文档元数据接口、原始文档上传接口、文件一致性检查接口与占位问答接口。
- frontend: React + Vite 最小前端，包含首页、知识库页、问答页。

当前已进入“文件注册与一致性校验”阶段：文档列表从 SQLite 读取，支持注册 `.txt` / `.md` / `.pdf` 原始文件，记录文件大小、MIME、SHA-256、解析状态等元数据，并提供 dry-run 文件一致性检查。本阶段仍不做文本解析、MinerU 调用、chunk 切分、向量库、LLM / embedding、认证、对象存储或后台任务队列。

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

默认 SQLite 数据库：

- 未设置 `DATABASE_URL` 时，后端使用 `sqlite:///./data/aerostat_knowledge.db`。
- 从 `backend/` 目录启动时，对应文件为 `backend/data/aerostat_knowledge.db`。
- 可参考 `backend/.env.example` 设置 `DATABASE_URL`。

默认原始文档目录：

- 未设置 `DOCS_RAW_DIR` 时，后端使用 `backend/data/docs_raw/`。
- 每个上传文件会保存到独立 UUID 子目录，避免同名覆盖。

常用接口：

- `GET /health`: 返回后端健康状态。
- `GET /documents`: 从 SQLite 返回文档元数据列表。
- `POST /documents`: 创建一条文档元数据记录，不上传文件。
- `POST /documents/upload`: 上传 `.txt` / `.md` / `.pdf` 原始文件，并创建文档元数据记录。
- `GET /documents/{document_id}`: 读取单条文档元数据记录。
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
- 已完成第一版数据库记录与本地文件系统 dry-run 一致性检查。
- 已完成最小 React + Vite 前端骨架与三页面路由。
- 首页保留 Backend Health 卡片，调用 `GET /health`。
- Knowledge 页面调用 `GET /documents` 并展示 SQLite 文档元数据列表，支持上传 `.txt` / `.md` / `.pdf` 文件。
- Chat 页面提交问题到 `POST /chat` 并展示后端返回的 `reply`。
- 前端 API 基地址支持 `VITE_API_BASE_URL` 环境变量，未设置时回退到 `http://localhost:8000`。
- 后端已启用开发期 CORS（仅允许本地开发来源）。
