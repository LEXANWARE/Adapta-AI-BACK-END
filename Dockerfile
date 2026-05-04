FROM python:3.13-slim

# 1. Install uv from the official binaries
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 2. Prevent Python from writing .pyc files and enable live logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Ensure the root binaries folder is in the path
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# 3. Install minimal build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 4. Copy requirements and install dependencies
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# 5. Copy your project code
COPY . .

# 6. Expose the FastAPI port
EXPOSE 8000

# 7. Start the app. 
# We set PYTHONPATH=. to ensure 'import app' works from the root.
# We use 'app.main' (module syntax) instead of 'app/main.py' for better reliability.
CMD ["sh", "-c", "PYTHONPATH=. fastapi run app/main.py --port ${PORT:-8000} --host 0.0.0.0"]