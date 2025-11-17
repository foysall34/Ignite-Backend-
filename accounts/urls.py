from django.urls import path

from .views import (
    AllRegisteredUsersView,
    RegisterView,
    VerifyOTPView,
    LoginView,
    ResendOTPView,
    ForgotPasswordView,
    ResetPasswordView,
    ChangePasswordView,
    UserProfileView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('login/', LoginView.as_view(), name='login'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path("all-users/", AllRegisteredUsersView.as_view(), name="all_users"),


]