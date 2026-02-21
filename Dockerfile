# Build: docker build -t blk-hacking-ind-winson .
# Run:   docker run -d -p 5477:5477 blk-hacking-ind-winson

# python:3.11-slim (Debian) - small image, compatible with psutil/uvicorn C extensions
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 5477

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5477/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5477", "--workers", "1"]
