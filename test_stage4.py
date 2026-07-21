from google_drive import get_drive_service, upload_file, download_file

service = get_drive_service()

# Upload data uji sederhana
test_data = b"Test upload ke Google Drive dari Secure Cloud Storage app"
file_id = upload_file(service, test_data, "test_upload.enc")
print("File berhasil diupload, ID:", file_id)

# Download kembali
downloaded_data = download_file(service, file_id)
print("Isi file setelah download:", downloaded_data)
print("Data sama dengan yang diupload?", downloaded_data == test_data)