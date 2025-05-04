FROM node:16-alpine

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm ci

# Copy application code
COPY . .

# Set environment variables with defaults
ENV PORT=3000
ENV HOST=0.0.0.0
ENV REACT_APP_API_URL=http://localhost:5000/api/v1

# Expose the port
EXPOSE 3000

# Start the application
CMD ["npm", "start"] 