from rest_framework.views import APIView
from django.template.response import TemplateResponse
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.http import JsonResponse
from django.core.mail import send_mail, BadHeaderError
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
import json
from transbackend.models import User
from .permissions import IsAnonymousUser
from rest_framework_simplejwt.tokens import RefreshToken

class VerifyLoginView(APIView):
    permission_classes = [IsAnonymousUser]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        return TemplateResponse(request, '2fa.html')

    def post(self, request):
        try:
            data = json.loads(request.body)
            username = data.get('username')
            verification_code = data.get('verification_code')

            try:
                user = User.objects.get(username=username)
                print(now())
                if verification_code is None:
                    return JsonResponse({"error": "Verification code is required."}, status=400)
                try:
                    verification_code = int(verification_code)
                except ValueError:
                    return JsonResponse({"error": "Invalid verification code format."}, status=400)

                if user.verification_code != verification_code:
                    return JsonResponse({"error": "Invalid verification code."}, status=400)

                if user.code_expiration <= now():
                    return JsonResponse({"error": "Verification code has expired."}, status=400)

                if not user.is_verified:
                    user.is_verified = True

                user.verification_code = None
                user.code_expiration = None
                user.save()

                refresh = RefreshToken.for_user(user)
                return JsonResponse({
                    "message": "Login successful!",
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                }, status=200)

            except User.DoesNotExist:
                return JsonResponse({"error": "User not found."}, status=404)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data."}, status=400)

class HeaderView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        user = request.user
        return TemplateResponse(request, 'header.html', {"user": user})

class HomeView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user
        return TemplateResponse(request, 'home.html', {"user": user})

class GameView(APIView):
    permission_classes = [AllowAny]
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

            user.save()
            return JsonResponse({"message": "Profile updated successfully!"}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data."}, status=400)

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return TemplateResponse(request, 'reset-password.html', {"user": request.user})

    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get('email')
            user = User.objects.filter(email=email).first()

            if user:
                user.set_verification_code()

                try:
                    send_mail(
                        'Password Reset Code',
                        f'Your password reset code is {user.verification_code}. It expires in 3 minutes.',
                        [email],
                        fail_silently=False,
                    )
                    return JsonResponse({"message": "Verification code sent to email."}, status=200)
    
                except BadHeaderError:
                    return JsonResponse({"error": "Failed to send email invalid email."}, status=500)
                
                except Exception as e:
                    return JsonResponse({"error": f"Failed to send email: {str(e)}"}, status=500)

            else:
                return JsonResponse({"error": "User with this email does not exist."}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data."}, status=400)

class VerifyAccountView(APIView):
    permission_classes = [IsAnonymousUser]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        return TemplateResponse(request, 'verify.html')

    def post(self, request):
        try:
            data = json.loads(request.body)
            username = data.get('username')
            verification_code = data.get('verification_code')

            try:
                user = User.objects.get(username=username)

                if user.verification_code is None or verification_code is None:
                    return JsonResponse({"error": "Verification code is missing."}, status=400)

                try:
                    verification_code = int(verification_code)
                except ValueError:
                    return JsonResponse({"error": "Invalid verification code format."}, status=400)

                if user.verification_code == verification_code and user.code_expiration > now():
                    user.is_verified = True
                    user.verification_code = None
                    user.code_expiration = None
                    user.save()
                    return JsonResponse({"message": "Account verified successfully!"}, status=200)
                else:
                    return JsonResponse({"error": "Invalid or expired verification code."}, status=400)

            except User.DoesNotExist:
                return JsonResponse({"error": "User not found."}, status=404)

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

class PongGame:
    def __init__(self, mode='single'):
        self.mode = mode  # single, two_player, four_player
        self.ball = {'x': 400, 'y': 250, 'dx': 5, 'dy': 5}
        self.paddles = {
            'player1': 200,  # Sol paddle (Oyuncu 1)
            'player2': 200,  # Sağ paddle (Oyuncu 2 veya Bilgisayar)
            'player3': 200,  # Üst paddle (Oyuncu 3)
            'player4': 200   # Alt paddle (Oyuncu 4)
        }

    def move_ball(self):
        self.ball['x'] += self.ball['dx']
        self.ball['y'] += self.ball['dy']

        # Top kenarlara çarptığında yön değiştir
        if self.ball['y'] <= 0 or self.ball['y'] >= 500:
            self.ball['dy'] *= -1

        # Paddle'lara çarpma kontrolleri
        if (self.ball['x'] <= 20 and 
            self.paddles['player1'] < self.ball['y'] < self.paddles['player1'] + 100):
            self.ball['dx'] *= -1

        if (self.ball['x'] >= 780 and 
            self.paddles['player2'] < self.ball['y'] < self.paddles['player2'] + 100):
            self.ball['dx'] *= -1

        if self.mode in ['four_player']:
            # Üst paddle
            if (self.ball['y'] <= 20 and 
                self.paddles['player3'] < self.ball['x'] < self.paddles['player3'] + 100):
                self.ball['dy'] *= -1

            # Alt paddle
            if (self.ball['y'] >= 480 and 
                self.paddles['player4'] < self.ball['x'] < self.paddles['player4'] + 100):
                self.ball['dy'] *= -1

    def move_computer_paddle(self):
        if self.mode == 'single':
            if self.paddles['player2'] + 50 < self.ball['y']:
                self.paddles['player2'] = min(400, self.paddles['player2'] + 5)
            else:
                self.paddles['player2'] = max(0, self.paddles['player2'] - 5)

    def move_player_paddle(self, player, direction):
        if direction == 'up':
            self.paddles[player] = max(0, self.paddles[player] - 30)
        elif direction == 'down':
            self.paddles[player] = min(400, self.paddles[player] + 30)

    def get_game_state(self):
        return {
            'ball': self.ball,
            'paddles': self.paddles,
            'mode': self.mode
        }

game_instance = PongGame()

class PongAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        game_instance.move_ball()
        if game_instance.mode == 'single':
            game_instance.move_computer_paddle()
        game_state = game_instance.get_game_state()
        return JsonResponse(game_state, status=200)

    def post(self, request):
        action = request.data.get('action')
        player = request.data.get('player', 'player1')

        if action in ['up', 'down']:
            game_instance.move_player_paddle(player, action)
        
        game_instance.move_ball()
        if game_instance.mode == 'single':
            game_instance.move_computer_paddle()
        
        game_state = game_instance.get_game_state()
        return JsonResponse(game_state, status=200)

    def put(self, request):
        mode = request.data.get('mode', 'single')
        game_instance._init_(mode)
        return JsonResponse({"message": "Game mode changed successfully!"}, status=200)