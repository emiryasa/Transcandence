from django.contrib.auth import authenticate, login as auth_login
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.urls import reverse
from django.contrib.auth.forms import SetPasswordForm
from django.shortcuts import render
from django.http import JsonResponse
from .models import User


def request_password_reset(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_link = request.build_absolute_uri(
                reverse('reset_password', kwargs={'uidb64': uid, 'token': token})
            )
            send_mail(
                "Password Reset Requested",
                f"To reset your password, click the link: {reset_link}",
                'from@example.com',  # email lazım
                [email],
            )
            return JsonResponse({"message": "Password reset email sent!"}, status=200)
        except User.DoesNotExist:
            return JsonResponse({"error": "Email not found."}, status=404)

    return JsonResponse({"error": "Invalid request method."}, status=405)


def reset_password(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            if new_password:
                user.set_password(new_password)
                user.save()
                return JsonResponse({"message": "Password has been reset!"}, status=200)
            else:
                return JsonResponse({"error": "New password is required."}, status=400)

    return JsonResponse({"error": "Invalid token or user."}, status=400)


def hello_world(request):
    return HttpResponse("Hello, World!")


def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        profile_picture = request.FILES.get('profile_picture')

        if username and email and password:
            if User.objects.filter(username=username).exists():
                return JsonResponse({"error": "Username already taken."}, status=400)
            if User.objects.filter(email=email).exists():
                return JsonResponse({"error": "Email already in use."}, status=400)
            user = User(username=username, email=email, profile_picture=profile_picture)
            user.set_password(password)
            user.save()

            return JsonResponse({"message": "Registration successful!"}, status=201)
        else:
            return JsonResponse({"error": "All fields are required."}, status=400)

    return JsonResponse({"error": "Invalid request method."}, status=405)


def login(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            return JsonResponse({"message": "Already logged in."}, status=200)

        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return JsonResponse({"message": "Login successful!"}, status=200)
        else:
            return JsonResponse({"error": "Invalid username or password."}, status=401)

    return JsonResponse({"error": "Invalid request method."}, status=405)

def upload_profile_picture(request):
    if request.method == 'POST':
        user_id = request.POST.get('userId')
        try:
            user = User.objects.get(pk=user_id)
            if 'profile_picture' in request.FILES:
                profile_picture = request.FILES['profile_picture']
                user.profile_picture.save(profile_picture.name, profile_picture)
                user.save()
                return JsonResponse({"message": "Profile picture updated!"}, status=200)
            else:
                return JsonResponse({"error": "No picture uploaded."}, status=400)
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found."}, status=404)

    return JsonResponse({"error": "Invalid request method."}, status=405)