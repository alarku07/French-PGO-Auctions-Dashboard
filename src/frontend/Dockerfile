# ── Stage 1: builder ──────────────────────────────────────────────────────────
FROM node:24-slim AS builder

WORKDIR /app

COPY package*.json .
RUN npm ci

COPY . .

ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build

ARG VERSION=dev

# ── Stage 2: dev (hot-reload) ─────────────────────────────────────────────────
FROM node:24-slim AS dev

WORKDIR /app

COPY --from=builder /app/node_modules ./node_modules
COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev"]

# ── Stage 3: runtime (production) ────────────────────────────────────────────
FROM nginx:1.29.5-alpine AS runtime

COPY --from=builder /app/dist /usr/share/nginx/html

RUN printf 'server {\n\
    listen 80;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
\n\
    gzip on;\n\
    gzip_types text/css application/javascript text/html;\n\
\n\
    location / {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 80
