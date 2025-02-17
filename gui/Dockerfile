FROM nginx:1.23.2-alpine

RUN mkdir -p /opt/service

WORKDIR /opt/service

COPY nginx/nginx.conf /etc/nginx/
COPY nginx/default.conf /etc/nginx/conf.d/
COPY www www
