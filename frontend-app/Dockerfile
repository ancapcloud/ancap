FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
COPY vendor/picomatch-safe ./vendor/picomatch-safe
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ARG NEXT_PUBLIC_ASSET_PREFIX=
ARG NEXT_PUBLIC_API_URL=
ARG NEXT_PUBLIC_ACP_URL=
ARG APP_BUILD_ID=unknown
ARG NEXT_PUBLIC_TURNSTILE_SITE_KEY=
ENV NEXT_PUBLIC_ASSET_PREFIX=$NEXT_PUBLIC_ASSET_PREFIX
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_ACP_URL=$NEXT_PUBLIC_ACP_URL
ENV NEXT_PUBLIC_TURNSTILE_SITE_KEY=$NEXT_PUBLIC_TURNSTILE_SITE_KEY
ENV NEXT_PUBLIC_APP_BUILD_ID=$APP_BUILD_ID
ENV NEXT_BUILD_ID=$APP_BUILD_ID
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ARG APP_BUILD_ID=unknown
ENV NODE_ENV=production
ENV NEXT_PUBLIC_APP_BUILD_ID=$APP_BUILD_ID
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/vendor ./vendor
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.ts ./next.config.ts

EXPOSE 3000
CMD ["./node_modules/.bin/next", "start", "-p", "3000"]

