# syntax=docker/dockerfile:1.7
FROM oven/bun:1.3-alpine AS deps
WORKDIR /app
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile --production

FROM oven/bun:1.3-alpine AS runtime
WORKDIR /app
RUN addgroup -S app && adduser -S app -G app && \
    mkdir -p /data && chown -R app:app /data
COPY --from=deps /app/node_modules ./node_modules
COPY package.json tsconfig.json ./
COPY src ./src
COPY data ./data
USER app

ARG GIT_SHA=dev
ENV GIT_SHA=${GIT_SHA} \
    NODE_ENV=production \
    PORT=8080 \
    DATA_DIR=/data

VOLUME ["/data"]
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://127.0.0.1:8080/healthz | grep -q '"status":"ok"' || exit 1

CMD ["bun", "run", "src/server.ts"]
