FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	PIP_DISABLE_PIP_VERSION_CHECK=1 \
	PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
	&& pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Run MCP server with SSE transport
CMD ["python", "server.py"]
