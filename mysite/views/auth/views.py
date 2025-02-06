from datetime import datetime
import firebase_admin
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from firebase_admin import auth, firestore
from rest_framework.permissions import AllowAny
from rest_framework import serializers

db = firestore.client()

class RegisterView(APIView):
    def post(self, request):
        f_name = request.data.get("f_name")
        l_name = request.data.get("l_name")
        email = request.data.get("email")
        phone = request.data.get("phone")
        role = request.data.get("role")
        password = request.data.get("password")
        password_confirmation = request.data.get("passwordConfirmation")

        # Check if passwords match
        if password != password_confirmation:
            return Response({"error": "Passwords do not match!"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Create Firebase Authentication User
            user = auth.create_user(
                email=email,
                password=password,
                phone_number=phone
            )
            
            token =  auth.create_custom_token(user.uid).decode()

            # Save additional user details in Firestore
            user_data = {
                "uid": user.uid,
                "f_name": f_name,
                "l_name": l_name,
                "email": email,
                "phone": phone,
                "role": role,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            db.collection("users").document(user.uid).set(user_data)

            return Response({"message": "User registered successfully!", "user": user_data, "token": token}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": f"Firebase registration failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({"detail": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Try signing in user with Firebase
            user = auth.get_user_by_email(email)
            user_ref = db.collection("users").document(format(user.uid))
            user_doc = user_ref.get()

            if not user_doc.exists:
                return Response({"detail": "User not found in Firestore."}, status=status.HTTP_404_NOT_FOUND)

            # Get the user data from Firestore
            user_data = user_doc.to_dict()
            token = auth.create_custom_token(format(user.uid)).decode()
            
            return Response({
                "message": f"Welcome!",
                "user": user_data,
                "token": token,
            }, status=status.HTTP_200_OK)

        except firebase_admin.auth.UserNotFoundError:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
class LogoutView(APIView):
    def post(self, request):
        user_id = request.data.get("user_id")
        
        if not user_id:
            return Response({"error": "User ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            auth.revoke_refresh_tokens(user_id) # Revoke the refresh token
            return Response({"message": "User logged out successfully!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)