"""
utils.py
Helper functions: hashing, file I/O, key management, formatting.
"""
import os
import hashlib
from Crypto.PublicKey import RSA

# ---------- Hashing & Integrity ----------

def compute_sha256(data: bytes) -> str:
    """Hitung SHA-256 hash dari data (bytes) -> hex string."""
    return hashlib.sha256(data).hexdigest()

def compute_file_hash(filepath: str) -> str:
    """Hitung SHA-256 hash dari isi file di disk."""
    with open(filepath, "rb") as f:
        return compute_sha256(f.read())

def verify_integrity(original_hash: str, current_data: bytes) -> bool:
    """Bandingkan hash asli dengan hash data saat ini."""
    return original_hash == compute_sha256(current_data)

# ---------- File I/O ----------

def read_file_bytes(filepath: str) -> bytes:
    with open(filepath, "rb") as f:
        return f.read()

def write_file_bytes(filepath: str, data: bytes) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(data)

# ---------- RSA Key Management ----------

def generate_rsa_keypair(key_size: int = 2048):
    """Generate RSA keypair, return (private_key, public_key) sebagai objek RSA."""
    key = RSA.generate(key_size)
    return key, key.publickey()

def save_rsa_key(key, filepath: str) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(key.export_key())

def load_rsa_key(filepath: str):
    with open(filepath, "rb") as f:
        return RSA.import_key(f.read())

def ensure_rsa_keys(priv_path: str, pub_path: str):
    """Buat keypair RSA jika belum ada, atau load jika sudah ada."""
    if os.path.exists(priv_path) and os.path.exists(pub_path):
        return load_rsa_key(priv_path), load_rsa_key(pub_path)
    priv, pub = generate_rsa_keypair()
    save_rsa_key(priv, priv_path)
    save_rsa_key(pub, pub_path)
    return priv, pub

# ---------- Formatting (untuk benchmark) ----------

def format_size(num_bytes: int) -> str:
    """Format ukuran byte jadi human-readable (KB/MB)."""
    for unit in ["B", "KB", "MB", "GB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.2f} TB"