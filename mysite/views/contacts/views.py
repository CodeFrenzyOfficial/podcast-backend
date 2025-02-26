from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from mysite.services.upload import upload_file_to_firebase
from firebase_admin import firestore
db = firestore.client()
      
class ContactsView(APIView):

    def get(self, request):
        try:
            admin_users = db.collection("users").where("role", "==", "admin").limit(1).stream()
            admin_user_doc = next(admin_users, None)

            if admin_user_doc:
                contacts_ref = admin_user_doc.reference.collection("contacts").stream()
                contacts = [contact.to_dict() for contact in contacts_ref]

                return Response(contacts, status=status.HTTP_200_OK)
            else:
                return Response({"message": "No admin users found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def post(self, request):
        try:
            name = request.data.get("name")
            email = request.data.get("email")
            phone = request.data.get("phone") 
            subject = request.data.get("subject")
            message = request.data.get("message")

            # Validate required fields
            if not name or not email or not phone or not subject:
                return Response({"error": "Name, Email, Subject, and Phone are required"}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch first admin user
            admin_users = db.collection("users").where("role", "==", "admin").limit(1).stream()
            admin_user_doc = next(admin_users, None)

            if not admin_user_doc:
                return Response({"error": "No admin user found"}, status=status.HTTP_404_NOT_FOUND)

            # Reference to admin's "contacts" subcollection
            contacts_ref = admin_user_doc.reference.collection("contacts")

            # Generate unique document ID
            new_contact_ref = contacts_ref.document()  
            contact_id = new_contact_ref.id

            # Contact data
            contact_data = {
                "id": contact_id,
                "name": name,
                "email": email,
                "phone": phone,
                "subject": subject,
                "message": message,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }

            # Save contact to Firestore
            new_contact_ref.set(contact_data)

            return Response({"message": "Message sent successfully", "contact": contact_data}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)