from django.template.response import TemplateResponse
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from transbackend.serializers import serializers
from .permissions import IsAnonymousUser
from transbackend.services.user_service import UserService
from transbackend.utils.response_utils import json_response
from transbackend.serializers import UserRegistrationSerializer, UserSerializer, LoginSerializer
import json
from rest_framework.permissions import IsAuthenticated
from django.utils.translation import gettext as _

class RegisterView(APIView):
    permission_classes = [IsAnonymousUser]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        return TemplateResponse(request, 'register.html')

    def post(self, request):
        try:
            serializer = UserRegistrationSerializer(data=request.data)
            if not serializer.is_valid():
                return json_response(error=serializer.errors, status=400)

            user = UserService.create_or_update_unverified_user(
                username=serializer.validated_data['username'],
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )
            UserService.handle_verification_email(user)
            return json_response(message=_("Registration successful! A verification code has been sent to your email."))
            
        except Exception as e:
            return json_response(error=str(e), status=500)

class LoginView(APIView):
    permission_classes = [IsAnonymousUser]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        return TemplateResponse(request, 'login.html')

    def post(self, request):
        try:
            serializer = LoginSerializer(data=request.data)
            if not serializer.is_valid():
                return json_response(error=serializer.errors, status=401)

            user = serializer.validated_data['user']
            
            if not user.is_verified:
                user.set_verification_code()
                UserService.handle_verification_email(user)
                return json_response(
                    message=_("Your account is not verified. A verification code has been sent to your email.")
                )

            user.set_verification_code()
            UserService.handle_verification_email(user)
            return json_response(message=_("Verification code sent to your email."))

        except serializers.ValidationError as ve:
            error_message = str(ve.detail[0]) if isinstance(ve.detail, list) else str(ve.detail)
            return json_response(error=error_message, status=401)
        except Exception as e:
            return json_response(error=_("An unexpected error occurred."), status=500)

class ResetPasswordView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        return TemplateResponse(request, 'reset-password.html')

    def post(self, request):
        try:
            data = request.data
            old_password = data.get('old_password')
            new_password = data.get('new_password')

            if old_password is None:
                return json_response(error={"old_password": _("This field is required.")}, status=400)
            if new_password is None:
                return json_response(error={"new_password": _("This field is required.")}, status=400)

            user = request.user

            if not user.check_password(old_password):
                return json_response(error=_("Current password is incorrect"), status=400)

            user.set_password(new_password)
            user.save()

            return json_response(message=_("Password updated successfully"))

        except json.JSONDecodeError:
            return json_response(error=_("Invalid JSON format"), status=400)
        except Exception as e:
            return json_response(error=_("An error occurred while resetting password"), status=500)
