# Dev runtime Dockerfile for shared tooling (CI stub and frontend/backend artifacts)
FROM node:20-alpine

# Create app directory
WORKDIR /app

# Install dependencies (copy package manifests first for leverage of layer caching)
COPY package.json package.json
RUN npm install

# Copy the rest of the repository
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Start the dev server (serves the shared tooling)
CMD ["npm", "run", "dev"]
