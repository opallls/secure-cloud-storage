"""
benchmark.py
Membandingkan performa AES-256 vs RSA-2048:
waktu enkripsi/dekripsi, CPU, RAM, ukuran ciphertext, throughput.
Hasil diekspor ke CSV dan divisualisasikan dengan Matplotlib.
"""
import os
import time
import psutil
import pandas as pd
import matplotlib.pyplot as plt

from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Util.Padding import pad, unpad
from Crypto.PublicKey import RSA

RESULTS_CSV = "results/benchmark.csv"
CHARTS_DIR = "results/charts"

# Ukuran RSA-2048 + OAEP (SHA-1 default) max plaintext = 2048/8 - 2*20 - 2 = 214 byte
RSA_MAX_BYTES = 190  # ambil margin aman

process = psutil.Process(os.getpid())


def measure_resources():
    """Ambil snapshot CPU% dan RAM (RSS dalam bytes) saat ini."""
    return process.cpu_percent(interval=None), process.memory_info().rss


def benchmark_aes(data: bytes) -> dict:
    key = get_random_bytes(32)

    mem_before = measure_resources()[1]
    t0 = time.perf_counter()
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = iv + cipher.encrypt(pad(data, 16))
    t1 = time.perf_counter()
    cpu_after, mem_after = measure_resources()

    enc_time = t1 - t0

    t2 = time.perf_counter()
    dec_cipher = AES.new(key, AES.MODE_CBC, ciphertext[:16])
    _ = unpad(dec_cipher.decrypt(ciphertext[16:]), 16)
    t3 = time.perf_counter()
    dec_time = t3 - t2

    return {
        "algorithm": "AES-256",
        "data_size_bytes": len(data),
        "ciphertext_size_bytes": len(ciphertext),
        "encrypt_time_s": enc_time,
        "decrypt_time_s": dec_time,
        "cpu_percent": cpu_after,
        "ram_used_bytes": max(mem_after - mem_before, 0),
        "throughput_mbps": (len(data) / (1024 * 1024)) / enc_time if enc_time > 0 else 0
    }


def benchmark_rsa(data: bytes, public_key, private_key) -> dict:
    if len(data) > RSA_MAX_BYTES:
        data = data[:RSA_MAX_BYTES]  # RSA murni tidak bisa enkripsi data besar

    cipher_rsa_enc = PKCS1_OAEP.new(public_key)
    cipher_rsa_dec = PKCS1_OAEP.new(private_key)

    mem_before = measure_resources()[1]
    t0 = time.perf_counter()
    ciphertext = cipher_rsa_enc.encrypt(data)
    t1 = time.perf_counter()
    cpu_after, mem_after = measure_resources()

    enc_time = t1 - t0

    t2 = time.perf_counter()
    _ = cipher_rsa_dec.decrypt(ciphertext)
    t3 = time.perf_counter()
    dec_time = t3 - t2

    return {
        "algorithm": "RSA-2048",
        "data_size_bytes": len(data),
        "ciphertext_size_bytes": len(ciphertext),
        "encrypt_time_s": enc_time,
        "decrypt_time_s": dec_time,
        "cpu_percent": cpu_after,
        "ram_used_bytes": max(mem_after - mem_before, 0),
        "throughput_mbps": (len(data) / (1024 * 1024)) / enc_time if enc_time > 0 else 0
    }


def run_benchmark():
    print("Generating RSA-2048 keypair untuk benchmark...")
    rsa_key = RSA.generate(2048)
    public_key = rsa_key.publickey()
    private_key = rsa_key

    test_sizes = [1_000, 10_000, 100_000, 1_000_000, 5_000_000]  # bytes
    results = []

    for size in test_sizes:
        print(f"\nMenguji ukuran data: {size} bytes...")
        data = get_random_bytes(size)

        aes_result = benchmark_aes(data)
        results.append(aes_result)
        print(f"  AES-256  -> enc: {aes_result['encrypt_time_s']:.6f}s | "
              f"dec: {aes_result['decrypt_time_s']:.6f}s | "
              f"throughput: {aes_result['throughput_mbps']:.2f} MB/s")

        rsa_result = benchmark_rsa(data, public_key, private_key)
        results.append(rsa_result)
        print(f"  RSA-2048 -> enc: {rsa_result['encrypt_time_s']:.6f}s | "
              f"dec: {rsa_result['decrypt_time_s']:.6f}s | "
              f"(data dipotong jadi {rsa_result['data_size_bytes']} byte, batas RSA-2048)")

    df = pd.DataFrame(results)
    os.makedirs("results", exist_ok=True)
    df.to_csv(RESULTS_CSV, index=False)
    print(f"\n✅ Hasil benchmark disimpan ke {RESULTS_CSV}")

    return df


def plot_results(df: pd.DataFrame):
    os.makedirs(CHARTS_DIR, exist_ok=True)

    metrics = [
        ("encrypt_time_s", "Waktu Enkripsi (detik)", "encrypt_time.png"),
        ("decrypt_time_s", "Waktu Dekripsi (detik)", "decrypt_time.png"),
        ("throughput_mbps", "Throughput (MB/s)", "throughput.png"),
        ("ciphertext_size_bytes", "Ukuran Ciphertext (bytes)", "ciphertext_size.png"),
        ("ram_used_bytes", "Penggunaan RAM (bytes)", "ram_usage.png"),
    ]

    for column, title, filename in metrics:
        plt.figure(figsize=(8, 5))
        for algo in df["algorithm"].unique():
            subset = df[df["algorithm"] == algo]
            plt.plot(subset["data_size_bytes"], subset[column], marker="o", label=algo)
        plt.xlabel("Ukuran Data (bytes)")
        plt.ylabel(title)
        plt.title(f"Perbandingan AES-256 vs RSA-2048: {title}")
        plt.xscale("log")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(CHARTS_DIR, filename))
        plt.close()
        print(f"Chart tersimpan: {CHARTS_DIR}/{filename}")


if __name__ == "__main__":
    df = run_benchmark()
    plot_results(df)