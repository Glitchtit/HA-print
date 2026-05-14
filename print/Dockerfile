ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest

FROM $BUILD_FROM

RUN apk add --no-cache \
        python3 py3-pip \
        nginx gettext jq curl \
        libjpeg-turbo zlib \
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

WORKDIR /app
