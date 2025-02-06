from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from mysite.services.blog_service import save_blog_to_firebase, upload_image_to_firebase
from firebase_admin import firestore

from mysite.services.upload import upload_file_to_firebase
db = firestore.client()

class BlogView(APIView):

    def get(self, request, user_id=None, blog_id=None):
        if user_id and blog_id:
            # Fetch single blog by blog_id
            blog_ref = db.collection(f"users/{user_id}/blogs").document(blog_id)  
            blog = blog_ref.get()
            if not blog.exists:
                return Response({"error": "Blog not found!"}, status=status.HTTP_404_NOT_FOUND)
            return Response(blog.to_dict(), status=status.HTTP_200_OK)
        else:
            # Fetch all blogs
            blogs_ref = db.collection(f"users/{user_id}/blogs").stream()
            blogs = [blog.to_dict() for blog in blogs_ref]
            return Response(blogs, status=status.HTTP_200_OK)

    def post(self, request, user_id=None, blog_id=None):
        title = request.data.get("title")
        content = request.data.get("desc")
        image = request.FILES.get("image")
        
        if not user_id or not title or not content:
            return Response({"error": "User id, Title and content are required"}, status=400)

        # Create a new Firestore document under user's collection
        doc_ref = db.collection(f"users/{user_id}/blogs").document()  
        blog_id = doc_ref.id 

        image_url = None
        if image:
            image_url = upload_file_to_firebase(f"blogs/{user_id}/{blog_id}/thumbnail.jpg", image)  # Upload image
            
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

        return Response({"message": "Blog created successfully", "blog": blog_data}, status=201)

    def put(self, request, user_id, blog_id):
        if request.method == 'PUT':
            if not user_id:
                return Response({"error": "User id is required"}, status=400)
        
            blog_ref = db.collection(f"users/{user_id}/blogs").document(blog_id)  
            
            if(request.FILES.get("image")):
                image = request.FILES.get("image")
                image_url = upload_file_to_firebase(f"blogs/{user_id}/{blog_id}/thumbnail.jpg", image)  # Upload image
            
            # Check if blog exists
            blog = blog_ref.get()
            if not blog.exists:
                return Response({"error": "Blog not found!"}, status=status.HTTP_404_NOT_FOUND)
            
            # Update blog data
            data = request.data
            blog_ref.update({
                'title': data.get('title', blog.to_dict()['title']),
                'desc': data.get('desc', blog.to_dict()['desc']),
                'imgSrc': image_url,
                'updated_at': datetime.utcnow()
            })
            
            return Response({"message": "Blog updated successfully!"}, status=status.HTTP_200_OK)

    def delete(self, request,user_id, blog_id):
        if request.method == 'DELETE':
            blog_ref = db.collection(f"users/{user_id}/blogs").document(blog_id)  

            # Check if blog exists
            blog = blog_ref.get()
            if not blog.exists:
                return Response({"error": "Blog not found!"}, status=status.HTTP_404_NOT_FOUND)
            
            # Delete blog
            blog_ref.delete()
            
            return Response({"message": "Blog deleted successfully!"}, status=status.HTTP_200_OK)
          