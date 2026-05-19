"""
Implementasi manual kompresi JPEG.

Pipeline:
1. RGB -> YCbCr
2. Geser nilai dengan -128 (level shift)
3. DCT per blok 8x8
4. Kuantisasi: bagi tiap koefisien dengan tabel kuantisasi, bulatkan
5. Dequantisasi: kalikan kembali dengan tabel
6. IDCT
7. Geser kembali dengan +128
8. YCbCr -> RGB

Tidak menggunakan PIL.Image.save(quality=...) atau cv2.imencode.
Yang menentukan tingkat kompresi adalah Quality Factor (QF):
- QF tinggi (95) -> step kuantisasi kecil -> kualitas tinggi
- QF rendah (10) -> step kuantisasi besar -> kualitas rendah
"""

import numpy as np
from watermark.color import rgb_to_ycbcr, ycbcr_to_rgb
from watermark.dct import dct2, idct2


# Tabel kuantisasi standar JPEG untuk luminance (Y)
Q_LUMA = np.array([
    [16, 11, 10, 16,  24,  40,  51,  61],
    [12, 12, 14, 19,  26,  58,  60,  55],
    [14, 13, 16, 24,  40,  57,  69,  56],
    [14, 17, 22, 29,  51,  87,  80,  62],
    [18, 22, 37, 56,  68, 109, 103,  77],
    [24, 35, 55, 64,  81, 104, 113,  92],
    [49, 64, 78, 87, 103, 121, 120, 101],
    [72, 92, 95, 98, 112, 100, 103,  99],
], dtype=np.float32)


# Tabel kuantisasi standar JPEG untuk chrominance (Cb, Cr)
Q_CHROMA = np.array([
    [17, 18, 24, 47, 99, 99, 99, 99],
    [18, 21, 26, 66, 99, 99, 99, 99],
    [24, 26, 56, 99, 99, 99, 99, 99],
    [47, 66, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
], dtype=np.float32)


def scale_q_table(Q: np.ndarray, qf: int) -> np.ndarray:
    """
    Skalakan tabel kuantisasi berdasarkan Quality Factor.

    Rumus IJG (Independent JPEG Group):
    - S = 5000/QF  jika QF < 50
    - S = 200 - 2*QF  jika QF >= 50
    - Qs = floor((Q * S + 50) / 100), minimal 1
    """
    qf = max(1, min(100, qf))
    S = 5000 / qf if qf < 50 else 200 - 2 * qf
    Qs = np.floor((Q * S + 50) / 100)
    Qs[Qs < 1] = 1
    return Qs


def jpeg_compress_channel(channel: np.ndarray, qf: int, Q_table: np.ndarray) -> np.ndarray:
    """Kompresi satu channel melalui pipeline JPEG (DCT -> quantize -> IDCT)."""
    Qs = scale_q_table(Q_table, qf)
    h, w = channel.shape
    out = np.zeros_like(channel, dtype=np.float32)
    # Level shift: nilai piksel digeser ke range [-128, 127]
    ch = channel.astype(np.float32) - 128.0

    for i in range(0, h, 8):
        for j in range(0, w, 8):
            block = ch[i:i + 8, j:j + 8]
            D = dct2(block)
            # Kuantisasi + dequantisasi (di sinilah informasi hilang)
            Dq = np.round(D / Qs) * Qs
            out[i:i + 8, j:j + 8] = idct2(Dq)
    return out + 128.0


def jpeg_compress_image(rgb: np.ndarray, qf: int):
    """
    Kompresi gambar RGB dengan pipeline JPEG manual.

    Returns
    -------
    tuple
        (rgb_terkompresi, Y_terkompresi)
        Y_terkompresi dikembalikan juga supaya bisa dipakai untuk ekstraksi
        watermark tanpa harus konversi balik.
    """
    ycc = rgb_to_ycbcr(rgb)
    Yc = jpeg_compress_channel(ycc[..., 0], qf, Q_LUMA)
    Cbc = jpeg_compress_channel(ycc[..., 1], qf, Q_CHROMA)
    Crc = jpeg_compress_channel(ycc[..., 2], qf, Q_CHROMA)
    rgb_out = ycbcr_to_rgb(np.stack([Yc, Cbc, Crc], axis=-1))
    return rgb_out, Yc
