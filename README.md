# TALAS Service

API ini dikembangkan menggunakan **Python (Flask)** untuk menyediakan layanan crawling berita, analisis teks, serta berbagai endpoint pemrosesan data seperti deteksi bias, ideologi, hoaks, dan embedding.

## Fitur Utama

- **CRAWLER**  
  - Jalankan crawler untuk mengambil berita terkini  
  - Update status proses crawling  
  - Kelompokkan hasil crawling berdasarkan sumber / kategori  

- **NEWS**  
  - Ambil daftar berita, detail, berita teratas  
  - Pencarian berita berdasarkan judul  
  - Hitung jumlah berita  
  - Filter berita berdasarkan tanggal, sumber, judul, atau grup  

- **CLUSTER**  
  - Ambil daftar cluster berita  

- **Analisis Teks**  
  - Deteksi Bias  
  - Deteksi Hoaks  
  - Deteksi Ideologi  
  - Buat Embedding untuk representasi teks  
  - Ringkasan berita (Summarization)  
  - Pemisahan konten (Separate)  
  - Analisis umum (Analyze)  
  - Pemrosesan judul berita (Title)  

---

## Teknologi yang Digunakan

- **Python 3.12**  
- **Flask 3.1** sebagai framework utama  
- **Flask-CORS** untuk mendukung akses lintas domain  
- **SQLAlchemy 2.0** untuk ORM database  
- **PyTorch 2.4** dan **TensorFlow 2.17** untuk pemodelan machine learning  
- **simpletransformers** untuk NLP pipeline  
- **Loguru** untuk logging  
- **Pytest** untuk pengujian otomatis  

---

## Instalasi

1. **Clone repository**
   ```bash
   git clone https://github.com/MuhammadAliffandy/TALAS-BE.git
   cd TALAS-BE
   ```

2. **Buat virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate    # Linux/Mac
   venv\Scripts\activate       # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

## Virtual Env (Python 3.12.3)

Repository ini sudah menyertakan file versi Python ([.python-version](.python-version) dan [.tool-versions](.tool-versions)) untuk memastikan semua pengembang memakai Python 3.12.3. Pilih salah satu alat berikut:

- **UV (direkomendasikan, ringan & cepat)**
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  uv python install 3.12.3
  uv venv
  source .venv/bin/activate
  uv pip install -r requirements.txt
  ```

- **pyenv**
  ```bash
  pyenv install -s 3.12.3
  pyenv local 3.12.3
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```

- **asdf**
  ```bash
  asdf plugin add python || true
  asdf install
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```

Catatan:
- Folder venv (.venv/ atau venv/) sudah diabaikan di [.gitignore](.gitignore).
- Jika memakai UV, perintah `uv python install` dan `uv venv` otomatis membaca versi dari [.python-version](.python-version).

---

## Menjalankan Server

```bash
python run.py
```

Server default berjalan di `http://localhost:5000/`.

---

## Dokumentasi API

Berikut adalah daftar endpoint yang tersedia (metode dan path):

### CRAWLER
- POST /crawlers/run – Jalankan proses crawling  
- POST /crawlers/update – Update proses crawling  
- GET /crawlers/group – Ambil group crawler  
- GET /crawlers/process – Ambil status proses  

### NEWS
- GET /news – Ambil semua berita  
- GET /news/detail – Ambil detail berita  
- GET /news/top – Ambil berita teratas  
- GET /news/cluster – Ambil berita dalam cluster  
- GET /news/search-title – Cari berita berdasarkan judul  
- GET /news/count-side – Hitung jumlah berita per sisi  
- GET /news/today – Ambil berita hari ini  
- GET /news/today/source – Filter berita hari ini per sumber  
- GET /news/today/title – Filter berita hari ini per judul  
- GET /news/today/groups – Ambil grup berita hari ini  

### CLUSTER
- GET /cluster/list – Ambil daftar cluster berita  

### Analisis Teks
- POST /analyze – Analisis umum teks  
- POST /bias – Deteksi bias  
- POST /cleaned – Bersihkan teks  
- POST /embedding – Buat embedding teks  
- POST /hoax – Deteksi hoaks  
- POST /ideology – Deteksi ideologi  
- POST /separate – Pemisahan konten  
- POST /summary – Ringkasan teks  
- POST /title – Pemrosesan judul  

---

## Testing

Gunakan pytest untuk menjalankan test:
```bash
python -m pytest
```

---

## Kontribusi

1. Fork repository ini  
2. Buat branch fitur baru (`git checkout -b fitur-anda`)  
3. Commit perubahan (`git commit -m 'Tambah fitur X'`)  
4. Push ke branch (`git push origin fitur-anda`)  
5. Ajukan pull request  

---

## Lisensi

Proyek ini menggunakan lisensi MIT – silakan lihat file LICENSE untuk informasi lebih lanjut.
