FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# The application code imports itself as the `backend` package (from backend.x
# import ...), so it must live under a `backend/` dir that is on the import path.
# The build context is ./backend, so copy its contents into /app/backend.
COPY . ./backend

# Make /app importable so `import backend` resolves to /app/backend.
ENV PYTHONPATH=/app

RUN chmod +x /app/backend/start.sh

# 7860 is the local/default port; Render overrides via $PORT (see start.sh).
EXPOSE 7860

# start.sh runs migrations then binds uvicorn to ${PORT:-7860}.
CMD ["/app/backend/start.sh"]
