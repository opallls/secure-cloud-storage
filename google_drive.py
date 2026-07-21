"""
google_drive.py
Upload & download file ke/dari Google Drive menggunakan OAuth 2.0.
Scope: drive.file (least privilege - hanya akses file yang dibuat app ini)
"""
import os
import io
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
TOKEN_PATH = "credentials/token.json"
CREDENTIALS_PATH = "credentials/credentials.json"


def get_drive_service():
    """
    Autentikasi ke Google Drive API.
    Membuka browser untuk login pertama kali, lalu simpan token untuk dipakai ulang.
    """
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


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