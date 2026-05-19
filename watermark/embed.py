"""
Embed dan extract watermark menggunakan teknik DCT-QIM.

QIM (Quantization Index Modulation):
- Tiap blok 8x8 menyimpan 1 bit watermark.
- Bit disisipkan pada satu koefisien DCT di frekuensi menengah.
- Aturan: q = round(coef / DELTA). Jika q genap -> bit 0, jika ganjil -> bit 1.
- Jika parity tidak cocok dengan bit yang ingin disimpan, geser q ke +/- 1.

Pemilihan posisi (4, 3) adalah kompromi:
- Frekuensi rendah -> watermark terlihat (gambar rusak)
- Frekuensi tinggi -> dihapus JPEG (watermark hilang)
- Frekuensi menengah -> bertahan kompresi sambil tetap tidak terlihat
"""

import numpy as np
from watermark.dct import dct2, idct2

# Parameter default
DELTA_DEFAULT = 30
COEF_POS_DEFAULT = (4, 3)


def embed_watermark(
    Y_channel: np.ndarray,
    wm: np.ndarray,
    delta: float = DELTA_DEFAULT,
    coef_pos: tuple = COEF_POS_DEFAULT,
) -> np.ndarray:
    """
    Sisipkan watermark biner ke dalam channel Y menggunakan DCT-QIM.

    Parameters
    ----------
    Y_channel : np.ndarray
        Channel luminance, shape (H, W). H dan W harus kelipatan 8.
    wm : np.ndarray
        Watermark biner (0/1), shape (wm_h, wm_w).
    delta : float
        Step kuantisasi. Lebih besar = lebih tahan kompresi tapi lebih terlihat.
    coef_pos : tuple
        Posisi (baris, kolom) koefisien DCT yang dipakai untuk embedding.

    Returns
    -------
    np.ndarray
        Channel Y yang sudah berisi watermark, float32.
    """
    Y_wm = Y_channel.copy().astype(np.float32)
    bits = wm.flatten()
    h, w = Y_channel.shape
    r, c = coef_pos
    idx = 0

    for i in range(0, h, 8):
        for j in range(0, w, 8):
            if idx >= len(bits):
                return Y_wm
            block = Y_wm[i:i + 8, j:j + 8]
            D = dct2(block)
            coef = D[r, c]
            q = round(coef / delta)
            # Geser q ke parity yang benar
            if (int(q) % 2) != int(bits[idx]):
                q = q + 1 if coef > q * delta else q - 1
            D[r, c] = q * delta
            Y_wm[i:i + 8, j:j + 8] = idct2(D)
            idx += 1
    return Y_wm


def extract_watermark(
    Y_channel: np.ndarray,
    wm_shape: tuple,
    delta: float = DELTA_DEFAULT,
    coef_pos: tuple = COEF_POS_DEFAULT,
) -> np.ndarray:
    """
    Ekstrak watermark biner dari channel Y.

    Untuk setiap blok 8x8, hitung DCT, lalu bit = round(coef / delta) % 2.
    """
    Y_channel = Y_channel.astype(np.float32)
    h, w = Y_channel.shape
    r, c = coef_pos
    bits = np.zeros(wm_shape[0] * wm_shape[1], dtype=np.uint8)
    idx = 0

    for i in range(0, h, 8):
        for j in range(0, w, 8):
            if idx >= len(bits):
                return bits.reshape(wm_shape)
            block = Y_channel[i:i + 8, j:j + 8]
            D = dct2(block)
            q = round(D[r, c] / delta)
            bits[idx] = int(q) % 2
            idx += 1
    return bits.reshape(wm_shape)


def generate_watermark(size: int = 32, seed: int = 42) -> np.ndarray:
    """Buat watermark biner acak ukuran size x size dengan seed reproducible."""
    rng = np.random.default_rng(seed)
    return rng.integers(0, 2, (size, size)).astype(np.uint8)
