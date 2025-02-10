from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from mysite.services.upload import upload_file_to_firebase
from firebase_admin import firestore
db = firestore.client()
      
class PodcastView(APIView):

    def get(self, request, user_id=None, podcast_id=None):
        if user_id and podcast_id:
            podcast_ref = db.collection("users").document(user_id).collection("podcasts").document(podcast_id)  
            podcast = podcast_ref.get()
            if not podcast.exists:
                return Response({"error": "podcast not found!"}, status=status.HTTP_404_NOT_FOUND)
            return Response(podcast.to_dict(), status=status.HTTP_200_OK)
        
        elif user_id:
            # Fetch all podcasts
            podcasts_ref = db.collection("users").document(user_id).collection("podcasts").stream()
            podcasts = [podcast.to_dict() for podcast in podcasts_ref]
            return Response(podcasts, status=status.HTTP_200_OK)
        
        else:
            # Fetch all blogs across all users
            users_ref = db.collection("users").stream()
            all_podcasts = []

            for user in users_ref:
                user_id = user.id  # Get user document ID
                podcasts_ref = db.collection("users").document(user_id).collection("podcasts").stream()
                user_podcasts = [{"user_id": user_id, **podcast.to_dict()} for podcast in podcasts_ref]  # Add user_id for reference
                all_podcasts.extend(user_podcasts)

            return Response(all_podcasts, status=status.HTTP_200_OK)

    def post(self, request, user_id, podcast_id=None):
        title = request.data.get("title")
        desc = request.data.get("desc")
        image = request.FILES.get("image")  # Thumbnail
        video = request.FILES.get("video")  # Video file

        if not user_id or not title or not desc:
            return Response({"error": "User id, Title and desc are required"}, status=status.HTTP_400_BAD_REQUEST)

        podcast_id = db.collection("users").document(user_id).collection("podcasts").document().id  # Generate a unique ID

        # Upload image (thumbnail)
        image_url = None
        if image:
            image_url = upload_file_to_firebase(f"podcasts/{user_id}/thumbnail/{podcast_id}/thumbnail.jpg", image)

        # Upload video
        video_url = None
        if video:
            video_url = upload_file_to_firebase(f"podcasts/{user_id}/video/{podcast_id}/video.mp4", video)

        # Save podcast to Firestore
        podcast_data = {
            "id": podcast_id,
            "title": title,
            "desc": desc,
            "imgSrc": image_url,
            "videoSrc": video_url,
            "upload_date": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        db.collection("users").document(user_id).collection("podcasts").document(podcast_id).set(podcast_data)
        return Response({"message": "Podcast created successfully", "podcast": podcast_data}, status=status.HTTP_201_CREATED)


    def put(self, request, user_id, podcast_id):
        if request.method == 'PUT':
            podcast_ref = db.collection("users").document(user_id).collection("podcasts").document(podcast_id)  
            
            image = request.FILES.get("image")  # Thumbnail
            video = request.FILES.get("video")  # Video file
            
            # Check if podcast exists
            podcast = podcast_ref.get()
            if not podcast.exists:
                return Response({"error": "podcast not found!"}, status=status.HTTP_404_NOT_FOUND)

            # Upload image (thumbnail)
            image_url = None
            if image:
                image_url = upload_file_to_firebase(f"podcasts/{user_id}/thumbnail/{podcast_id}/thumbnail.jpg", image)
                podcast_ref.update({
                    'imgSrc': image_url,
                })

            # Upload video
            video_url = None
            if video:
                video_url = upload_file_to_firebase(f"podcasts/{user_id}/video/{podcast_id}/video.mp4", video)
                podcast_ref.update({
                    'videoSrc': video_url,
                })
            
            # Update podcast data
            data = request.data
            podcast_ref.update({
                'title': data.get('title', podcast.to_dict()['title']),
                'desc': data.get('desc', podcast.to_dict()['desc']),
                'updated_at': datetime.utcnow()
            })
            
            return Response({"message": "podcast updated successfully!"}, status=status.HTTP_200_OK)

    def delete(self, request, user_id, podcast_id):
        if request.method == 'DELETE':
            podcast_ref = db.collection("users").document(user_id).collection("podcasts").document(podcast_id)
            
            # Check if podcast exists
            podcast = podcast_ref.get()
            if not podcast.exists:
                return Response({"error": "podcast not found!"}, status=status.HTTP_404_NOT_FOUND)
            
            # Delete podcast
            podcast_ref.delete()
            
            return Response({"message": "podcast deleted successfully!"}, status=status.HTTP_200_OK)
        