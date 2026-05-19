"""
Konversi ruang warna RGB <-> YCbCr (ITU-R BT.601).

Rumus konversi ini standar yang dipakai JPEG. Komponen Y menyimpan
kecerahan (luminance), Cb dan Cr menyimpan informasi warna (chrominance).
Watermark disisipkan hanya di Y karena mata manusia paling sensitif
terhadap perubahan kecerahan, sehingga lebih mudah memprediksi
seberapa terlihat watermarknya.
"""

import numpy as np


def rgb_to_ycbcr(rgb: np.ndarray) -> np.ndarray:
    """
    Konversi gambar RGB menjadi YCbCr.

    Parameters
    ----------
    rgb : np.ndarray
        Array bentuk (H, W, 3) dengan nilai piksel 0-255.

    Returns
    -------
    np.ndarray
        Array float32 bentuk (H, W, 3) berisi [Y, Cb, Cr].
    """
    rgb = rgb.astype(np.float32)
    R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    Y  =  0.299    * R + 0.587    * G + 0.114    * B
    Cb = -0.168736 * R - 0.331264 * G + 0.5      * B + 128.0
    Cr =  0.5      * R - 0.418688 * G - 0.081312 * B + 128.0
    return np.stack([Y, Cb, Cr], axis=-1)


def ycbcr_to_rgb(ycbcr: np.ndarray) -> np.ndarray:
    """
    Konversi gambar YCbCr kembali menjadi RGB.

    Parameters
    ----------
    ycbcr : np.ndarray
        Array float bentuk (H, W, 3) berisi [Y, Cb, Cr].

    Returns
    -------
    np.ndarray
        Array uint8 bentuk (H, W, 3) dengan nilai piksel 0-255.
    """
    Y  = ycbcr[..., 0]
    Cb = ycbcr[..., 1] - 128.0
    Cr = ycbcr[..., 2] - 128.0
    R = Y + 1.402    * Cr
    G = Y - 0.344136 * Cb - 0.714136 * Cr
    B = Y + 1.772    * Cb
    rgb = np.stack([R, G, B], axis=-1)
    return np.clip(rgb, 0, 255).astype(np.uint8)
