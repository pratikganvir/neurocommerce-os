FROM node:18-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* pnpm-lock.yaml* ./

# Install dependencies
RUN npm install

COPY . .

# Create public directory if it doesn't exist
RUN mkdir -p public

# Build
RUN npm run build

# Runtime
FROM node:18-alpine

WORKDIR /app

COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public/
COPY package.json next.config.js ./

EXPOSE 3000

CMD ["npm", "start"]
