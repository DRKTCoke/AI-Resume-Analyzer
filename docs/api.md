# API 文档

## 1. 上传简历

`POST /api/resume/upload`

- Content-Type: `multipart/form-data`
- 字段: `file` (PDF)

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
    "intent": null,
    "skills": ["python", "redis"]
  }
}
```

## 2. 查询简历

`GET /api/resume/{resume_id}`

## 3. 岗位匹配

`POST /api/job/match`

```json
{
  "resume_id": "uuid",
  "jd_text": "岗位描述文本"
}
```

返回：

```json
{
  "resume_id": "uuid",
  "total_score": 0.82,
  "breakdown": {
    "jd_keywords": ["python", "redis"],
    "matched_keywords": ["python"],
    "keyword_match_rate": 0.5,
    "experience_score": 1.0
  }
}
```
