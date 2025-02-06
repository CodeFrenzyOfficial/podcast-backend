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
            poodcast_ref = db.collection(f"users/{user_id}/podcasts").document(podcast_id)  
            poodcast = poodcast_ref.get()
            if not poodcast.exists:
                return Response({"error": "podcast not found!"}, status=status.HTTP_404_NOT_FOUND)
            return Response(poodcast.to_dict(), status=status.HTTP_200_OK)
        else:
            # Fetch all podcasts
            poodcasts_ref = db.collection('podcasts').stream()
            podcasts = [poodcast.to_dict() for poodcast in poodcasts_ref]
            return Response(podcasts, status=status.HTTP_200_OK)

    def post(self, request, user_id=None, podcast_id=None):
        title = request.data.get("title")
        desc = request.data.get("desc")
        image = request.FILES.get("image")  # Thumbnail
        video = request.FILES.get("video")  # Video file

        if not title or not desc:
            return Response({"error": "Title and desc are required"}, status=status.HTTP_400_BAD_REQUEST)

        podcast_id = db.collection(f"users/{user_id}/podcasts").document().id  # Generate a unique ID

        # Upload image (thumbnail)
        image_url = None
        if image:
            image_url = upload_file_to_firebase(f"podcasts/thumbnail/{podcast_id}/thumbnail.jpg", image)

        # Upload video
        video_url = None
        if video:
            video_url = upload_file_to_firebase(f"podcasts/video/{podcast_id}/video.mp4", video)

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
        
        db.collection("podcasts").document(podcast_id).set(podcast_data)
        return Response({"message": "Podcast created successfully", "podcast": podcast_data}, status=status.HTTP_201_CREATED)


    def put(self, request, user_id, podcast_id):
        if request.method == 'PUT':
            poodcast_ref = db.collection(f"users/{user_id}/podcasts").document(podcast_id)  
            
            image = request.FILES.get("image")  # Thumbnail
            video = request.FILES.get("video")  # Video file

            # Upload image (thumbnail)
            image_url = None
            if image:
                image_url = upload_file_to_firebase(f"podcasts/thumbnail/{podcast_id}/thumbnail.jpg", image)

            # Upload video
            video_url = None
            if video:
                video_url = upload_file_to_firebase(f"podcasts/video/{podcast_id}/video.mp4", video)
            
            # Check if poodcast exists
            poodcast = poodcast_ref.get()
            if not poodcast.exists:
                return Response({"error": "poodcast not found!"}, status=status.HTTP_404_NOT_FOUND)
            
            # Update poodcast data
            data = request.data
            poodcast_ref.update({
                'title': data.get('title', poodcast.to_dict()['title']),
                'desc': data.get('desc', poodcast.to_dict()['desc']),
                'imgSrc': image_url,
                'videoSrc': video_url,
                'updated_at': datetime.utcnow()
            })
            
            return Response({"message": "poodcast updated successfully!"}, status=status.HTTP_200_OK)

    def delete(self, request, user_id, podcast_id):
        if request.method == 'DELETE':
            poodcast_ref = db.collection(f"users/{user_id}/podcasts").document(podcast_id)
            
            # Check if poodcast exists
            poodcast = poodcast_ref.get()
            if not poodcast.exists:
                return Response({"error": "poodcast not found!"}, status=status.HTTP_404_NOT_FOUND)
            
            # Delete poodcast
            poodcast_ref.delete()
            
            return Response({"message": "poodcast deleted successfully!"}, status=status.HTTP_200_OK)
        