FROM node:18-alpine

WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy .env file (if exists)
COPY .env* ./

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Install serve for running static files
RUN npm install -g serve

# Expose port
EXPOSE 3000

# Start command
CMD ["npm", "start"]