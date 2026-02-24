# 技术方案说明（二阶段）

## 一次性交付结论

可以一次性交付一个可验收二阶段版本：
- PDF 文本抽取 + 扫描件 OCR 回退。
- LLM 结构化抽取（OpenAI / 百炼 compatible-mode 二选一）。
- 更稳定的多维度匹配评分（关键词/经验/学历/求职意向）。

## 架构

- 前端：静态网页（GitHub Pages）
- 后端：FastAPI（可部署阿里云函数计算）
- 缓存：Redis（可选，未配置时回退内存缓存）
- 文本来源：`pypdf` 优先，低质量文本时触发 OCR
- 抽取策略：规则抽取默认，开启 LLM 后切到结构化抽取

流程：
1. 上传 PDF -> `/api/resume/upload`
2. `pypdf` 提取文本
3. 文本质量较低时启用 OCR（扫描件）
4. 文本清洗
5. 规则抽取或 LLM 抽取（二选一）
6. 缓存结果并返回
7. 提交 JD -> `/api/job/match`，输出稳定评分

## 评分策略（稳定版）

`total = 0.55 * keyword + 0.25 * experience + 0.1 * education + 0.1 * intent`

- `keyword`：JD 关键词命中率
- `experience`：简历年限与 JD 要求年限的比值（封顶 1.0）
- `education`：学历等级映射比较（大专<本科<硕士<博士）
- `intent`：求职意向与 JD 关键词相关性

## 风险与建议

- OCR 依赖运行环境的 Tesseract 可执行文件，部署时需打包或安装。
- LLM 输出偶发格式偏差，已做 JSON 提取兜底，建议后续加 schema 重试。
- 并发场景建议补充请求级限流与异步任务队列。
