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

class RegisterView(generics.GenericAPIView):
    serializer_class = RegisterSerializer 

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        if User.objects.filter(email=email, is_active=True).exists():
            return Response(
                {'detail': 'Email is already registered and verified.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        otp = generate_otp()
        hashed_password = make_password(password) 

        cache_key = f"unverified_user_{email}"
        user_data = {
            'email': email,
            'password_hash': hashed_password,
            'otp': otp
        }
        cache.set(cache_key, user_data, timeout=600)  
        send_otp_email(email, otp)
        
        return Response(
            {'detail': 'An OTP has been sent to your email. Please use it to verify your account.'},
            status=status.HTTP_200_OK
        )
class VerifyOTPView(generics.GenericAPIView):
    serializer_class = OTPSerializer
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        otp_from_user = serializer.validated_data['otp']

        # Retrieve user data from cache
        cache_key = f"unverified_user_{email}"
        user_data = cache.get(cache_key)

        # Check if data exists in cache
        if not user_data:
            return Response(
                {'detail': 'OTP has expired or you have not registered yet.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if the provided OTP is correct
        if user_data.get('otp') != otp_from_user:
            return Response(
                {'detail': 'Invalid OTP.'},
                status=status.HTTP_400_BAD_REQUEST
            )
       
        try:
          
            user, created = User.objects.get_or_create(
                email=user_data['email'],
                defaults={
                    'password': user_data['password_hash'],
                    'is_active': True
                }
            )
            
            # If the user was already created somehow but not active, activate them now
            if not created and not user.is_active:
                user.password = user_data['password_hash']
                user.is_active = True
                user.save()

            # Clean up by deleting the cache entry
            cache.delete(cache_key)

            return Response(
                {'detail': 'Account verified successfully. You can now log in.'},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'detail': f'An error occurred: {str(e)}'},
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

        send_password_reset_otp_email(user.email, otp)
        
        return Response({'detail': 'Password reset OTP sent to your email.'}, status=status.HTTP_200_OK)

class ResetPasswordView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        new_password = serializer.validated_data['new_password']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        if user.otp == otp:
            # Consider adding OTP expiry check here
            user.set_password(new_password)
            user.otp = None
            user.otp_created_at = None
            user.save()
            return Response({'detail': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)

        return Response({'detail': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)

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


class UserProfileView(generics.GenericAPIView):

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    

    serializer_class = ProfileSerializer
    queryset = Profile.objects.all() 

    def get_object(self):
        """
  
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
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
    
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
            return Response({'error': 'Profile not found. Please create one first.'}, status=status.HTTP_404_NOT_FOUND)
        

        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)