FROM rust:1.88-slim AS wallet-builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc pkg-config ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY ACP-crypto ./ACP-crypto
RUN cargo build --manifest-path ACP-crypto/Cargo.toml --bin walletd --release --locked --jobs 2

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc curl ca-certificates pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV PYTHONPATH=/app
EXPOSE 8000

COPY --from=wallet-builder /app/ACP-crypto/target/release/walletd /usr/local/bin/walletd
RUN chmod +x /usr/local/bin/walletd

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
