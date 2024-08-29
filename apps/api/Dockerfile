FROM node:22.7.0-slim AS base

SHELL [ "/bin/bash", "-c" ]

COPY dist/ /dist/api

WORKDIR /dist

RUN npm i argon2 nodejs-polars
RUN mkdir -p node_modules/.prisma/client && mv api/src/assets/libquery_engine-* node_modules/.prisma/client/

# Install openssl
RUN apt-get update && apt-get install -y openssl

EXPOSE 3000

ARG ENABLE_CONFIDENTIALITY
ARG ENABLE_FAKE_OAUTH
ARG FRONTEND_URL
ARG API_URL

# Assign environment variables
ENV ENABLE_CONFIDENTIALITY=${ENABLE_CONFIDENTIALITY}
ENV ENABLE_FAKE_OAUTH=${ENABLE_FAKE_OAUTH}
ENV FRONTEND_URL=${FRONTEND_URL}
ENV API_URL=${API_URL}


CMD [ "node", "api" ]
