from django.contrib.auth import authenticate, login as auth_login
from django.http import JsonResponse, HttpResponse
from django.core.mail import send_mail
from .models import User
from rest_framework_simplejwt.tokens import RefreshToken
import json
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, BasePermission, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.template.response import TemplateResponse
from django.contrib.auth import get_user_model
from django.contrib.auth import logout as auth_logout
import random
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
class IsAnonymousUser(BasePermission):
    """
    This permission class allows access only to anonymous users.
    """
    def has_permission(self, request, view):
        print(request.user)
        return not request.user.is_authenticated

class HeaderView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        user = request.user
        return TemplateResponse(request, 'header.html', {"user": user})
    
class RegisterView(APIView):
    permission_classes = [IsAnonymousUser]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        return TemplateResponse(request, 'register.html')

    def post(self, request):
        try:
            data = json.loads(request.body)
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')

            if username and email and password:
                if User.objects.filter(username=username).exists():
                    return JsonResponse({"error": "Username already taken."}, status=400)
                if User.objects.filter(email=email).exists():
                    return JsonResponse({"error": "Email already in use."}, status=400)

                user = User(username=username, email=email)
                user.set_password(password)
                user.save()
                return JsonResponse({"message": "Registration successful!"}, status=201)
            else:
                return JsonResponse({"error": "All fields are required."}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data."}, status=400)

class HomeView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user
        return TemplateResponse(request, 'home.html', {"user": user})

class LoginView(APIView):
    permission_classes = [IsAnonymousUser]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        return TemplateResponse(request, 'login.html')

    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            User = get_user_model()

            try:
                user = User.objects.get(email=email)
                if user.check_password(password):
                    refresh = RefreshToken.for_user(user)
                    return JsonResponse({
                        "message": "Login successful!",
                        "access": str(refresh.access_token),
                        "refresh": str(refresh),
                    }, status=200)
                else:
                    return JsonResponse({"error": "Invalid email or password."}, status=401)
            except User.DoesNotExist:
                return JsonResponse({"error": "Invalid email or password."}, status=401)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data."}, status=400)

class GameView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user
        return TemplateResponse(request, 'game.html', {"user": user})

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user
        return TemplateResponse(request, 'profile.html', {"user": user})

    def post(self, request):
        try:
            data = request.data
            user = request.user
            if data.get('username'):
                user.username = data.get('username')
            if data.get('email'):
                user.email = data.get('email')
            if data.get('profile_picture'):
                user.profile_picture = data.get('profile_picture')
            if data.get('password'):
                user.password = data.get('password')
            user.save()
            return JsonResponse({"message": "Profile updated successfully!"}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data."}, status=400)
        
class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return TemplateResponse(request, 'new-password.html', {"user": request.user})

    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get('email')
            user = User.objects.filter(email=email).first()

            if user:
                user.set_verification_code()

                send_mail(
                    'Password Reset Code',
                    f'Your password reset code is {user.verification_code}. It expires in 3 minutes.',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )

                return JsonResponse({"message": "Verification code sent to email."}, status=200)
            else:
                return JsonResponse({"error": "User with this email does not exist."}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data."}, status=400)

class VerifyCodeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get('email')
            verification_code = data.get('verify_code')
            user = User.objects.filter(email=email).first()

            if user and user.verification_code == int(verification_code):
                if timezone.now() > user.code_expiration:
                    return JsonResponse({"error": "Verification code has expired."}, status=400)

                user.verification_code = None
                user.code_expiration = None
                user.save()

                return JsonResponse({"message": "Password reset successful!"}, status=200)
            else:
                return JsonResponse({"error": "Invalid verification code or email."}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data."}, status=400)

class ChangePasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get('email')
            new_password = data.get('new_password')

            user = User.objects.filter(email=email).first()
            if user:
                user.set_password(new_password)
                user.save()
            else:
                return JsonResponse({"error": "User with this email does not exist."}, status=400)
            return JsonResponse({"message": "Password changed successfully!"}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data."}, status=400)