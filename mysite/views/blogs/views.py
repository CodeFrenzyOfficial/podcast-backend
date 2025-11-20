import re
import traceback
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from firebase_admin import firestore

from mysite.services.blog_service import save_blog_to_firebase, upload_image_to_firebase

db = firestore.client()


def generate_slug(title: str) -> str:
    """Generate SEO-friendly slug from title"""
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


class BlogView(APIView):

    def get(self, request, user_id=None, blog_id=None):
            try:
                # 🔥 Fetch single blog
                if user_id and blog_id:
                    blog_ref = db.collection("users").document(user_id).collection("blogs").document(blog_id).get()
                    if not blog_ref.exists:
                        return Response({"error": "Blog not found"}, status=status.HTTP_404_NOT_FOUND)

                    return Response(blog_ref.to_dict(), status=status.HTTP_200_OK)

                # 🔥 Fetch all blogs for a single user
                if user_id:
                    blogs_ref = (
                        db.collection("users")
                        .document(user_id)
                        .collection("blogs")
                        .order_by("upload_date", direction=firestore.Query.DESCENDING)
                        .get()
                    )
                    blogs = [b.to_dict() for b in blogs_ref]
                    return Response(blogs, status=status.HTTP_200_OK)

                # 🔥 Fetch ALL blogs from ALL users
                all_blogs = []
                users = db.collection("users").get()

                print(f"🔍 Total users found: {len(list(users))}")
                
                # Need to get users again since we consumed the iterator
                users = db.collection("users").get()
                for user in users:
                    uid = user.id
                    print(f"🔍 Fetching blogs for user: {uid}")
                    
                    blogs_ref = (
                        db.collection("users")
                        .document(uid)
                        .collection("blogs")
                        .order_by("upload_date", direction=firestore.Query.DESCENDING)
                        .get()
                    )
                    
                    user_blogs = [b.to_dict() for b in blogs_ref]
                    print(f"🔍 Found {len(user_blogs)} blogs for user {uid}")
                    
                    all_blogs.extend(user_blogs)

                print(f"🔍 Total blogs collected from all users: {len(all_blogs)}")
                
                # Sort by upload time
                all_blogs.sort(key=lambda x: x.get("upload_date", datetime.min), reverse=True)
                return Response(all_blogs, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def post(self, request, user_id=None, blog_id=None):
        """Create or update a blog with thumbnail + content images"""
        print("\n===== BLOG POST REQUEST RECEIVED =====")
        print(f"🔥 URL Parameter user_id: {user_id}")
        print(f"🔥 URL Parameter blog_id: {blog_id}")
        print("Request Data:", dict(request.data))
        print("Files:", request.FILES)

        try:
            if not user_id:
                print("❌ ERROR: Missing user_id")
                return Response({"error": "User ID is required"}, status=status.HTTP_400_BAD_REQUEST)

            title = request.data.get("title")
            desc = request.data.get("desc")

            if not title or not desc:
                print("ERROR: Title or description missing")
                return Response({"error": "Title and description required"}, status=status.HTTP_400_BAD_REQUEST)

            thumbnail_file = request.FILES.get("thumbnail")
            content_files = request.FILES.getlist("content_files")

            print("Thumbnail File:", thumbnail_file)
            print("Content Files Count:", len(content_files))

            slug = generate_slug(title)

            # ----------------------------------
            # UPDATE OPERATION
            # ----------------------------------
            if blog_id:
                print(f"Updating blog: {blog_id}")

                blog_ref = (
                    db.collection("users")
                    .document(user_id)
                    .collection("blogs")
                    .document(blog_id)
                )
                blog_doc = blog_ref.get()

                if not blog_doc.exists:
                    print("ERROR: Blog not found in Firestore")
                    return Response({"error": "Blog not found"}, status=status.HTTP_404_NOT_FOUND)

                existing = blog_doc.to_dict()

                # Upload new thumbnail
                thumbnail_url = existing.get("thumbnail")
                if thumbnail_file:
                    print("Uploading new thumbnail...")
                    thumbnail_url = upload_image_to_firebase(blog_id, "thumbnail", thumbnail_file)
                    print("Thumbnail Upload URL:", thumbnail_url)

                # Upload new content images
                imgSrc = existing.get("imgSrc", [])
                if content_files:
                    print("Uploading new content images...")
                    imgSrc = [
                        upload_image_to_firebase(blog_id, f"content_{i}", f)
                        for i, f in enumerate(content_files)
                    ]
                    print("Content Image URLs:", imgSrc)

                blog_ref.update({
                    "title": title,
                    "desc": desc,
                    "slug": slug,
                    "thumbnail": thumbnail_url,
                    "imgSrc": imgSrc,
                    "updated_at": firestore.SERVER_TIMESTAMP
                })

                print("Blog updated successfully")
                return Response({"message": "Blog updated successfully"}, status=status.HTTP_200_OK)

            # ----------------------------------
            # CREATE OPERATION
            # ----------------------------------
            print("Creating a NEW blog...")
            print(f"🔥 USER_ID RECEIVED: {user_id}")
            print(f"🔥 SAVING TO PATH: /users/{user_id}/blogs/")

            doc_ref = db.collection("users").document(user_id).collection("blogs").document()
            new_blog_id = doc_ref.id
            print(f"🔥 New Blog ID: {new_blog_id}")
            print(f"🔥 Full Firestore Path: /users/{user_id}/blogs/{new_blog_id}")

            # Upload thumbnail
            thumbnail_url = None
            if thumbnail_file:
                print("Uploading thumbnail...")
                thumbnail_url = upload_image_to_firebase(new_blog_id, "thumbnail", thumbnail_file)
                print("Thumbnail URL:", thumbnail_url)

            # Upload content images
            imgSrc = []
            if content_files:
                print("Uploading content images...")
                imgSrc = [
                    upload_image_to_firebase(new_blog_id, f"content_{i}", f)
                    for i, f in enumerate(content_files)
                ]
                print("Uploaded Content Images:", imgSrc)

            blog_data = {
                "id": new_blog_id,
                "title": title,
                "slug": slug,
                "desc": desc,
                "thumbnail": thumbnail_url,
                "imgSrc": imgSrc,
                "upload_date": firestore.SERVER_TIMESTAMP,
                "updated_at": firestore.SERVER_TIMESTAMP,
            }

            print("🔥 Saving blog to Firestore...")
            doc_ref.set(blog_data)
            print("🔥 Blog saved successfully to Firestore!")

            # Fetch the document to get the actual timestamps
            saved_blog_doc = doc_ref.get()
            print(f"🔥 Document exists after save: {saved_blog_doc.exists}")
            
            saved_blog = saved_blog_doc.to_dict()
            print(f"🔥 Saved blog data: {saved_blog}")

            return Response({"message": "Blog created successfully", "blog": saved_blog}, status=status.HTTP_201_CREATED)

        except Exception as e:
            error_trace = traceback.format_exc()
            print("\n===== BACKEND ERROR =====")
            print(error_trace)

            return Response({"error": str(e), "trace": error_trace}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, user_id, blog_id):
        try:
            blog_ref = db.collection("users").document(user_id).collection("blogs").document(blog_id)
            blog_doc = blog_ref.get()
            if not blog_doc.exists:
                return Response({"error": "Blog not found"}, status=status.HTTP_404_NOT_FOUND)
            blog_ref.delete()
            return Response({"message": "Blog deleted successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
