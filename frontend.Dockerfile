FROM node:20-alpine

WORKDIR /frontend

COPY package.json package-lock.json ./

RUN npm ci

RUN npm run build