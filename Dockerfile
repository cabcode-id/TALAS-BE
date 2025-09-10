# Gunakan Python versi slim agar image lebih kecil
FROM python:3.11-slim

# Set working directory di dalam container
WORKDIR /app

# Install dependencies OS yang dibutuhkan mysqlclient
RUN apt-get update && apt-get install -y \
    pkg-config \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Salin file requirements.txt terlebih dahulu
COPY requirements.txt .

# Install dependencies Python
RUN pip install --no-cache-dir -r requirements.txt

# Salin semua file project ke container (kecuali yang di .dockerignore)
COPY . .

# Jalankan aplikasi
CMD ["python", "run.py"]
