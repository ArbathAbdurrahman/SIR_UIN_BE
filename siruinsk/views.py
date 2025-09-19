from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework import status
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db.models import Q
from .serializers import *

class RegistrationView(APIView):
    """ Registrasi user """
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"message": "User registered successfully!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """ Login user """
    def post(self, request):
        identifier = request.data.get('username') 
        password = request.data.get('password')

        if not identifier or not password:
            return Response({'error': 'Identifier dan password wajib diisi.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(Q(username=identifier) | Q(email=identifier))
        except User.DoesNotExist:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        user_authenticated = authenticate(username=user.username, password=password)

        if user_authenticated is not None:
            refresh = RefreshToken.for_user(user_authenticated)
            user_serializer = UserSerializer(user_authenticated)

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': user_serializer.data
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]  # Hanya user yang terautentikasi yang bisa logout

    def post(self, request):
        refresh_token = request.data.get("refresh")
        print(request.data)

        if not refresh_token:
            return Response({"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()  # Memasukkan token ke blacklist
            return Response({"message": "Logout successful"}, status=status.HTTP_205_RESET_CONTENT)
        except TokenError:  # Menangani token yang tidak valid atau sudah kadaluarsa
            return Response({"error": "Invalid or expired refresh token"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ResetPasswordView(APIView):

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            # user = User.objects.get(email=email)

            # Generate reset token
            reset_token = get_random_string(32)

            # Kirim email reset password
            reset_link = f"https://scit.com/reset-password/{reset_token}"
            send_mail(
                "Reset Password",
                f"Klik link berikut untuk reset password: {reset_link}",
                "noreply@scit.com",
                [email],
                fail_silently=False,
            )
            return Response({'message': 'Silakan cek email untuk reset password'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AuthView(APIView):
    def get(self, request):
        if request.user.is_authenticated:
            user = request.user
            context = {
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
            return Response(context, status=status.HTTP_200_OK)
        return Response({'detail': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)