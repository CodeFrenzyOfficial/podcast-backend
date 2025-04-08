from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
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
        try:
            data = request.data
            title = data.get("title")
            desc = data.get("desc")
            category = data.get("category")
            image_url = data.get("imgSrc")
            video_url = data.get("videoSrc")

            if not user_id or not title or not desc or not image_url or not video_url:
                return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

            podcast_id = db.collection("users").document(user_id).collection("podcasts").document().id  

            podcast_data = {
                "id": podcast_id,
                "title": title,
                "desc": desc,
                "category": category,
                "imgSrc": image_url,
                "videoSrc": video_url,
                "upload_date": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "file_size": data.get("file_size", 0),
                "duration": data.get("duration", 0),
                "status": "completed"
            }

            db.collection("users").document(user_id).collection("podcasts").document(podcast_id).set(podcast_data)

            return Response({"message": "Podcast created successfully", "podcast": podcast_data}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": f"Failed to create podcast: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, user_id, podcast_id):
        try:
            podcast_ref = db.collection("users").document(user_id).collection("podcasts").document(podcast_id)
            podcast = podcast_ref.get()
            if not podcast.exists:
                return Response({"error": "podcast not found!"}, status=status.HTTP_404_NOT_FOUND)

            data = request.data
            update_data = {
                "updated_at": datetime.utcnow()
            }

            for key in ["title", "desc", "category", "imgSrc", "videoSrc", "duration", "file_size"]:
                if data.get(key):
                    update_data[key] = data[key]

            podcast_ref.update(update_data)

            return Response({"message": "Podcast updated successfully", "updated": update_data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"Failed to update podcast: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, user_id, podcast_id):
        try:
            podcast_ref = db.collection("users").document(user_id).collection("podcasts").document(podcast_id)
            podcast = podcast_ref.get()
            if not podcast.exists:
                return Response({"error": "podcast not found!"}, status=status.HTTP_404_NOT_FOUND)

            podcast_ref.delete()

            return Response({"message": "podcast deleted successfully!"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"Failed to delete podcast: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
