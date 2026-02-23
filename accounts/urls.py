from django.urls import path

from .views import (
    AllRegisteredUsersView,
    RegisterView,
    VerifyOTPView,
    LoginView,
    LogoutView,
    TokenRefreshCookieView,
    ResendOTPView,
    ForgotPasswordView,
    ResetPasswordView,
    ChangePasswordView,
    UserProfileView,
    UserProfileView,
    UserCreateAPIView,
    UserUpdateDeleteAPIView,
    UserLimitsOverviewView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshCookieView.as_view(), name='token-refresh'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path("all-users/", AllRegisteredUsersView.as_view(), name="all_users"),
    path("users/", UserCreateAPIView.as_view(), name="user-create"),
    path("users/<int:id>/", UserUpdateDeleteAPIView.as_view(), name="user-ud"),
    path("user-limits/", UserLimitsOverviewView.as_view(), name="user-limits"),


]