from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from mysite.services.upload import upload_file_to_firebase
from firebase_admin import firestore
db = firestore.client()
      
class UsersView(APIView):

    def get(self, request, user_id=None):
        if user_id:
            user_ref = db.collection('users').document(user_id)
            user = user_ref.get()
            if not user.exists:
                return Response({"error": "user not found!"}, status=status.HTTP_404_NOT_FOUND)
            return Response(user.to_dict(), status=status.HTTP_200_OK)
        else:
            # Fetch all podcasts
            poodcasts_ref = db.collection('users').stream()
            podcasts = [user.to_dict() for user in poodcasts_ref]
            return Response(podcasts, status=status.HTTP_200_OK)

    def put(self, request, user_id):
        if request.method == 'PUT':
            user_ref = db.collection('users').document(user_id)
            
            # Check if user exists
            user = user_ref.get()
            if not user.exists:
                return Response({"error": "user not found!"}, status=status.HTTP_404_NOT_FOUND)
            
            # Update user data
            data = request.data
            user_ref.update({
                'f_name': data.get('f_name', user.to_dict()['f_name']),
                'l_name': data.get('l_name', user.to_dict()['l_name']),
                'phone': data.get('phone', user.to_dict()['phone']),
                'updated_at': datetime.utcnow()
            })
            
            return Response({"message": "user updated successfully!"}, status=status.HTTP_200_OK)