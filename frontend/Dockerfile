# Build stage
FROM node:20-alpine AS build

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build app
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom nginx config template
COPY nginx.conf.template /etc/nginx/conf.d/default.conf.template

# Copy entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 80

# Set default API_PORT if not provided
ENV API_PORT=8000

ENTRYPOINT ["/docker-entrypoint.sh"]

