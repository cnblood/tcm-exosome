FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Create directories for logs
RUN mkdir -p /app/logs

# Expose Streamlit port
EXPOSE 8501

# Startup script
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
# 移除硬编码的环境变量，改为运行时传入
