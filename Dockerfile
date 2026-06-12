FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary upload directories and chroma_db
RUN mkdir -p static/uploads/avatars \
             static/uploads/thumbnails \
             static/uploads/videos \
             static/uploads/notes \
             static/uploads/certificates \
             static/uploads/assignments \
             static/uploads/files \
             chroma_db

# Seed the database with demo data
RUN python seed.py

EXPOSE 8000

# Use gunicorn with uvicorn workers for production
CMD ["gunicorn", "main:app", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "120", "--graceful-timeout", "30", "--access-logfile", "-"]
