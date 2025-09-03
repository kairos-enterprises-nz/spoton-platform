FROM node:18-alpine

WORKDIR /app

# Install dependencies (cached by Docker layer when package files unchanged)
COPY apps/staff-web/package*.json ./
RUN npm install

# Copy source
COPY apps/staff-web/ .

EXPOSE 3002

# Default to production static server; in UAT we override the command to use dev with HMR via compose
RUN npm run build || true
CMD ["npx", "serve", "-s", "dist", "-l", "3002"]