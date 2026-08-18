# Build stage
FROM node:22-alpine AS builder
WORKDIR /app

# Copy workspace files
COPY package.json ./
COPY apps/studio ./apps/studio

WORKDIR /app/apps/studio

# Install dependencies  
RUN npm install

# Build
RUN npm run build

# Runtime stage
FROM node:22-alpine
WORKDIR /app

COPY --from=builder /app/apps/studio/.next/standalone ./

EXPOSE 3000
CMD ["node", "server.js"]
