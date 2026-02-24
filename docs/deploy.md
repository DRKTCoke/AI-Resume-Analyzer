# 部署说明

## 1) 后端部署到阿里云函数计算（Serverless Devs）

前提：已安装 `s` 命令行并完成阿里云账号配置。

```bash
cd backend
s deploy
```

部署成功后会返回公网 URL，作为前端 API Base URL。

## 2) 前端部署到 GitHub Pages

1. 将 `frontend/` 内容放到仓库根目录或 `docs/` 目录。
2. GitHub -> Settings -> Pages -> 选择分支与目录。
3. 发布后得到可访问页面 URL。
4. 页面里填写后端 URL 并测试上传/匹配。

## 3) Redis（可选）

配置 `REDIS_URL` 后自动启用 Redis；未配置则使用进程内缓存。
