"""
encrypt.py
Fungsi enkripsi AES-256-CBC dan RSA-2048-OAEP.
"""
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes

AES_KEY_SIZE = 32   # 256 bit
AES_BLOCK_SIZE = 16 # 128 bit block

# ---------- AES-256 ----------

def generate_aes_key() -> bytes:
    """Generate random AES-256 key (32 byte)."""
    return get_random_bytes(AES_KEY_SIZE)

def aes_encrypt(data: bytes, key: bytes) -> bytes:
    """
    Enkripsi data dengan AES-256-CBC.
    Output format: IV (16 byte) + ciphertext
    """
    iv = get_random_bytes(AES_BLOCK_SIZE)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_data = pad(data, AES_BLOCK_SIZE)
    ciphertext = cipher.encrypt(padded_data)
    return iv + ciphertext

# ---------- RSA-2048 ----------

def rsa_encrypt(data: bytes, public_key) -> bytes:
    """
    Enkripsi data (biasanya AES key, harus < ~190 byte untuk RSA-2048 OAEP)
    menggunakan RSA public key dengan padding OAEP.
    """
    cipher_rsa = PKCS1_OAEP.new(public_key)
    return cipher_rsa.encrypt(data)

# ---------- Hybrid Encryption (dipakai app.py) ----------

def hybrid_encrypt_file(filepath_in: str, public_key):
    """
    Enkripsi file: AES-256 untuk data, RSA-2048 untuk AES key.
    Return: (encrypted_aes_key, encrypted_file_bytes, aes_key)
    aes_key dikembalikan juga untuk keperluan logging/benchmark, JANGAN
    disimpan plaintext di produksi nyata.
    """
    with open(filepath_in, "rb") as f:
        file_data = f.read()

    aes_key = generate_aes_key()
    encrypted_file = aes_encrypt(file_data, aes_key)
    encrypted_aes_key = rsa_encrypt(aes_key, public_key)

    return encrypted_aes_key, encrypted_file, aes_key

def hybrid_encrypt_bytes(file_data: bytes, public_key):
    """Sama seperti hybrid_encrypt_file, tapi input berupa bytes langsung."""
    aes_key = generate_aes_key()
    encrypted_file = aes_encrypt(file_data, aes_key)
    encrypted_aes_key = rsa_encrypt(aes_key, public_key)
    return encrypted_aes_key, encrypted_file, aes_key


def hybrid_encrypt_file(filepath_in: str, public_key):
    with open(filepath_in, "rb") as f:
        file_data = f.read()
    return hybrid_encrypt_bytes(file_data, public_key)