from firebase_admin import auth
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import User

class FirebaseAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        id_token = auth_header.split(' ')[1]

        try:
            decoded_token = auth.verify_id_token(id_token)
        except Exception:
            raise AuthenticationFailed('Invalid Firebase ID token')

        uid = decoded_token.get('uid')
        
        if not uid:
            raise AuthenticationFailed('Invalid token payload')

        # Get or create a Django user based on Firebase UID
        user, _ = User.objects.get_or_create(username=uid)
        return (user, None)
