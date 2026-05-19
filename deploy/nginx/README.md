# Nginx 统一出口方案

这个项目适合采用单域名统一出口：

- Nginx 对外监听 `80/443`
- 静态前端直接由 Nginx 提供
- `/api/`、`/docs`、`/openapi.json` 反向代理到 FastAPI `127.0.0.1:8002`

对应仓库中的真实结构：

- 前端静态目录：`xuanxue-web/frontend/`
- 后端服务端口：`8002`
- 前端默认 API 基地址：`window.location.origin`
- 前端接口路径：`/api/...`

## 请求链路

```text
Browser
  -> http://your-domain/
  -> Nginx
     -> /index.html / *.js / *.css / *.html
     -> /api/* -> 127.0.0.1:8002
     -> /docs -> 127.0.0.1:8002/docs
     -> /openapi.json -> 127.0.0.1:8002/openapi.json
```

这样做的好处：

- 前后端同域，不依赖跨域
- 前端不用写死 `8002`
- 浏览器访问入口统一为 `http://域名/`
- 后端可以只暴露内网端口

## 模板说明

配置文件见 [xuanxue.conf](/home/alfred/multiproject/xuanxue/deploy/nginx/xuanxue.conf:1)。

这个模板已经考虑了当前项目的几个实际需求：

- `root` 指向 `xuanxue-web/frontend`
- `/api/` 代理到 `127.0.0.1:8002`
- `client_max_body_size 20m`
  因为 `visual-insight` 会上传图片
- `location = /AI配置指南.md`
  把仓库根目录的 `AI配置指南.md` 暴露到站点根路径
- 对 `html/md` 关闭强缓存
- 对 `js/css/图片` 增加适度缓存

## 推荐部署方式

1. 启动后端

```bash
cd /home/alfred/multiproject/xuanxue
./start.sh
```

如果已经接入 Nginx，建议继续保持默认模式：

```bash
FRONTEND_MODE=nginx PUBLIC_ENTRY_URL=http://localhost/index.html ./start.sh
```

2. 安装 Nginx 后，把模板链接到站点目录

常见 Debian/Ubuntu 方式：

```bash
sudo cp /home/alfred/multiproject/xuanxue/deploy/nginx/xuanxue.conf /etc/nginx/sites-available/xuanxue.conf
sudo ln -s /etc/nginx/sites-available/xuanxue.conf /etc/nginx/sites-enabled/xuanxue.conf
```

3. 校验并重载

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## HTTPS 建议

如果后续上公网，推荐在这个 `server` 之外再补：

- `listen 443 ssl http2`
- 证书配置
- `80 -> 443` 跳转

## 生产建议

- 后端进程建议交给 `systemd` 或 `supervisor` 托管，不只靠手工脚本
- 如果只允许 Nginx 访问后端，可把 FastAPI 绑定到 `127.0.0.1:8002`
- 生产环境建议把 `CORS_ALLOW_ORIGINS` 调整成真实域名，虽然同域部署下几乎不会触发跨域
