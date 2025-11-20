import firebase_admin
from firebase_admin import firestore, storage
from datetime import datetime
import re
import uuid
import traceback

db = firestore.client()
bucket = storage.bucket()


def generate_slug(title: str):
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def save_blog_to_firebase(title, content, thumbnail_file=None, content_files=None):
    """
    Save a blog to Firebase.
    - thumbnail_file: single Django File
    - content_files: list of Django Files
    """
    try:
        doc_ref = db.collection("blogs").document()
        blog_id = doc_ref.id
        slug = generate_slug(title)

        # Upload thumbnail
        thumbnail_url = None
        if thumbnail_file:
            thumbnail_url = upload_image_to_firebase(blog_id, "thumbnail", thumbnail_file)

        # Upload content images
        content_urls = []
        if content_files:
            for idx, file in enumerate(content_files):
                url = upload_image_to_firebase(blog_id, f"content_{idx}", file)
                content_urls.append(url)

        now = firestore.SERVER_TIMESTAMP

        blog_data = {
            "id": blog_id,
            "slug": slug,
            "title": title,
            "desc": content,
            "thumbnail": thumbnail_url,
            "imgSrc": content_urls,
            "upload_date": now,
            "updated_at": now,
        }

        doc_ref.set(blog_data)
        return blog_data

    except Exception as e:
        print("\n🔥 ERROR IN save_blog_to_firebase 🔥")
        print(traceback.format_exc())
        raise e


def upload_image_to_firebase(blog_id: str, name_prefix: str, image_file):
    """Upload single file to Firebase Storage safely"""
    try:
        file_extension = image_file.name.split(".")[-1]

        # unique file name
        file_name = f"blogs/{blog_id}/{name_prefix}_{uuid.uuid4()}.{file_extension}"
        blob = bucket.blob(file_name)

        # Reset pointer before sending
        image_file.file.seek(0)

        blob.upload_from_file(
            image_file.file,
            content_type=image_file.content_type,
            rewind=True,   # prevent pointer issues
        )

        blob.make_public()
        return blob.public_url

    except Exception as e:
        print("\n🔥 ERROR IN upload_image_to_firebase 🔥")
        print("File:", image_file.name)
        print(traceback.format_exc())
        raise e
