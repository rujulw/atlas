FROM node:20-alpine

WORKDIR /app

COPY client/package.json /app/package.json

EXPOSE 5173
