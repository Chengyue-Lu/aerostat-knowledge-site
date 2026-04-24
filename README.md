# Aerostat Knowledge Site

## 项目简介

这是一个浮空器知识网站第一版原型仓库，当前采用前后端分离结构：

- backend: FastAPI 最小服务，提供健康检查与占位接口。
- frontend: React + Vite 最小前端，包含首页、知识库页、问答页。

当前目标是在现有本地联调方式下稳定推进业务原型，不包含数据库、认证、对象存储或真实检索索引。

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

常用接口：

- `GET /health`: 返回后端健康状态。
- `GET /documents`: 返回 3 条硬编码占位文档。
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
- 已完成最小 React + Vite 前端骨架与三页面路由。
- 首页保留 Backend Health 卡片，调用 `GET /health`。
- Knowledge 页面调用 `GET /documents` 并展示占位文档列表。
- Chat 页面提交问题到 `POST /chat` 并展示后端返回的 `reply`。
- 前端 API 基地址支持 `VITE_API_BASE_URL` 环境变量，未设置时回退到 `http://localhost:8000`。
- 后端已启用开发期 CORS（仅允许本地开发来源）。
