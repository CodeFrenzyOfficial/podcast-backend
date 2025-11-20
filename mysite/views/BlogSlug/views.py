from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from firebase_admin import firestore

db = firestore.client()

class BlogSlugView(APIView):
    def get(self, request, slug):
        try:
            slug = slug.strip().lower()  # normalize
            users = db.collection("users").stream()
            for user in users:
                blogs_ref = db.collection("users").document(user.id).collection("blogs").stream()
                for b in blogs_ref:
                    blog_data = b.to_dict()
                    if blog_data.get("slug", "").lower() == slug:
                        blog_data["user_id"] = user.id
                        return Response(blog_data, status=200)

            return Response({"error": "Blog not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
