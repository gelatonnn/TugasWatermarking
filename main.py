"""
Main script untuk eksperimen watermarking dengan kompresi JPEG.

Cara pakai:
    python main.py path/to/photo.jpg
    python main.py path/to/photo.jpg --delta 30 --wm-size 32
    python main.py path/to/photo.jpg --no-show   (tidak menampilkan plot, hanya simpan)

Output disimpan di folder ./output/:
    - watermarked.png      : gambar yang sudah berisi watermark
    - watermark.png        : watermark biner asli
    - comparison.png       : perbandingan original vs watermarked
    - robustness.png       : grid hasil ekstraksi pada berbagai QF
    - ber_curve.png        : grafik BER dan NC vs QF
    - results.csv          : tabel hasil eksperimen
"""

import argparse
import os
import csv

import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

from watermark import (
    rgb_to_ycbcr,
    ycbcr_to_rgb,
    embed_watermark,
    extract_watermark,
    jpeg_compress_image,
    psnr,
    ber,
    nc,
)
from watermark.embed import generate_watermark


QF_VALUES = [95, 90, 80, 70, 60, 50, 40, 30, 20, 10]


def load_image(path: str) -> np.ndarray:
    """Buka gambar dan crop ke kelipatan 8."""
    img = np.array(Image.open(path).convert("RGB"))
    h, w = img.shape[:2]
    new_h, new_w = (h // 8) * 8, (w // 8) * 8
    return img[:new_h, :new_w]


def run_experiment(
    image_path: str,
    delta: float = 30,
    wm_size: int = 32,
    output_dir: str = "output",
    show: bool = True,
):
    os.makedirs(output_dir, exist_ok=True)

    # ---- STEP 1: Load gambar ----
    print("\n[1/6] Memuat gambar...")
    img = load_image(image_path)
    h, w = img.shape[:2]
    num_blocks = (h // 8) * (w // 8)
    print(f"      Ukuran: {h}x{w}, jumlah blok 8x8: {num_blocks}")

    # ---- STEP 2: Konversi YCbCr ----
    print("[2/6] Konversi RGB -> YCbCr...")
    ycbcr = rgb_to_ycbcr(img)
    Y_orig = ycbcr[..., 0].copy()
    Cb_orig = ycbcr[..., 1].copy()
    Cr_orig = ycbcr[..., 2].copy()
    print(f"      Y range: [{Y_orig.min():.1f}, {Y_orig.max():.1f}]")

    # ---- STEP 3: Generate watermark ----
    print(f"[3/6] Membuat watermark biner acak {wm_size}x{wm_size}...")
    wm = generate_watermark(size=wm_size, seed=42)
    total_bits = wm_size * wm_size
    if num_blocks < total_bits:
        raise ValueError(
            f"Gambar terlalu kecil: butuh {total_bits} blok, hanya tersedia {num_blocks}"
        )
    print(f"      Total bit: {total_bits} ({100 * total_bits / num_blocks:.1f}% dari blok)")
    Image.fromarray((wm * 255).astype(np.uint8)).save(
        os.path.join(output_dir, "watermark.png")
    )

    # ---- STEP 4: Embed watermark ----
    print(f"[4/6] Menyisipkan watermark dengan DELTA={delta}...")
    Y_wm = embed_watermark(Y_orig, wm, delta=delta)
    Y_wm_clipped = np.clip(Y_wm, 0, 255)
    img_wm = ycbcr_to_rgb(np.stack([Y_wm_clipped, Cb_orig, Cr_orig], axis=-1))

    psnr_val = psnr(img, img_wm)
    print(f"      PSNR: {psnr_val:.2f} dB")
    Image.fromarray(img_wm).save(os.path.join(output_dir, "watermarked.png"))

    # Sanity check tanpa serangan
    wm_check = extract_watermark(Y_wm_clipped, wm.shape, delta=delta)
    print(f"      BER tanpa serangan: {ber(wm, wm_check):.4f}")

    # Plot perbandingan
    fig, ax = plt.subplots(1, 3, figsize=(13, 5))
    ax[0].imshow(img); ax[0].set_title("Original"); ax[0].axis("off")
    ax[1].imshow(img_wm); ax[1].set_title(f"Watermarked\nPSNR={psnr_val:.2f} dB"); ax[1].axis("off")
    diff = np.abs(img.astype(np.float32) - img_wm.astype(np.float32)).mean(axis=2)
    ax[2].imshow(np.clip(diff * 8, 0, 255).astype(np.uint8), cmap="hot")
    ax[2].set_title("Difference (x8)"); ax[2].axis("off")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "comparison.png"), dpi=120, bbox_inches="tight")
    if show:
        plt.show()
    plt.close()

    # ---- STEP 5: Uji robustness terhadap JPEG ----
    print("[5/6] Menguji robustness terhadap kompresi JPEG...")
    print(f"      {'QF':<6}{'BER':<10}{'NC':<10}{'Status'}")
    print("      " + "-" * 40)

    results = []
    fail_qf = None

    fig, axes = plt.subplots(2, len(QF_VALUES), figsize=(2.2 * len(QF_VALUES), 5))
    for k, qf in enumerate(QF_VALUES):
        img_jpeg, Y_jpeg = jpeg_compress_image(img_wm, qf)
        wm_ext = extract_watermark(Y_jpeg, wm.shape, delta=delta)
        b = ber(wm, wm_ext)
        n = nc(wm, wm_ext)
        results.append((qf, b, n))

        if b < 0.05:
            status = "Extractable"
        elif b < 0.25:
            status = "Degraded"
        else:
            status = "FAILED"
            if fail_qf is None:
                fail_qf = qf

        print(f"      {qf:<6}{b:<10.4f}{n:<10.4f}{status}")

        axes[0, k].imshow(img_jpeg); axes[0, k].set_title(f"QF={qf}"); axes[0, k].axis("off")
        axes[1, k].imshow(wm_ext, cmap="gray")
        axes[1, k].set_title(f"BER={b:.3f}\nNC={n:.2f}"); axes[1, k].axis("off")

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "robustness.png"), dpi=120, bbox_inches="tight")
    if show:
        plt.show()
    plt.close()

    # ---- STEP 6: Plot kurva & simpan CSV ----
    print("[6/6] Menyimpan grafik dan CSV...")
    qfs = [r[0] for r in results]
    bers = [r[1] for r in results]
    ncs = [r[2] for r in results]

    fig, ax1 = plt.subplots(figsize=(8, 4))
    ax1.plot(qfs, bers, "o-", color="crimson", label="BER")
    ax1.set_xlabel("JPEG Quality Factor (QF)")
    ax1.set_ylabel("Bit Error Rate", color="crimson")
    ax1.axhline(0.05, linestyle="--", color="gray", alpha=0.5)
    ax1.invert_xaxis()
    ax2 = ax1.twinx()
    ax2.plot(qfs, ncs, "s-", color="steelblue", label="NC")
    ax2.set_ylabel("Normalized Correlation", color="steelblue")
    plt.title("Watermark robustness vs JPEG QF")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "ber_curve.png"), dpi=120, bbox_inches="tight")
    if show:
        plt.show()
    plt.close()

    # Simpan hasil ke CSV
    csv_path = os.path.join(output_dir, "results.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["QF", "BER", "NC", "Status"])
        for qf, b, n in results:
            status = "Extractable" if b < 0.05 else "Degraded" if b < 0.25 else "FAILED"
            writer.writerow([qf, f"{b:.4f}", f"{n:.4f}", status])

    print("\n=== Kesimpulan ===")
    if fail_qf is not None:
        print(f"  Watermark gagal diekstrak mulai dari QF = {fail_qf} ke bawah.")
        last_ok = max((qf for qf, b, _ in results if b < 0.25), default=None)
        if last_ok is not None:
            print(f"  Hingga QF = {last_ok}, watermark masih bisa dikenali.")
    else:
        print("  Watermark bertahan di semua nilai QF yang diuji.")

    print(f"\n  Semua output tersimpan di: {os.path.abspath(output_dir)}/")
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Eksperimen watermarking DCT-QIM terhadap kompresi JPEG"
    )
    parser.add_argument("image", help="Path ke gambar wajah (jpg/png)")
    parser.add_argument("--delta", type=float, default=30,
                        help="Step kuantisasi QIM (default: 30)")
    parser.add_argument("--wm-size", type=int, default=32,
                        help="Ukuran sisi watermark biner (default: 32 -> 32x32 bit)")
    parser.add_argument("--output-dir", default="output",
                        help="Folder output (default: ./output)")
    parser.add_argument("--no-show", action="store_true",
                        help="Jangan tampilkan plot, hanya simpan ke file")
    args = parser.parse_args()

    run_experiment(
        image_path=args.image,
        delta=args.delta,
        wm_size=args.wm_size,
        output_dir=args.output_dir,
        show=not args.no_show,
    )


if __name__ == "__main__":
    main()
