# 部署说明

## 1) 后端部署到阿里云函数计算（Serverless Devs）

前提：已安装 `s` 命令行并完成阿里云账号配置。

```bash
cd backend
s deploy
```

部署成功后会返回公网 URL，作为前端 API Base URL。

## 2) OCR 运行依赖

OCR 使用 `pytesseract`，运行环境需要系统安装 `tesseract` 与中文语言包。

示例（Ubuntu）：

```bash
apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-chi-sim
```

函数计算环境建议通过自定义运行时镜像打包这些依赖。

## 3) LLM 配置（二选一）

### OpenAI
- `ENABLE_LLM=true`
- `LLM_PROVIDER=openai`
- `LLM_BASE_URL=https://api.openai.com`
- `LLM_MODEL=gpt-4o-mini`
- `LLM_API_KEY=...`

### 百炼（OpenAI 兼容模式）
- `ENABLE_LLM=true`
- `LLM_PROVIDER=bailian`
- `LLM_BASE_URL=https://dashscope.aliyuncs.com`
- `LLM_MODEL=qwen-plus`
- `LLM_API_KEY=...`

## 4) 前端已部署到 GitHub Pages

页面里填写后端 URL 并测试上传/匹配（后端需本地或云端部署，且公网可达）
