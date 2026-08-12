# Stage 1: Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package descriptors
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build production bundle
RUN npm run build

# Stage 2: Production Nginx stage
FROM nginx:alpine AS production

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built static assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
