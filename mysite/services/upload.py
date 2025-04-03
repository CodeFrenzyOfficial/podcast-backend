import firebase_admin
from firebase_admin import firestore, storage
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession
from datetime import datetime

# Load service account credentials with proper scopes
credentials = service_account.Credentials.from_service_account_file(
    "mysite/firebase-key.json",
    scopes=["https://www.googleapis.com/auth/devstorage.full_control"]
)

# Initialize Firebase Firestore and Storage
db = firestore.client()
bucket = storage.bucket()


def upload_file_to_firebase(path, file, chunk_size=10 * 1024 * 1024, upload_url=None):
    """
    Uploads a file to Firebase Storage using resumable, chunked upload.
    Supports retry/resume from last byte if an upload session is passed in.

    Args:
        path (str): Destination path in Firebase Storage.
        file (UploadedFile): Django's uploaded file object.
        chunk_size (int): Size of each chunk in bytes.
        upload_url (str): (Optional) Existing resumable session URL.

    Returns:
        str: Public URL of the uploaded file.
    """
    try:
        session = AuthorizedSession(credentials)
        file_size = file.size

        # If no resumable upload session exists, create one
        if not upload_url:
            metadata = {
                "name": path,
                "contentType": file.content_type,
            }

            upload_url = (
                f"https://storage.googleapis.com/upload/storage/v1/b/{bucket.name}/o?uploadType=resumable"
            )

            response = session.post(upload_url, json=metadata)
            if response.status_code != 200:
                raise Exception(f"Failed to create upload session: {response.text}")

            upload_url = response.headers["Location"]

        # Determine already uploaded bytes (resume logic)
        headers = {
            "Content-Range": f"bytes */{file_size}"
        }

        status_check = session.put(upload_url, headers=headers)
        uploaded = 0

        if status_check.status_code == 308:
            range_header = status_check.headers.get("Range")
            if range_header:
                uploaded = int(range_header.split("-")[1]) + 1
                file.seek(uploaded)

        # Start/resume uploading chunks
        while uploaded < file_size:
            start = uploaded
            end = min(start + chunk_size, file_size)
            current_chunk_size = end - start
            chunk_data = file.read(current_chunk_size)

            headers = {
                "Content-Range": f"bytes {start}-{end - 1}/{file_size}"
            }

            response = session.put(upload_url, data=chunk_data, headers=headers)

            if response.status_code not in (200, 201, 308):
                raise Exception(f"Chunk upload failed: {response.text}")

            uploaded = end

            if uploaded >= file_size and response.status_code in (200, 201):
                break

        # Finalize upload and make public
        blob = bucket.blob(path)
        blob.make_public()
        return blob.public_url

    except Exception as e:
        raise Exception(f"Upload failed: {str(e)}")
