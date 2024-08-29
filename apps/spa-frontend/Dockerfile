FROM nginx:alpine

COPY dist/ /dist/spa-frontend

WORKDIR /dist/spa-frontend

RUN echo 'server { \
  listen 4200; \
  server_name localhost; \
  root /dist/spa-frontend; \
  index index.html; \
  location / { \
  try_files $uri $uri/ /index.html; \
  } \
  }' > /etc/nginx/conf.d/default.conf

ARG VITE_API_URL
ARG VITE_ENABLE_CONFIDENTIALITY
ARG VITE_STREAM_CHAT_API_KEY

ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_ENABLE_CONFIDENTIALITY=${VITE_ENABLE_CONFIDENTIALITY}
ENV VITE_STREAM_CHAT_API_KEY=${VITE_STREAM_CHAT_API_KEY}


CMD ["nginx", "-g", "daemon off;"]
