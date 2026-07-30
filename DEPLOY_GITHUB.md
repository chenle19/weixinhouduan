# GitHub Actions + GHCR + Watchtower 部署说明

这套流程用于部署 `backend` FastAPI 服务：

```text
push main
  -> GitHub Actions 构建 Docker 镜像
  -> 推送到 GHCR
  -> 阿里云服务器上的 Watchtower 自动拉取新镜像并重启容器
```

## 1. 文件位置

- `backend/Dockerfile`：后端镜像构建
- `backend/.dockerignore`：构建时忽略本地数据库、日志、密钥
- `.github/workflows/docker-image.yml`：GitHub Actions 自动构建并推送 GHCR
- `backend/docker-compose.yml`：服务器生产部署
- `backend/.env`：生产环境变量，不要提交到 Git

## 2. 后端环境变量

服务器上创建 `backend/.env`：

```env
APP_NAME="Hair Booking API"
DATABASE_URL="sqlite:///./data/hair_booking.db"
SECRET_KEY="change-this-secret-in-production"
ACCESS_TOKEN_EXPIRE_MINUTES=1440
BACKEND_CORS_ORIGINS="https://你的后台域名"
WECHAT_APPID="你的微信小程序AppID"
WECHAT_SECRET="你的微信小程序AppSecret"
APP_PORT=8000
IMAGE="ghcr.io/你的github用户名或组织名/hair-booking-backend:latest"
```

注意：`WECHAT_APPID` 和 `WECHAT_SECRET` 必须和小程序 AppID 对应。

## 3. GitHub 仓库准备

1. 把当前项目提交到 GitHub。
2. 默认分支使用 `main`。
3. 推送后，GitHub Actions 会自动运行。
4. 镜像会推送到：

```text
ghcr.io/你的github用户名或组织名/hair-booking-backend:latest
```

如果 GHCR 包默认是 private，服务器需要先登录 GHCR。

## 4. 阿里云服务器登录 GHCR

在 GitHub 创建一个 Personal Access Token，至少需要：

```text
read:packages
```

服务器执行：

```bash
echo "你的GitHub PAT" | docker login ghcr.io -u 你的GitHub用户名 --password-stdin
```

## 5. 服务器首次部署

上传 `backend/docker-compose.yml` 和 `backend/.env` 到服务器同一目录，例如：

```bash
/opt/hair-booking/backend
```

启动：

```bash
cd /opt/hair-booking/backend
docker compose pull
docker compose up -d
```

检查：

```bash
docker ps
curl http://127.0.0.1:8000/health
```

## 6. Watchtower 自动更新

`docker-compose.yml` 已包含 Watchtower。

以后只要推送到 `main`：

```bash
git push origin main
```

GitHub Actions 会构建新镜像并推送到 GHCR。服务器上的 Watchtower 每 60 秒检查一次新镜像，发现更新后会自动：

1. 拉取新镜像
2. 重启 `hair-booking-api`
3. 清理旧镜像

## 7. Nginx HTTPS 反向代理

微信小程序真机预览和线上环境需要 HTTPS 合法域名，不能使用 `127.0.0.1`。

如果 VPS 上已经有另一个项目占用了 80 端口，不要让 Python 容器直接绑定 80。
正确做法是让 Nginx 继续监听 80/443，并按域名分流：

- `www.clandxdz.cn` -> 原来的项目
- `api.clandxdz.cn` -> Python 后端 `127.0.0.1:8000`

当前 `docker-compose.yml` 已经把后端绑定到 VPS 本机端口：

```yaml
ports:
  - "127.0.0.1:${APP_PORT:-8000}:8000"
```

所以外网不能直接访问 `:8000`，必须通过 Nginx 反向代理。

Nginx 示例：

```nginx
server {
    listen 80;
    server_name api.clandxdz.cn;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

HTTPS 示例：

```nginx
server {
    listen 443 ssl http2;
    server_name api.clandxdz.cn;

    ssl_certificate /etc/letsencrypt/live/api.clandxdz.cn/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.clandxdz.cn/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

然后到微信公众平台配置：

```text
开发管理 -> 开发设置 -> 服务器域名 -> request 合法域名
```

填写：

```text
https://api.clandxdz.cn
```

最后把小程序接口地址改成这个 HTTPS 域名。

## 8. 关于 npm ci / npm run build

当前这套 workflow 只构建 Python 后端镜像，后端不需要：

```bash
npm ci
npm run build
```

如果要把 `vue3-admin` 后台管理系统也自动部署，建议单独做一个前端镜像或静态资源发布 workflow，避免和后端镜像混在一起。
