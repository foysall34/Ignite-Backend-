# users/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from django.contrib.auth.models import User
from .serializers import (
    RegisterSerializer, VerifyOTPSerializer, ChangePasswordSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer, LoginSerializer
)
from .models import Profile
from .utils import generate_otp, send_otp_via_email
from django.utils import timezone
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers  
from rest_framework_simplejwt.tokens import RefreshToken


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.create(serializer.validated_data)
            return Response(
                {"message": "Registration successful. Please check your email for OTP."},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyOTPView(APIView):
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            
            try:
                user = User.objects.get(email__iexact=email)
                profile = Profile.objects.get(user=user)
                
                if profile.otp == otp and not profile.is_otp_expired():
                    user.is_active = True
                    user.save()
                    profile.otp = None 
                    profile.save()
                    return Response({"message": "Account verified successfully."}, status=status.HTTP_200_OK)
                
                return Response({"error": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)
                
            except (User.DoesNotExist, Profile.DoesNotExist):
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendOTPView(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email__iexact=email)
            if user.is_active:
                return Response({"message": "This account is already verified."}, status=status.HTTP_400_BAD_REQUEST)

            profile = user.profile
            otp = generate_otp()
            profile.otp = otp
            profile.otp_created_at = timezone.now()
            profile.save()
            
            send_otp_via_email(email, otp)
            return Response({"message": "A new OTP has been sent to your email."}, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)


class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
           
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            custom_response = {
                "success": True,
                "message": "Login successful",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "email": user.email,
                "role": user.profile.role
            }
            return Response(custom_response, status=status.HTTP_200_OK)
        return Response({
            "success": False,
            "message": serializer.errors
        }, status=status.HTTP_401_UNAUTHORIZED)

class ForgotPasswordView(APIView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email__iexact=email)
                profile = user.profile
                otp = generate_otp()
                profile.otp = otp
                profile.otp_created_at = timezone.now()
                profile.save()
                send_otp_via_email(email, otp)
                return Response({"message": "Password reset OTP sent to your email."}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            new_password = serializer.validated_data['new_password']
            
            try:
                user = User.objects.get(email__iexact=email)
                profile = user.profile
                if profile.otp == otp and not profile.is_otp_expired():
                    user.set_password(new_password)
                    user.save()
                    profile.otp = None
                    profile.save()
                    return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)
                return Response({"error": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)
            except (User.DoesNotExist, Profile.DoesNotExist):
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    model = User
    permission_classes = (IsAuthenticated,)

    def get_object(self, queryset=None):
        return self.request.user

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            if not self.object.check_password(serializer.data.get("old_password")):
                return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
            if serializer.data.get("new_password") != serializer.data.get("confirm_new_password"):
                return Response({"new_password": ["Passwords do not match."]}, status=status.HTTP_400_BAD_REQUEST)

            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)