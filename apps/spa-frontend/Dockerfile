FROM nginx:alpine

COPY dist/ /dist/spa-frontend

WORKDIR /dist/spa-frontend

RUN echo 'server { \
  listen 80; \
  server_name localhost; \
  root /dist/spa-frontend; \
  index index.html; \
  location / { \
  try_files $uri $uri/ /index.html; \
  } \
  }' > /etc/nginx/conf.d/default.conf


CMD ["nginx", "-g", "daemon off;"]
