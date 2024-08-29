FROM node:22.7.0-slim AS base

SHELL [ "/bin/bash", "-c" ]

COPY dist/ /api

WORKDIR /

# Move the Prisma client to the correct location
RUN mkdir -p /.prisma/client
RUN mv /api/src/assets/libquery_engine-linux-musl-openssl-3.0.x.so.node /.prisma/client/

# Install argon2
RUN npm i -g argon2

EXPOSE 3000

ARG ENABLE_CONFIDENTIALITY
ARG ENABLE_FAKE_OAUTH
ARG FRONTEND_URL
ARG API_URL


CMD [ "node", "api" ]
