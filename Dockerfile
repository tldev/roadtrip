# syntax=docker/dockerfile:1.7
FROM oven/bun:1.3-alpine AS deps
WORKDIR /app
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile --production

FROM oven/bun:1.3-alpine AS builder
WORKDIR /app
COPY package.json bun.lock ./
COPY scripts ./scripts
COPY src ./src
RUN bun run build

FROM oven/bun:1.3-alpine AS runtime
WORKDIR /app

# Pin UID/GID explicitly so bind-mount hosts can pre-chown to a known
# numeric owner. UID 100 / GID 101 matches what Alpine's `adduser -S`
# allocated on the prior unpinned build, so prod's existing bind-path
# ownership remains valid through the Watchtower roll.
ARG APP_UID=100
ARG APP_GID=101
RUN addgroup -g ${APP_GID} -S app \
 && adduser -u ${APP_UID} -S app -G app \
 && install -d -o app -g app -m 0755 /data

COPY --from=deps /app/node_modules ./node_modules
COPY package.json tsconfig.json ./
COPY src ./src
COPY data ./data
COPY --from=builder /app/dist ./dist
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
