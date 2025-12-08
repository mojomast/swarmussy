FROM node:18
WORKDIR /app
COPY ./ .
RUN npm ci 2>/dev/null || true
CMD ["node", "index.js"]
