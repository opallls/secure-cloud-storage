"""
google_drive.py
Upload & download file ke/dari Google Drive menggunakan OAuth 2.0.
Scope: drive.file (least privilege - hanya akses file yang dibuat app ini)

Mendukung dua mode:
1. LOKAL  - login pertama kali via browser (InstalledAppFlow), token disimpan
            ke credentials/token.json untuk dipakai ulang.
2. CLOUD  - (Streamlit Cloud / server headless) tidak ada browser, jadi token
            diambil dari Streamlit secrets (st.secrets["google_oauth"]["token_json"]),
            hasil generate token.json secara lokal sebelumnya.
"""
import os
import io
import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
TOKEN_PATH = "credentials/token.json"
CREDENTIALS_PATH = "credentials/credentials.json"
DEFAULT_FOLDER_NAME = "database_keamanan"


def _load_creds_from_streamlit_secrets():
    """
    Coba ambil credentials dari Streamlit secrets.
    Return None jika Streamlit tidak tersedia atau secrets belum diset
    (misalnya saat dijalankan sebagai script biasa di lokal, bukan lewat `streamlit run`).
    """
    try:
        import streamlit as st
    except ImportError:
        return None

    try:
        token_info = json.loads(st.secrets["google_oauth"]["token_json"])
    except (KeyError, FileNotFoundError):
        return None

    # Buang field "expiry": beberapa versi google-auth menyimpan expiry dalam
    # format yang tidak konsisten (ada yang pakai "Z", ada yang pakai "+00:00"),
    # sehingga from_authorized_user_info bisa crash saat parsing. Tanpa field ini,
    # credentials dianggap belum ada info expiry, dan kita paksa refresh di bawah
    # agar selalu dapat token yang benar-benar valid.
    token_info.pop("expiry", None)

    return Credentials.from_authorized_user_info(token_info, SCOPES)


def _load_creds_from_local_file():
    """Coba ambil credentials dari file token.json lokal. Return None jika tidak ada."""
    if os.path.exists(TOKEN_PATH):
        return Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    return None


def _run_local_oauth_flow():
    """
    Jalankan flow OAuth interaktif via browser lokal.
    HANYA bisa berjalan di mesin yang punya browser (laptop/PC),
    TIDAK bisa dipanggil di server headless seperti Streamlit Cloud.
    """
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
    # access_type="offline" + prompt="consent" memastikan refresh_token ikut diberikan
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")

    os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
    with open(TOKEN_PATH, "w") as token_file:
        token_file.write(creds.to_json())

    return creds


def get_drive_service():
    """
    Autentikasi ke Google Drive API dengan urutan prioritas:
    1. Streamlit secrets (untuk deployment di Streamlit Cloud - tanpa browser)
    2. File token.json lokal (untuk development di laptop)
    3. Jalankan flow OAuth via browser (hanya jika token.json belum ada, lokal saja)
    """
    creds = _load_creds_from_streamlit_secrets()

    if creds is None:
        creds = _load_creds_from_local_file()

    if creds is None:
        # Tidak ada token sama sekali -> hanya boleh terjadi di lokal.
        creds = _run_local_oauth_flow()
    elif creds.refresh_token:
        # Selalu refresh secara proaktif alih-alih mengandalkan creds.valid,
        # karena field "expiry" yang tersimpan bisa tidak akurat/hilang.
        # Ini menghasilkan access token yang pasti valid tanpa risiko crash parsing.
        creds.refresh(Request())
        # Simpan token yang sudah di-refresh, tapi hanya jika sumbernya file lokal
        # (secrets Streamlit tidak bisa ditulis ulang dari kode).
        if os.path.exists(TOKEN_PATH):
            with open(TOKEN_PATH, "w") as token_file:
                token_file.write(creds.to_json())
    elif not creds.valid:
        creds = _run_local_oauth_flow()

    return build("drive", "v3", credentials=creds)


def get_or_create_folder(service, folder_name: str, parent_id: str = None) -> str:
    """
    Cari folder dengan nama `folder_name` yang sudah dibuat oleh app ini.
    Kalau belum ada, buat folder baru. Return folder_id.

    PENTING: dengan scope drive.file, app hanya bisa melihat/menggunakan folder
    yang DIBUAT SENDIRI lewat fungsi ini - folder yang dibuat manual di Drive
    (lewat browser) TIDAK akan terlihat oleh app, meskipun ID-nya diketahui.
    """
    query = (
        f"name = '{folder_name}' "
        "and mimeType = 'application/vnd.google-apps.folder' "
        "and trashed = false"
    )
    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = service.files().list(
        q=query,
        fields="files(id, name)",
        spaces="drive",
    ).execute()

    folders = results.get("files", [])
    if folders:
        return folders[0]["id"]

    # Folder belum ada -> buat baru
    file_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id:
        file_metadata["parents"] = [parent_id]

    folder = service.files().create(body=file_metadata, fields="id").execute()
    return folder.get("id")


def upload_file(service, data: bytes, filename: str, folder_id: str = None) -> str:
    """
    Upload bytes (ciphertext) ke Google Drive sebagai file.
    Return: file_id di Google Drive.
    """
    file_metadata = {"name": filename}
    if folder_id:
        file_metadata["parents"] = [folder_id]

    media = MediaIoBaseUpload(io.BytesIO(data), mimetype="application/octet-stream")
    uploaded = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()

    return uploaded.get("id")


def download_file(service, file_id: str) -> bytes:
    """
    Download file dari Google Drive berdasarkan file_id.
    Return: isi file sebagai bytes.
    """
    request = service.files().get_media(fileId=file_id)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()

    return buffer.getvalue()


def delete_file(service, file_id: str) -> None:
    """Hapus file dari Google Drive (opsional, untuk cleanup saat testing)."""
    service.files().delete(fileId=file_id).execute()
