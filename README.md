# AI Resume Analyzer

MVP：
- Python FastAPI 后端（可部署为阿里云函数计算）
- PDF 简历上传与解析
- 关键字段提取（姓名/电话/邮箱/地址/技能/经历）
- 岗位 JD 关键词提取与匹配评分
- Redis 缓存（可选其他缓存？）
- 纯静态前端（已部署到 GitHub Pages）

## 目录

- `backend/` 后端服务
- `frontend/` 静态页面
- `docs/` 技术文档与部署说明

## 本地快速启动

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

前端：

```bash
cd frontend
python -m http.server 8080
```

打开 `http://localhost:8080`，将 API Base URL 设为 `http://localhost:8000`。

## API 概览

- `POST /api/resume/upload`：上传 PDF 并解析
- `POST /api/job/match`：输入 JD 与简历 ID，返回匹配分
- `GET /api/resume/{resume_id}`：读取简历解析结果
- `GET /healthz`：健康检查

详见 `docs/api.md`。

## 阿里云 Serverless 部署

已提供 `backend/s.yaml` 模板，可按 `docs/deploy.md` 一步步部署。

## 说明

- 这个版本默认使用**规则+关键词**实现可交付能力。
- 如需接入大模型（例如阿里云百炼 / OpenAI），只需在 `.env` 打开开关并配置 key。
