FROM python:3.11-slim

WORKDIR /PUDA_APP

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system packages required to build
# durable_rules and other native Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["hypercorn", "Backend.app1:app", "--bind", "0.0.0.0:8000"]