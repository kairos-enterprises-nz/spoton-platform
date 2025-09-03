FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY apps/web/package*.json ./

# Install dependencies
RUN npm install

# Copy app source
COPY apps/web/ .

# Build the application
RUN npm run build

# Install serve for production
RUN npm install -g serve@14.2.3

# Expose port
EXPOSE 3000

# Start production server
CMD ["serve", "-s", "dist", "-l", "3000"]
