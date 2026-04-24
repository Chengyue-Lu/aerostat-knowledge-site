# Aerostat Knowledge Site

## 项目简介

这是一个知识站点原型仓库，当前采用前后端分离结构：

- backend: FastAPI 最小服务，提供健康检查与占位接口。
- frontend: React + Vite 最小前端，包含首页、知识库页、问答页。

当前目标是先打通本地开发链路，为后续业务迭代提供清晰基础。

## 当前目录结构

```text
.
├── README.md
├── backend/
├── docs/
├── frontend/
├── infra/
└── scripts/
```

## Backend 启动方式

```bash
cd backend
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

常用接口：

- GET /health
- GET /documents
- POST /chat

## Frontend 启动方式

```bash
cd frontend
npm install
npm run dev
```

默认开发地址：

- http://localhost:5173

## 当前开发状态

- 已完成最小可运行 FastAPI 后端骨架。
- 已完成最小 React + Vite 前端骨架与三页面路由。
- 首页已接入后端健康检查组件。
- 前端 API 基地址支持 `VITE_API_BASE_URL` 环境变量，未设置时回退到 `http://localhost:8000`。
- 后端已启用开发期 CORS（仅允许本地开发来源）。
