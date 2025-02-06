import firebase_admin
from firebase_admin import firestore, storage
import uuid
from datetime import datetime

# Initialize Firebase Firestore and Storage
db = firestore.client()
bucket = storage.bucket()


def upload_file_to_firebase(path, file):
    blob = bucket.blob(path)
    blob.upload_from_file(file, content_type=file.content_type)
    blob.make_public()
    return blob.public_url 