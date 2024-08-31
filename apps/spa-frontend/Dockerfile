FROM fholzer/nginx-brotli:latest

COPY dist/ /dist/spa-frontend

WORKDIR /dist/spa-frontend

RUN echo 'server { \
  listen 80; \
  server_name localhost; \
  root /dist/spa-frontend; \
  index index.html; \
  brotli on; \
  brotli_comp_level 6; \
  brotli_types text/plain text/css application/javascript application/json image/svg+xml application/xml+rss; \
  location / { \
  try_files $uri $uri/ /index.html; \
  } \
  }' > /etc/nginx/conf.d/default.conf


CMD ["-g", "daemon off;"]
