from utils import ensure_rsa_keys, compute_sha256
from encrypt import hybrid_encrypt_file

priv, pub = ensure_rsa_keys("credentials/rsa_private.pem", "credentials/rsa_public.pem")

# siapkan file uji kecil dulu, misal data/input/test.txt berisi "Hello World"
enc_key, enc_file, aes_key = hybrid_encrypt_file("data/input/test.txt", pub)

print("Encrypted AES key length:", len(enc_key), "bytes")
print("Encrypted file length:", len(enc_file), "bytes")
print("AES key (hex):", aes_key.hex())