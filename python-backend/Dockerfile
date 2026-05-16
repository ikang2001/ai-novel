# ========================================
# AI 小说连载助手 - Python 后端 Dockerfile
# ========================================

# ============ 构建阶段 ============
FROM m.daocloud.io/docker.io/python:3.12-slim AS build

WORKDIR /app

# 换国内 apt 镜像源加速
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list 2>/dev/null || true

# 系统依赖（仅编译 Python 包需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv（使用国内 pip 镜像）
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com uv

# 先拷贝依赖清单，利用 Docker 缓存
COPY requirements.txt ./

# 安装依赖
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -r requirements.txt

# 拷贝业务代码
COPY app ./app
COPY .env.example ./.env.example

# ============ 运行阶段 ============
FROM m.daocloud.io/docker.io/python:3.12-slim

WORKDIR /app

# 换国内 apt 镜像源加速
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list 2>/dev/null || true

# 仅安装运行时需要的工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制环境与代码
COPY --from=build /app /app

# 创建非 root 用户
RUN groupadd -g 1000 appuser \
    && useradd -u 1000 -g appuser -m appuser \
    && chown -R appuser:appuser /app

USER appuser

# 容器内固定使用 8123，与前端 nginx 反代保持一致
ENV SERVER_HOST=0.0.0.0
ENV SERVER_PORT=8123

EXPOSE 8123

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8123/api/health/ || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8123"]
