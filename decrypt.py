"""
decrypt.py
Fungsi dekripsi AES-256-CBC dan RSA-2048-OAEP, plus verifikasi integritas.
"""
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Util.Padding import unpad

AES_BLOCK_SIZE = 16

# ---------- RSA ----------

def rsa_decrypt(encrypted_data: bytes, private_key) -> bytes:
    """Dekripsi data (AES key) menggunakan RSA private key dengan padding OAEP."""
    cipher_rsa = PKCS1_OAEP.new(private_key)
    return cipher_rsa.decrypt(encrypted_data)

# ---------- AES ----------

def aes_decrypt(encrypted_data: bytes, key: bytes) -> bytes:
    """
    Dekripsi data AES-256-CBC.
    Input format: IV (16 byte) + ciphertext
    """
    iv = encrypted_data[:AES_BLOCK_SIZE]
    ciphertext = encrypted_data[AES_BLOCK_SIZE:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_data = cipher.decrypt(ciphertext)
    return unpad(padded_data, AES_BLOCK_SIZE)

# ---------- Hybrid Decryption (dipakai app.py) ----------

def hybrid_decrypt_file(encrypted_aes_key: bytes, encrypted_file: bytes, private_key) -> bytes:
    """
    Dekripsi file: RSA buka AES key, lalu AES buka data file.
    Return: data asli (bytes)
    """
    aes_key = rsa_decrypt(encrypted_aes_key, private_key)
    original_data = aes_decrypt(encrypted_file, aes_key)
    return original_data