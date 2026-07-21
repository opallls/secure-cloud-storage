import os
import json
import sys

from utils import ensure_rsa_keys, compute_sha256, write_file_bytes
from encrypt import hybrid_encrypt_file
from decrypt import hybrid_decrypt_file
from google_drive import get_drive_service, upload_file, download_file

PRIVATE_KEY_PATH = "credentials/rsa_private.pem"
PUBLIC_KEY_PATH = "credentials/rsa_public.pem"
MANIFEST_PATH = "results/manifest.json"


def load_manifest() -> dict:
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, "r") as f:
            return json.load(f)
    return {}


def save_manifest(manifest: dict) -> None:
    os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)


def do_upload(filepath: str):
    priv, pub = ensure_rsa_keys(PRIVATE_KEY_PATH, PUBLIC_KEY_PATH)
    filename = os.path.basename(filepath)

    print(f"[1/4] Membaca & menghitung hash asli: {filename}")
    with open(filepath, "rb") as f:
        original_data = f.read()
    original_hash = compute_sha256(original_data)

    print("[2/4] Enkripsi AES-256 + RSA-2048...")
    enc_key, enc_file, _ = hybrid_encrypt_file(filepath, pub)

    print("[3/4] Upload ke Google Drive...")
    service = get_drive_service()
    file_id = upload_file(service, enc_file, filename + ".enc")
    key_id = upload_file(service, enc_key, filename + ".key.enc")

    print("[4/4] Menyimpan manifest lokal...")
    manifest = load_manifest()
    manifest[filename] = {
        "file_id": file_id,
        "key_id": key_id,
        "original_hash": original_hash
    }
    save_manifest(manifest)

    print(f"\n✅ Selesai! '{filename}' berhasil dienkripsi & diupload.")
    print(f"   Drive file_id : {file_id}")
    print(f"   Drive key_id  : {key_id}")


def do_download(filename: str):
    manifest = load_manifest()
    if filename not in manifest:
        print(f"❌ '{filename}' tidak ditemukan di manifest lokal.")
        return

    entry = manifest[filename]
    priv = ensure_rsa_keys(PRIVATE_KEY_PATH, PUBLIC_KEY_PATH)[0]

    print("[1/3] Download ciphertext dari Google Drive...")
    service = get_drive_service()
    enc_file = download_file(service, entry["file_id"])
    enc_key = download_file(service, entry["key_id"])

    print("[2/3] Dekripsi RSA + AES...")
    decrypted_data = hybrid_decrypt_file(enc_key, enc_file, priv)

    print("[3/3] Verifikasi integritas...")
    current_hash = compute_sha256(decrypted_data)
    is_valid = current_hash == entry["original_hash"]

    output_path = os.path.join("data/output", filename)
    write_file_bytes(output_path, decrypted_data)

    print(f"\n{'✅' if is_valid else '❌'} Integritas file: {'TERJAGA' if is_valid else 'RUSAK/BERUBAH'}")
    print(f"   Hash asli     : {entry['original_hash']}")
    print(f"   Hash saat ini : {current_hash}")
    print(f"   Disimpan di   : {output_path}")


def main():
    print("=== Secure Cloud File Storage ===")
    print("1. Upload & Encrypt file")
    print("2. Download & Decrypt file")
    choice = input("Pilih menu (1/2): ").strip()

    if choice == "1":
        filepath = input("Path file yang mau diupload (contoh: data/input/test.txt): ").strip()
        if not os.path.exists(filepath):
            print("❌ File tidak ditemukan.")
            sys.exit(1)
        do_upload(filepath)

    elif choice == "2":
        filename = input("Nama file asli yang mau didownload (contoh: test.txt): ").strip()
        do_download(filename)

    else:
        print("❌ Pilihan tidak valid.")


if __name__ == "__main__":
    main()