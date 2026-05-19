"""
Implementasi manual 2D Discrete Cosine Transform (DCT) ukuran 8x8.

DCT diimplementasikan sebagai perkalian matriks: D = M @ block @ M.T
Matriks M dibangun dari basis kosinus dan bersifat orthogonal,
sehingga IDCT cukup pakai transpose: block = M.T @ D @ M.

Tidak menggunakan scipy.fftpack atau cv2.dct.
"""

import numpy as np

N = 8  # Ukuran blok DCT standar (sama dengan JPEG)


def build_dct_matrix(n: int = N) -> np.ndarray:
    """
    Bangun matriks DCT orthogonal ukuran n x n.

    Rumus: M[k, i] = cos(pi * (2i + 1) * k / (2n))
    Baris ke-0 dikalikan sqrt(1/n), sisanya dikalikan sqrt(2/n)
    supaya matriks bersifat orthogonal (M @ M.T = I).
    """
    M = np.zeros((n, n), dtype=np.float32)
    for k in range(n):
        for i in range(n):
            M[k, i] = np.cos(np.pi * (2 * i + 1) * k / (2 * n))
    M[0, :] *= np.sqrt(1.0 / n)
    M[1:, :] *= np.sqrt(2.0 / n)
    return M


# Precompute sekali saat module di-load
DCT_M = build_dct_matrix(N)
IDCT_M = DCT_M.T


def dct2(block: np.ndarray) -> np.ndarray:
    """
    DCT 2D pada blok 8x8.

    Hasil: matriks koefisien frekuensi 8x8.
    Posisi (0,0) = DC (rata-rata kecerahan blok).
    Posisi lainnya = AC (komponen frekuensi).
    """
    return DCT_M @ block @ IDCT_M


def idct2(D: np.ndarray) -> np.ndarray:
    """IDCT 2D - membalik DCT kembali ke domain piksel."""
    return IDCT_M @ D @ DCT_M
