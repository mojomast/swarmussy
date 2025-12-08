FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Expose the app port
EXPOSE 8000
# Provide a root-entrypoint script to support repository-backed API layer
RUN chmod +x start_api.sh && mv start_api.sh /start_api.sh
CMD ["/start_api.sh"]
