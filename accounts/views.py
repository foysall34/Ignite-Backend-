from rest_framework import generics, status
from django.contrib.auth.hashers import make_password 
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from .serializers import (
    RegisterSerializer, OTPSerializer, LoginSerializer,
    ResendOTPSerializer, ForgotPasswordSerializer,
    ResetPasswordSerializer, ChangePasswordSerializer
)
from .utils import generate_otp, send_otp_email, send_password_reset_otp_email
from django.utils import timezone
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import Profile
from .serializers import ProfileSerializer

from django.core.cache import cache
from rest_framework import generics, status
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password
from .models import User
from .serializers import RegisterSerializer
from .utils import generate_otp, send_otp_email


class RegisterView(generics.GenericAPIView):
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        # Check for already active user
        if User.objects.filter(email=email, is_active=True).exists():
            return Response(
                {'detail': 'Email is already registered and verified.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate OTP and hash password
        otp = generate_otp()
        hashed_password = make_password(password)

        # Use same cache format as VerifyOTPView
        cache_key = f"registration_otp_{email}"
        user_data = {
            'email': email,
            'password_hash': hashed_password,
            'otp': otp,
        }

        #  Store OTP data in cache for 10 minutes
        cache.set(cache_key, user_data, timeout=600)

        # Send email
        send_otp_email(email, otp)

        return Response(
            {'detail': 'An OTP has been sent to your email. Please use it to verify your account.'},
            status=status.HTTP_200_OK
        )



from django.core.cache import cache
from rest_framework import generics, status
from rest_framework.response import Response
from .serializers import OTPSerializer
from .models import User


class VerifyOTPView(generics.GenericAPIView):
    serializer_class = OTPSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        otp_from_user = serializer.validated_data['otp']
        purpose = serializer.validated_data['purpose']

        # cache key dynamic
        cache_key = f"{purpose}_otp_{email}"
        cached_data = cache.get(cache_key)

        if not cached_data:
            return Response(
                {"detail": "OTP expired or not found."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if cached_data.get("otp") != otp_from_user:
            return Response(
                {"detail": "Invalid OTP."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 1Registration OTP verification
            if purpose == "registration":
                user, created = User.objects.get_or_create(
                    email=cached_data['email'],
                    defaults={
                        'password': cached_data['password_hash'],
                        'is_active': True
                    }
                )
                if not created and not user.is_active:
                    user.password = cached_data['password_hash']
                    user.is_active = True
                    user.save()
                message = "Account verified successfully. You can now log in."

            # Password Reset OTP verification
            elif purpose == "password_reset":
                # Create temporary reset token
                from uuid import uuid4
                reset_token = str(uuid4())
                cache.set(f"reset_token_{email}", reset_token, timeout=300)  # 5 minutes
                message = "OTP verified successfully. Use the reset token to set a new password."
                response_data = {
                    "detail": message,
               
                }
                cache.delete(cache_key)
                return Response(response_data, status=status.HTTP_200_OK)

            # delete otp after verification
            cache.delete(cache_key)
            return Response({'detail': message}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"detail": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        refresh = RefreshToken.for_user(user)
        return Response({
            'role' : user.role ,
            'email' :user.email,
            'success_msg' : "login successfull",
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })

class ResendOTPView(generics.GenericAPIView):
    serializer_class = ResendOTPSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        

        otp = generate_otp()
        user.otp = otp
        user.otp_created_at = timezone.now()
        user.save()

        send_otp_email(user.email, otp)
        
        return Response({'detail': 'A new OTP has been sent to your email.'}, status=status.HTTP_200_OK)

from django.core.cache import cache
from datetime import timedelta

class ForgotPasswordView(generics.GenericAPIView):
    serializer_class = ForgotPasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            return Response({'detail': 'User not found or is not active.'}, status=status.HTTP_404_NOT_FOUND)
            
        otp = generate_otp()
        user.otp = otp
        user.otp_created_at = timezone.now()
        user.save()

        #  Save OTP to cache for VerifyOTPView to find
        cache_key = f"password_reset_otp_{email}"
        cache.set(cache_key, {"email": email, "otp": otp}, timeout=300)  # valid for 5 min

        # Send email
        send_password_reset_otp_email(user.email, otp)
        
        return Response({'detail': 'Password reset OTP sent to your email.'}, status=status.HTTP_200_OK)




class ResetPasswordView(generics.GenericAPIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get("email")

        new_password = request.data.get("new_password")

        
        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
           
            return Response({"detail": "Password reset successfully."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)





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
            
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            return Response({"detail": "Password updated successfully"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    





from drf_spectacular.utils import extend_schema

from .models import Profile
from .serializers import ProfileSerializer


from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .serializers import ProfileSerializer
from .models import Profile


class UserProfileView(generics.GenericAPIView):

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    serializer_class = ProfileSerializer
    queryset = Profile.objects.all()

    def get_object(self):
        """
        Return user's profile or None
        """
        try:
            return self.request.user.profile
        except Profile.DoesNotExist:
            return None

    def get(self, request, *args, **kwargs):
        profile = self.get_object()
        if profile is None:
            return Response({'error': 'Profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(profile)
        profile_data = serializer.data

        # Plan info merging
        plan_data = {
            "plan_type": request.user.plan_type,
            "is_plan_paid": request.user.is_plan_paid,
            "plan_start_date": request.user.plan_start_date,
            "plan_end_date": request.user.plan_end_date,
        }

        final_data = {
            **profile_data,
            **plan_data
        }

        return Response(final_data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        # Check if profile already exists
        if hasattr(request.user, 'profile'):
            return Response(
                {'error': 'Profile already exists for this user.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request, *args, **kwargs):
        profile = self.get_object()
        if profile is None:
            return Response(
                {'error': 'Profile not found. Please create one first.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
