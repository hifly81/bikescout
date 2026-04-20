FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY README.md .

COPY src/ ./src/

RUN pip install --no-cache-dir .

COPY . .

CMD ["bikescout"]