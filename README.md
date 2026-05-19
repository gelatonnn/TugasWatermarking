# JPEG Watermarking dengan DCT-QIM
## Francis Galton - 18224072

Implementasi watermarking citra digital menggunakan teknik **DCT-QIM (Quantization Index Modulation)** dan evaluasi ketahanannya terhadap kompresi JPEG pada berbagai nilai Quality Factor (QF).

Semua algoritma inti — DCT, IDCT, konversi ruang warna, dan kompresi JPEG — diimplementasikan **manual hanya dengan NumPy**. Tidak menggunakan `scipy.fftpack`, `cv2.dct`, atau fitur kompresi bawaan dari PIL.

## Tujuan

1. Menyisipkan watermark biner pada foto wajah.
2. Mengevaluasi ketahanan watermark terhadap kompresi JPEG.
3. Menemukan nilai QF yang membuat watermark tidak dapat diekstrak.

## Struktur Project

```
TugasWatermarking/
├── watermark/
│   ├── __init__.py
│   ├── color.py        # Konversi RGB <-> YCbCr
│   ├── dct.py          # DCT/IDCT 8x8 manual
│   ├── embed.py        # Embed & extract watermark (QIM)
│   ├── jpeg.py         # Kompresi JPEG manual
│   └── metrics.py      # PSNR, BER, NC
├── main.py             # Entry point CLI
├── requirements.txt
|-- wajah.jpg
├── .gitignore
└── README.md
```

## Instalasi

```bash
# Clone repository
git clone https://github.com/USERNAME/jpeg-watermarking.git
cd jpeg-watermarking

# (Opsional) buat virtual environment
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt
```

## Cara Menjalankan

```bash
# Jalankan dengan foto wajah Anda
python main.py path/to/wajah.jpg

# Atur parameter
python main.py wajah.jpg --delta 30 --wm-size 32

# Jalankan tanpa menampilkan plot (hanya simpan ke file)
python main.py wajah.jpg --no-show
```

### Parameter

| Parameter | Default | Deskripsi |
|-----------|---------|-----------|
| `image` | (wajib) | Path ke gambar wajah |
| `--delta` | `30` | Step kuantisasi QIM (besar = tahan kompresi, tapi lebih terlihat) |
| `--wm-size` | `32` | Ukuran watermark biner (32 = 32×32 = 1024 bit) |
| `--output-dir` | `output` | Folder untuk menyimpan hasil |
| `--no-show` | - | Jangan tampilkan plot (berguna untuk batch) |

## Output

Setelah dijalankan, folder `output/` akan berisi:

- `watermark.png` — watermark biner asli
- `watermarked.png` — gambar yang sudah disisipi watermark
- `comparison.png` — perbandingan original, watermarked, dan difference map
- `robustness.png` — hasil ekstraksi watermark pada berbagai QF
- `ber_curve.png` — grafik BER dan NC terhadap QF
- `results.csv` — tabel hasil dalam format CSV

## Penjelasan Singkat Algoritma

### 1. Konversi Ruang Warna (RGB → YCbCr)
Gambar diubah ke YCbCr supaya kita bisa bekerja hanya pada channel Y (luminance), karena mata manusia paling sensitif terhadap perubahan kecerahan.

### 2. DCT 8×8
Setiap blok 8×8 piksel pada channel Y diubah ke domain frekuensi menggunakan DCT 2D yang diimplementasikan sebagai perkalian matriks:

```
D = M · block · M^T
```

di mana `M[k,i] = cos(π(2i+1)k / 16)`.

### 3. Embedding (QIM)
Untuk tiap blok, koefisien DCT di posisi (4, 3) — frekuensi menengah — dikuantisasi:

```
q = round(coef / DELTA)
```

- Jika `q` genap → blok menyimpan bit 0
- Jika `q` ganjil → blok menyimpan bit 1
- Jika parity tidak cocok, geser `q` ke ±1

Lalu blok dikembalikan ke domain piksel via IDCT.

### 4. Ekstraksi
Untuk tiap blok di gambar yang dicurigai, hitung DCT, ambil koefisien (4, 3), bagi DELTA, bulatkan, lalu cek parity untuk mendapatkan bit.

### 5. Serangan JPEG Manual
Pipeline JPEG diimplementasikan dari nol:
1. Level shift (-128)
2. DCT per blok 8×8
3. Kuantisasi dengan tabel standar yang diskalakan menurut QF
4. Dequantisasi
5. IDCT
6. Level shift kembali (+128)

### 6. Metrik
- **PSNR** — kualitas visual gambar watermarked
- **BER** — proporsi bit watermark yang salah saat diekstrak
- **NC** — korelasi antara watermark asli dan hasil ekstraksi

## Trade-off DELTA

| DELTA | PSNR | Robustness |
|-------|------|------------|
| Kecil (10–20) | Tinggi (tidak terlihat) | Rendah (cepat rusak kena JPEG) |
| Sedang (30) | Cukup baik | Cukup tahan |
| Besar (50+) | Rendah (mulai terlihat) | Sangat tahan |