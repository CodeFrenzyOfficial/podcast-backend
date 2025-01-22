from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from rest_framework import status
from firebase_admin import auth
from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny

class RegisterView(APIView):
    def post(self, request):
        # Retrieve form data
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

        # Register user in Firebase
        try:
            # Create Firebase user
            firebase_user = auth.create_user(
                email=email,
                password=password,
                phone_number=phone
            )
        except Exception as e:
            return Response({"error": f"Firebase registration failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        # Register user in Django
        try:
            django_user = User.objects.create_user(
                username=email,
                first_name=f_name,
                last_name=l_name,
                email=email,
                password=password
            )
            django_user.save()

            return Response({"message": "User registered successfully!"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": f"Django registration failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=404)

        if user:
            return Response({"message": f"Welcome, {user.email}!"}, status=200)
        else:
            return Response({"detail": "Invalid credentials."}, status=400)

