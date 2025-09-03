FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY apps/portal-web/package*.json ./

# Install dependencies
RUN npm install

# Copy app source
COPY apps/portal-web/ .

# Build production assets
RUN npm run build

FROM node:18-alpine AS runner

WORKDIR /app

# Install a lightweight static server
RUN npm install -g serve@14.2.3

# Copy built assets
COPY --from=builder /app/dist ./dist

EXPOSE 3001

# Serve static build (no HMR/WebSocket)
CMD ["serve", "-s", "dist", "-l", "3001"]