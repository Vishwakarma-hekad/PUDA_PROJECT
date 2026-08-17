FROM python:3.11-slim

WORKDIR /PUDA_APP

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# --------------------------------------------------
# Headless Qt / X11
# --------------------------------------------------

ENV QT_QPA_PLATFORM=xcb
ENV DISPLAY=:99
ENV XDG_RUNTIME_DIR=/tmp/runtime-root

# --------------------------------------------------
# System dependencies
# --------------------------------------------------

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        build-essential \
        procps \
        xvfb \
        libgl1 \
        libglib2.0-0 \
        libx11-6 \
        libx11-xcb1 \
        libxext6 \
        libxrender1 \
        libxfixes3 \
        libxi6 \
        libxrandr2 \
        libxkbcommon0 \
        libxkbcommon-x11-0 \
        libxcb1 \
        libxcb-cursor0 \
        libxcb-xinerama0 \
        libxcb-xkb1 \
        libxcb-render-util0 \
        libxcb-image0 \
        libxcb-keysyms1 \
        libxcb-icccm4 \
        libxcb-shape0 \
        libfontconfig1 \
        libfreetype6 \
        libdbus-1-3 \
        libsm6 \
        libice6 \
    && rm -rf /var/lib/apt/lists/*

# --------------------------------------------------
# Install ODA File Converter
# --------------------------------------------------

COPY docker/oda/ODAFileConverter_QT6_lnxX64_8.3dll_27.1.deb /tmp/oda.deb

RUN apt-get update && \
    apt-get install -y --no-install-recommends /tmp/oda.deb && \
    rm -f /tmp/oda.deb && \
    rm -rf /var/lib/apt/lists/*

# --------------------------------------------------
# Python dependencies
# --------------------------------------------------

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# --------------------------------------------------
# Copy application
# --------------------------------------------------

COPY . .

# --------------------------------------------------
# Create XDG runtime directory
# --------------------------------------------------

RUN mkdir -p /tmp/runtime-root && \
    chmod 700 /tmp/runtime-root

# --------------------------------------------------
# Application port
# --------------------------------------------------

EXPOSE 8000

# --------------------------------------------------
# Default command
# Xvfb is started before FastAPI
# --------------------------------------------------

CMD ["sh", "-c", "Xvfb :99 -screen 0 1024x768x24 -ac & exec hypercorn app:app --bind 0.0.0.0:8000"]