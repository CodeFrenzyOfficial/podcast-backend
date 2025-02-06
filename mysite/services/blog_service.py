import firebase_admin
from firebase_admin import firestore, storage
import uuid
from datetime import datetime

# Initialize Firebase Firestore and Storage
db = firestore.client()
bucket = storage.bucket()

# Save blog post to Firestore
def save_blog_to_firebase(title, content, image_file=None):
    doc_ref = db.collection("blogs").document()  # Create new Firestore document
    blog_id = doc_ref.id  # Get generated ID

    image_url = None
    if image_file:
        image_url = upload_image_to_firebase(blog_id, image_file)  # Upload image
        
    # Get the current timestamp
    now = datetime.utcnow()

    blog_data = {
        "id": blog_id,
        "title": title,
        "desc": content,
        "imgSrc": image_url,
        "upload_date": now,  # Add the creation timestamp
        "updated_at": now,
    }
    doc_ref.set(blog_data)  # Save blog data to Firestore
    return blog_data

# Upload image to Firebase Storage
def upload_image_to_firebase(blog_id, image_file):
    file_extension = image_file.name.split(".")[-1]
    file_name = f"blogs/{blog_id}.{file_extension}"
    
    blob = bucket.blob(file_name)
    blob.upload_from_file(image_file)
    blob.make_public()  # Make URL accessible
    return blob.public_url  # Return the public URL

