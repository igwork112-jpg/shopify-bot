# ============================================================
# 🐍 Base: Python 3.12 + system libs for Pillow, Playwright, Chromium
# ============================================================
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0 \
    DEBIAN_FRONTEND=noninteractive

# ------------------------------------------------------------
# 🧰 Install system dependencies for Pillow + Playwright + Chromium
# ------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    libnss3 \
    libxss1 \
    libasound2 \
    libxshmfence1 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    libxdamage1 \
    libxrandr2 \
    libxcomposite1 \
    libxkbcommon0 \
    libjpeg62-turbo \
    zlib1g \
    libpng16-16 \
    libtiff6 \
    libwebp7 \
    libopenjp2-7 \
    fonts-dejavu \
    fontconfig \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

RUN playwright install --with-deps chromium

COPY . .

RUN mkdir -p logs temp && chmod 755 logs temp

CMD ["python", "app.py"]
