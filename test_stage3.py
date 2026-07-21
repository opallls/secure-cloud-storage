from utils import ensure_rsa_keys, compute_sha256
from encrypt import hybrid_encrypt_file
from decrypt import hybrid_decrypt_file

priv, pub = ensure_rsa_keys("credentials/rsa_private.pem", "credentials/rsa_public.pem")

# Enkripsi
with open("data/input/test.txt", "rb") as f:
    original_data = f.read()

original_hash = compute_sha256(original_data)
enc_key, enc_file, aes_key = hybrid_encrypt_file("data/input/test.txt", pub)

print("Encrypted AES key length:", len(enc_key), "bytes")
print("Encrypted file length:", len(enc_file), "bytes")

# Dekripsi
decrypted_data = hybrid_decrypt_file(enc_key, enc_file, priv)
decrypted_hash = compute_sha256(decrypted_data)

# Verifikasi integritas
print("Original hash :", original_hash)
print("Decrypted hash:", decrypted_hash)
print("Integritas terjaga?", original_hash == decrypted_hash)

# ==== GANTI BAGIAN INI ====
try:
    print("Isi file hasil dekripsi:", decrypted_data.decode("utf-8"))
except UnicodeDecodeError:
    print("Isi file hasil dekripsi (binary, tidak bisa ditampilkan sebagai teks):", decrypted_data[:50], "...")