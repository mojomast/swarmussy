# Multi-stage Dockerfile to build and run Level API

# Builder stage: install deps and compile TypeScript
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
# Build the project (produces dist/)
RUN npm run build

# Runtime stage
FROM node:20-alpine
WORKDIR /app
# Copy built artifacts and node_modules
COPY --from=builder /app/dist /app/dist
COPY --from=builder /app/node_modules /app/node_modules
# Expose Level API port
EXPOSE 3000
# Start server from built artifacts
CMD ["node", "dist/server.js"]
