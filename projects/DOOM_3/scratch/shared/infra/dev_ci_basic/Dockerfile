# Base dev container for a Vite app with npm ci optimization
FROM node:20-alpine
WORKDIR /app

# Copy package manifests first to leverage cached layers
COPY package.json package-lock.json* npm-shrinkwrap.json* ./

# Install dependencies using CI-friendly command when lockfile exists; fall back to npm install otherwise
RUN if [ -f package-lock.json ]; then npm ci --silent; else npm install --silent; fi

# Copy the rest of the application code
COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev"]
