FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create necessary directories
RUN mkdir -p static/uploads/avatars \
             static/uploads/thumbnails \
             static/uploads/videos \
             static/uploads/notes \
             static/uploads/certificates \
             static/uploads/assignments \
             static/uploads/files \
             chroma_db

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
