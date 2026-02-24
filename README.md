# AI Resume Analyzer

MVP：
- Python FastAPI 后端（可部署为阿里云函数计算）
- PDF 简历上传与解析
- OCR 扫描件识别（低质量文本自动触发）（注意：OCR需要tesseract依赖，若未安装依赖，建议将配置改为ENABLE_OCR=false）
- LLM 结构化抽取（OpenAI / 百炼二选一）
- 稳定匹配评分（关键词 + 经验 + 学历 + 意向）
- Redis 缓存（可选，填入相应URL，不填直接走本地内存缓存）
- 纯静态前端（可部署到 GitHub Pages）

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
cp .env.openai.example .env
uvicorn app.main:app --reload --port 8000
```

前端：

```bash
cd frontend
python -m http.server 8080
```

打开 `http://localhost:8080`，将 API Base URL 设为 `http://localhost:8000`。

## 二阶段关键配置

- 开启 LLM 抽取：`ENABLE_LLM=true`
- 供应商：`LLM_PROVIDER=openai` 或 `LLM_PROVIDER=bailian`
- OCR 开关：`ENABLE_OCR=true`

默认已切到 OpenAI 配置（`backend/.env.example` / `backend/.env.openai.example`），你只需要把 `LLM_API_KEY` 替换成真实 key。

详见 `docs/deploy.md`。

## API 概览

- `POST /api/resume/upload`：上传 PDF 并解析
- `POST /api/job/match`：输入 JD 与简历 ID，返回匹配分
- `GET /api/resume/{resume_id}`：读取简历解析结果
- `GET /healthz`：健康检查

详见 `docs/api.md`。

## 说明

- 默认规则抽取可直接跑通。
- 开启 LLM 后会返回 `extraction_method=llm:<provider>`。
