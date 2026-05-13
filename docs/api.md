# API 文档

## 1. 上传简历

`POST /api/resume/upload`

- Content-Type: `multipart/form-data`
- 字段: `file` (PDF)
- 可选请求头: `Idempotency-Key`
- 重复上传相同 PDF 内容时会返回同一个 `resume_id`，避免重复解析/OCR/LLM 调用。
- 同一个 `Idempotency-Key` 只能对应同一个上传请求；如果 key 相同但文件内容、文件名或 Content-Type 不同，返回 `409`。

返回（示例）：

```json
{
  "resume_id": "uuid",
  "filename": "xx.pdf",
  "raw_text": "...",
  "cleaned_text": "...",
  "extracted": {
    "name": "张三",
    "phone": "138...",
    "email": "a@b.com",
    "address": "上海",
    "years_of_experience": "5年工作经验",
    "education": "本科",
    "intent": "后端开发",
    "skills": ["python", "redis"]
  },
  "extraction_method": "llm:openai"
}
```

## 通用响应约定

- 所有响应都会带 `X-Request-ID`，也可以由客户端请求头传入同名 ID 方便链路排查。
- 发生错误时返回统一结构：

```json
{
  "error": {
    "code": "not_found",
    "message": "Resume not found",
    "request_id": "trace-id"
  }
}
```

## 2. 查询简历

`GET /api/resume/{resume_id}`

## 3. 岗位匹配

`POST /api/job/match`

可选请求头: `Idempotency-Key`

```json
{
  "resume_id": "uuid",
  "jd_text": "岗位描述文本"
}
```

说明：

- 相同 `resume_id + jd_text` 的匹配结果会复用缓存，不会重复执行匹配计算。
- 同一个 `Idempotency-Key` 只能对应同一个匹配请求；如果 key 相同但请求体不同，返回 `409`。
- `jd_text` 不能为空，最大长度为 20000 字符。

幂等命中时响应头会包含 `Idempotency-Replayed: true`。

返回：

```json
{
  "resume_id": "uuid",
  "total_score": 0.82,
  "breakdown": {
    "jd_keywords": ["python", "redis"],
    "matched_keywords": ["python"],
    "keyword_match_rate": 0.5,
    "experience_score": 1.0,
    "education_score": 1.0,
    "intent_score": 0.7
  }
}
```
