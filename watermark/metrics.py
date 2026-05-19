"""
Metrik evaluasi watermarking.

- PSNR: kualitas visual gambar watermarked vs original (higher = better)
- BER: bit error rate watermark hasil ekstraksi vs original (lower = better)
- NC: normalized correlation antara dua watermark (closer to 1 = better)
"""

import numpy as np


def psnr(original: np.ndarray, modified: np.ndarray) -> float:
    """
    Peak Signal-to-Noise Ratio dalam dB.

    > 40 dB : sangat baik, tidak terlihat
    30-40 dB: baik, sangat sulit dilihat
    < 30 dB : watermark mulai terlihat sebagai noise
    """
    orig = original.astype(np.float32)
    mod = modified.astype(np.float32)
    mse = np.mean((orig - mod) ** 2)
    if mse == 0:
        return float("inf")
    return 10.0 * np.log10(255.0 ** 2 / mse)


def ber(wm_original: np.ndarray, wm_extracted: np.ndarray) -> float:
    """Bit Error Rate: proporsi bit yang berbeda antara dua watermark."""
    return float(np.mean(wm_original != wm_extracted))


def nc(wm_original: np.ndarray, wm_extracted: np.ndarray) -> float:
    """
    Normalized Correlation antara dua watermark biner.

    Nilai dikonversi dari {0, 1} ke {-1, +1} sebelum dihitung.
    Hasil: 1 = identik, 0 = tidak berkorelasi, -1 = terbalik.
    """
    a = 2 * wm_original.astype(np.float32) - 1
    b = 2 * wm_extracted.astype(np.float32) - 1
    denom = np.sqrt(np.sum(a * a) * np.sum(b * b))
    if denom == 0:
        return 0.0
    return float(np.sum(a * b) / denom)
