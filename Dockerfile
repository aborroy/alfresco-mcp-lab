# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY chainlit.md .
COPY .env.example .

# Create a non-root user
RUN useradd -m -u 1000 chainlit && chown -R chainlit:chainlit /app
USER chainlit

# Expose port
EXPOSE 8000


# Run the application
CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8000"]
