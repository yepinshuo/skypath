# SkyPath frontend — Vite dev server (prototype).
# For a prototype we run Vite directly; a production build would compile to
# static assets and serve them via nginx (noted in the README as a tradeoff).
FROM node:20-slim

WORKDIR /app

# Install dependencies first for layer caching.
COPY package.json ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev"]
