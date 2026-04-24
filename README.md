# Aerostat Knowledge Site

## 项目简介

这是一个浮空器知识网站第一版原型仓库，当前采用前后端分离结构：

- backend: FastAPI 服务，提供健康检查、SQLite 文档元数据接口与占位问答接口。
- frontend: React + Vite 最小前端，包含首页、知识库页、问答页。

当前已进入“文档元数据持久化”阶段：文档列表从 SQLite 读取，支持创建和读取文档元数据记录。本阶段仍不包含真实文件上传、PDF 解析、向量库、LLM / embedding、认证、对象存储或后台任务队列。

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

常用接口：

- `GET /health`: 返回后端健康状态。
- `GET /documents`: 从 SQLite 返回文档元数据列表。
- `POST /documents`: 创建一条文档元数据记录，不上传文件。
- `GET /documents/{document_id}`: 读取单条文档元数据记录。
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
- 已完成最小 React + Vite 前端骨架与三页面路由。
- 首页保留 Backend Health 卡片，调用 `GET /health`。
- Knowledge 页面调用 `GET /documents` 并展示 SQLite 文档元数据列表。
- Chat 页面提交问题到 `POST /chat` 并展示后端返回的 `reply`。
- 前端 API 基地址支持 `VITE_API_BASE_URL` 环境变量，未设置时回退到 `http://localhost:8000`。
- 后端已启用开发期 CORS（仅允许本地开发来源）。
