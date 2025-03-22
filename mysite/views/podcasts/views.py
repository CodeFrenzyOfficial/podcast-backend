from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from mysite.services.upload import upload_file_to_firebase
from firebase_admin import firestore
from rest_framework.pagination import PageNumberPagination

db = firestore.client()
      
class PodcastView(APIView):

    def get(self, request, user_id=None, podcast_id=None, category=None):
        if user_id and podcast_id:
            podcast_ref = db.collection("users").document(user_id).collection("podcasts").document(podcast_id)  
            podcast = podcast_ref.get()
            if not podcast.exists:
                return Response({"error": "podcast not found!"}, status=status.HTTP_404_NOT_FOUND)
            return Response(podcast.to_dict(), status=status.HTTP_200_OK)
        
        elif user_id:
            podcasts_ref = db.collection("users").document(user_id).collection("podcasts").stream()
            podcasts = [podcast.to_dict() for podcast in podcasts_ref]
            return Response(podcasts, status=status.HTTP_200_OK)
        
        elif category:
            users_ref = db.collection("users").stream()
            all_podcasts = []

            for user in users_ref:
                user_id = user.id

                podcasts_ref = db.collection("users").document(user_id).collection("podcasts")

                if category == 'dj':
                    podcasts_query = podcasts_ref.where("category", "==", category).stream()
                else:
                    podcasts_query = podcasts_ref.stream()

                user_podcasts = [{"user_id": user_id, **podcast.to_dict()} for podcast in podcasts_query]
                all_podcasts.extend(user_podcasts)

            order = request.GET.get("order", "desc")
            reverse_order = order == "asc"

            all_podcasts.sort(key=lambda x: x.get("upload_date", ""), reverse=reverse_order)

            paginator = PageNumberPagination()
            paginator.page_size = 3
            result_page = paginator.paginate_queryset(all_podcasts, request)

            return paginator.get_paginated_response({"podcasts": result_page, "category": category})
        
        else:
            users_ref = db.collection("users").stream()
            all_podcasts = []

            for user in users_ref:
                user_id = user.id 
                podcasts_ref = db.collection("users").document(user_id).collection("podcasts").stream()
                user_podcasts = [{"user_id": user_id, **podcast.to_dict()} for podcast in podcasts_ref] 
                all_podcasts.extend(user_podcasts)

            return Response(all_podcasts, status=status.HTTP_200_OK)

    def post(self, request, user_id, podcast_id=None):
        title = request.data.get("title")
        desc = request.data.get("desc")
        category = request.data.get("category")
        image = request.FILES.get("image") 
        video = request.FILES.get("video")  

        if not user_id or not title or not desc:
            return Response({"error": "User id, Title and desc are required"}, status=status.HTTP_400_BAD_REQUEST)

        podcast_id = db.collection("users").document(user_id).collection("podcasts").document().id  

        image_url = None
        if image:
            image_url = upload_file_to_firebase(f"podcasts/{user_id}/thumbnail/{podcast_id}/thumbnail.jpg", image)

        video_url = None
        if video:
            video_url = upload_file_to_firebase(f"podcasts/{user_id}/video/{podcast_id}/video.mp4", video)

        podcast_data = {
            "id": podcast_id,
            "title": title,
            "desc": desc,
            "category": category,
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
                'category': data.get('desc', podcast.to_dict()['category']),
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
        