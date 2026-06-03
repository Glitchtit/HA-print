ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest

# ── Stage 1: build the React frontend ───────────────────────────────────────
FROM node:20-alpine AS frontend-builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# ── Stage 2: runtime image ───────────────────────────────────────────────────
FROM $BUILD_FROM

RUN apk add --no-cache \
        python3 py3-pip \
        nginx gettext jq curl \
        libjpeg-turbo zlib \
        rsvg-convert \
    && apk add --no-cache --virtual .build-deps \
        musl-dev gcc python3-dev jpeg-dev zlib-dev

COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt \
    && apk del .build-deps

COPY nginx.conf.template /etc/nginx/nginx.conf.template
COPY config.json /config.json
COPY app/ /app/
COPY rootfs /

# Built SPA replaces the static health-check page.
COPY --from=frontend-builder /app/dist /var/www/html

WORKDIR /app
